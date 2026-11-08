"""Tune one structured question for Jev with Opus, using errors on train data and selecting on validation data.

Version 0 is the start question, which Opus wrote from the 150 train texts that draw_texts gives for --seed. The
development set holds --dev-size other train texts, drawn at random with the same seed, so the labels keep their train
proportions. Jev scores each version with the first label order only, on the development and the validation set. Opus
reads only the development results and writes the next version, until it has written --iterations new versions. The
script keeps the version with the highest validation macro-F1, the earlier one on a tie, and copies it to
<out-dir>/questions/<name>.json for scoring on test with classify_sentiment. <out-dir>/runs/<name>/
holds every version, the conversation and a log, and <results-dir>/<name>/ holds the predictions. A run whose kept
question already exists is skipped; a stopped run starts again from version 0.

uv run python -m experiments.structured_tuning.tune_question -s 1 -x albanian_01 \\
    -q experiments/structured_tuning/start/questions/albanian_01.json
"""

import argparse
import asyncio
import datetime
import json
import os
import shutil

import anthropic
import pandas as pd
from dotenv import load_dotenv
from sklearn.metrics import f1_score
from typesafe_sdk import Questions

from data_prep.files import read_csv_any_encoding, sentiment_labels, text_column
from experiments.structured_tuning.classify_sentiment import structured_predictor
from experiments.structured_tuning.induce_questions import (
    CRITERION_SCHEMA,
    EFFORT,
    QUESTION_IDS,
    draw_texts,
    examples_not_copied,
    load_structured_questions,
    write_question_file,
)
from experiments.zero_shot.classify_sentiment import LABELS

MAX_ATTEMPTS = 3

TUNING_SCHEMA: dict[str, object] = {
    'type': 'object',
    'properties': {
        'analysis': {'type': 'string'},
        'question': {'type': 'string'},
        'rule': {'type': 'string'},
        'criteria': {
            'type': 'object',
            'properties': {label: CRITERION_SCHEMA for label in LABELS},
            'required': list(LABELS),
            'additionalProperties': False,
        },
    },
    'required': ['analysis', 'question', 'rule', 'criteria'],
    'additionalProperties': False,
}


def render_feedback(template: str, version: int, table: pd.DataFrame, texts: list[str], macro_f1: float) -> str:
    """Fill the feedback template with the macro-F1, the confusion matrix and one line per misclassified text."""
    confusion = pd.crosstab(table['gold'], table['prediction']).reindex(index=LABELS, columns=LABELS, fill_value=0)
    errors = table[table['gold'] != table['prediction']]
    error_lines = [
        f'<text label="{error["gold"]}" predicted="{error["prediction"]}" p_positive="{error["p_positive"]:.2f}" '
        f'p_neutral="{error["p_neutral"]:.2f}" p_negative="{error["p_negative"]:.2f}">{texts[error["row"]]}</text>'
        for error in errors.to_dict('records')
    ]
    return (
        template.replace('{version}', str(version))
        .replace('{next_version}', str(version + 1))
        .replace('{items}', str(len(table)))
        .replace('{macro_f1}', f'{macro_f1:.1f}')
        .replace('{confusion}', confusion.to_string())
        .replace('{errors}', str(len(errors)))
        .replace('{error_lines}', '\n'.join(error_lines))
    )


def as_answer_json(path: str) -> str:
    """Show a structured question file as Opus writes it: question, rule and criteria in the order of LABELS."""
    with open(path, encoding='utf-8') as file:
        question = json.load(file)[QUESTION_IDS[0]]
    answer = {
        'question': question['instructions']['question'],
        'rule': question['instructions']['rule'],
        'criteria': {label: question['criteria'][label] for label in LABELS},
    }
    return json.dumps(answer, ensure_ascii=False, indent=2)


async def ask_for_version(
    client: anthropic.AsyncAnthropic,
    model: str,
    messages: list[anthropic.types.MessageParam],
    path: str,
) -> tuple[Questions, dict[str, object], list[dict[str, object]]]:
    """Get the next version from Opus and write it to path, giving Opus the error when it fails the format check.

    Appends every reply and retry message to messages, and returns the question, Opus's answer and the usage per call.
    """
    usage: list[dict[str, object]] = []
    for _ in range(MAX_ATTEMPTS):
        response = await client.messages.create(
            model=model,
            max_tokens=16000,
            output_config={'effort': EFFORT, 'format': {'type': 'json_schema', 'schema': TUNING_SCHEMA}},
            cache_control={'type': 'ephemeral'},
            messages=messages,
        )
        # No refusal fallback: another model's answer would break the pinned model ID
        if response.stop_reason == 'refusal':
            raise RuntimeError(f'Opus refused, request {response._request_id}')
        messages.append({'role': 'assistant', 'content': response.content})
        usage.append(
            {
                'request_id': response._request_id,
                'response_model': response.model,
                'stop_reason': response.stop_reason,
                'input_tokens': response.usage.input_tokens,
                'cache_creation_input_tokens': response.usage.cache_creation_input_tokens,
                'cache_read_input_tokens': response.usage.cache_read_input_tokens,
                'output_tokens': response.usage.output_tokens,
            }
        )

        raw = ''.join(block.text for block in response.content if isinstance(block, anthropic.types.TextBlock))
        try:
            answer = json.loads(raw)
            write_question_file(answer, path)
            return load_structured_questions(path), answer, usage
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError, ValueError) as error:
            messages.append(
                {'role': 'user', 'content': f'That version fails the format check: {error}. Write it again.'}
            )

    raise RuntimeError(f'No version passed the format check in {MAX_ATTEMPTS} attempts')


async def main(
    start_path: str,
    seed: int,
    name: str,
    language: str,
    train_path: str,
    validation_path: str,
    dev_size: int,
    model: str,
    tuned_model: str,
    iterations: int,
    concurrency: int,
    out_dir: str,
    results_dir: str,
) -> None:
    kept_path = os.path.join(out_dir, 'questions', f'{name}.json')
    if os.path.exists(kept_path):
        print(f'{name}: skipped, {kept_path} already exists')
        return

    load_dotenv('.env')
    client = anthropic.AsyncAnthropic(max_retries=5)
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'tuning_prompt.md'), encoding='utf-8') as file:
        first_template = file.read()
    with open(os.path.join(here, 'feedback.md'), encoding='utf-8') as file:
        feedback_template = file.read()
    with open(os.path.join(here, 'contexts.json'), encoding='utf-8') as file:
        context = json.load(file)[language]['context']

    train = read_csv_any_encoding(train_path)
    train_texts = text_column(train).astype(str)
    induction_rows = draw_texts(train_path, seed).index
    dev_rows = train.drop(index=induction_rows).sample(dev_size, random_state=seed).index
    dev_texts = train_texts[dev_rows].tolist()
    dev_gold = sentiment_labels(train, train_path)[dev_rows].to_numpy()
    seen_texts = train_texts[induction_rows].tolist() + dev_texts

    validation = read_csv_any_encoding(validation_path)
    validation_texts = text_column(validation).astype(str).tolist()
    validation_gold = sentiment_labels(validation, validation_path).to_numpy()

    run_dir = os.path.join(out_dir, 'runs', name)
    predictions_dir = os.path.join(results_dir, name)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(predictions_dir, exist_ok=True)
    os.makedirs(os.path.dirname(kept_path), exist_ok=True)

    questions = load_structured_questions(start_path)
    version_path = os.path.join(run_dir, 'version_00.json')
    shutil.copyfile(start_path, version_path)
    messages: list[anthropic.types.MessageParam] = []
    versions: list[dict[str, object]] = []

    for version in range(iterations + 1):
        predict = structured_predictor(tuned_model, {QUESTION_IDS[0]: questions[QUESTION_IDS[0]]}, context, concurrency)
        scores = {}
        tables = {}
        for split, texts, gold in [('dev', dev_texts, dev_gold), ('validation', validation_texts, validation_gold)]:
            table = pd.DataFrame(await predict(texts))
            table.insert(0, 'row', range(len(texts)))
            table.insert(1, 'gold', gold)
            table.to_csv(os.path.join(predictions_dir, f'version_{version:02d}_{split}.csv'), index=False)
            tables[split] = table
            scores[split] = 100 * f1_score(table['gold'], table['prediction'], labels=list(LABELS), average='macro')
        versions.append(
            {
                'version': version,
                'path': version_path,
                'dev_macro_f1': round(float(scores['dev']), 2),
                'validation_macro_f1': round(float(scores['validation']), 2),
            }
        )
        print(f'{name} version {version}/{iterations}: dev {scores["dev"]:.1f}, validation {scores["validation"]:.1f}')

        if version == iterations:
            break
        feedback = render_feedback(feedback_template, version, tables['dev'], dev_texts, scores['dev'])
        if version == 0:
            feedback = (
                first_template.replace('{context}', context)
                .replace('{question}', as_answer_json(start_path))
                .replace('{feedback}', feedback)
            )
        messages.append({'role': 'user', 'content': feedback})

        version_path = os.path.join(run_dir, f'version_{version + 1:02d}.json')
        questions, answer, usage = await ask_for_version(client, model, messages, version_path)
        versions[-1] |= {
            'analysis_for_next': answer['analysis'],
            'next_examples_not_copied': examples_not_copied(answer, seen_texts),
            'opus_calls': usage,
        }

    validation_scores = [float(str(entry['validation_macro_f1'])) for entry in versions]
    kept = validation_scores.index(max(validation_scores))
    shutil.copyfile(str(versions[kept]['path']), kept_path)

    log = {
        'name': name,
        'seed': seed,
        'start_path': start_path,
        'language': language,
        'context': context,
        'train_path': train_path,
        'dev_rows': [int(row) for row in dev_rows],
        'validation_path': validation_path,
        'model': model,
        'effort': EFFORT,
        'tuned_model': tuned_model,
        'tuning_question_ids': [QUESTION_IDS[0]],
        'date': datetime.date.today().isoformat(),
        'kept_version': kept,
        'versions': versions,
    }
    with open(os.path.join(run_dir, 'log.json'), 'w', encoding='utf-8') as file:
        json.dump(log, file, ensure_ascii=False, indent=2)
        file.write('\n')
    with open(os.path.join(run_dir, 'conversation.json'), 'w', encoding='utf-8') as file:
        json.dump(messages, file, ensure_ascii=False, indent=2, default=lambda block: block.to_dict())
        file.write('\n')

    print(f'{name}: kept version {kept} (validation macro-F1 {validation_scores[kept]:.1f}); wrote {kept_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--start-path', required=True)
    parser.add_argument('-s', '--seed', type=int, required=True)
    parser.add_argument('-x', '--name', required=True)
    parser.add_argument('-l', '--language', default='Albanian')
    parser.add_argument('-t', '--train-path', default='data/lmr-sms/train/Albanian.csv')
    parser.add_argument('-v', '--validation-path', default='data/lmr-sms/validation/Albanian.csv')
    parser.add_argument('-d', '--dev-size', type=int, default=600)
    parser.add_argument('-m', '--model', default='claude-opus-5-5')
    parser.add_argument('-j', '--tuned-model', default='jev-1.14.0')
    parser.add_argument('-i', '--iterations', type=int, default=10)
    parser.add_argument('-c', '--concurrency', type=int, default=16)
    parser.add_argument('-o', '--out-dir', default='experiments/structured_tuning')
    parser.add_argument('-r', '--results-dir', default='results/structured_tuning/tuning')

    args = parser.parse_args()
    asyncio.run(
        main(
            args.start_path,
            args.seed,
            args.name,
            args.language,
            args.train_path,
            args.validation_path,
            args.dev_size,
            args.model,
            args.tuned_model,
            args.iterations,
            args.concurrency,
            args.out_dir,
            args.results_dir,
        )
    )
