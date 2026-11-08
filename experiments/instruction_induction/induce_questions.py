"""Ask Opus to write one Choice question per call from labelled train texts, and save each question with a call log.

Call n draws 50 texts per label from the train file with seed n, shuffles them with the same seed, and sends them in
the prompt. The script writes <out-dir>/questions/<prefix>_<n>.json and <out-dir>/calls/<prefix>_<n>.json. The log holds
the seed, the 0-based row numbers of the drawn texts, the model, the date, the token counts and Opus's raw answer, but
no text. A call whose question file already exists is skipped. If an answer fails the format check of load_questions,
the call is repeated with the same seed.

uv run python -m experiments.instruction_induction.induce_questions
"""

import argparse
import datetime
import json
import os
from typing import Final

import anthropic
import pandas as pd
from dotenv import load_dotenv

from data_prep.files import read_csv_any_encoding, sentiment_labels, text_column
from experiments.zero_shot.classify_sentiment import LABELS, QUESTION_ID, load_questions

TEXTS_PER_LABEL = 50
EFFORT: Final = 'medium'
MAX_ATTEMPTS = 3

ANSWER_SCHEMA: dict[str, object] = {
    'type': 'object',
    'properties': {
        'instructions': {'type': 'string'},
        'criteria': {
            'type': 'object',
            'properties': {label: {'type': 'string'} for label in LABELS},
            'required': list(LABELS),
            'additionalProperties': False,
        },
    },
    'required': ['instructions', 'criteria'],
    'additionalProperties': False,
}


def draw_texts(train_path: str, seed: int) -> 'pd.Series[str]':
    """Draw TEXTS_PER_LABEL texts per label with this seed, shuffled with the same seed, as labels indexed by row."""
    rows = read_csv_any_encoding(train_path)
    labels = sentiment_labels(rows, train_path)
    drawn = pd.concat([labels[labels == label].sample(TEXTS_PER_LABEL, random_state=seed) for label in LABELS])
    return drawn.sample(frac=1, random_state=seed)


def main(model: str, train_path: str, prompt_path: str, out_dir: str, calls: int, name_prefix: str) -> None:
    load_dotenv('.env')
    client = anthropic.Anthropic(max_retries=5)
    with open(prompt_path, encoding='utf-8') as file:
        template = file.read()
    texts = text_column(read_csv_any_encoding(train_path)).astype(str)

    os.makedirs(os.path.join(out_dir, 'questions'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'calls'), exist_ok=True)
    written, skipped = 0, []

    for seed in range(1, calls + 1):
        name = f'{name_prefix}_{seed:02d}'
        question_path = os.path.join(out_dir, 'questions', f'{name}.json')
        if os.path.exists(question_path):
            skipped.append(name)
            continue

        drawn = draw_texts(train_path, seed)
        lines = [f'<text label="{label}">{text}</text>' for text, label in zip(texts[drawn.index], drawn)]
        prompt = template.replace('{texts}', '\n'.join(lines))

        failed_answers = []
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = client.messages.create(
                model=model,
                max_tokens=16000,
                output_config={'effort': EFFORT, 'format': {'type': 'json_schema', 'schema': ANSWER_SCHEMA}},
                messages=[{'role': 'user', 'content': prompt}],
            )
            # No refusal fallback: another model's answer would break the pinned model ID
            if response.stop_reason == 'refusal':
                raise RuntimeError(f'{name}: Opus refused, request {response._request_id}')
            answer = ''.join(block.text for block in response.content if isinstance(block, anthropic.types.TextBlock))

            try:
                question = json.loads(answer)
                with open(question_path, 'w', encoding='utf-8') as file:
                    json.dump({QUESTION_ID: {'type': 'choice', **question}}, file, ensure_ascii=False, indent=2)
                    file.write('\n')
                load_questions(question_path)
                break
            except (json.JSONDecodeError, TypeError, ValueError):
                if os.path.exists(question_path):
                    os.remove(question_path)
                failed_answers.append(answer)
        else:
            raise RuntimeError(f'{name}: no answer passed the format check in {MAX_ATTEMPTS} attempts')

        log = {
            'call': seed,
            'seed': seed,
            'model': model,
            'response_model': response.model,
            'effort': EFFORT,
            'date': datetime.date.today().isoformat(),
            'train_path': train_path,
            'rows': [int(row) for row in drawn.index],
            'attempts': attempt,
            'failed_answers': failed_answers,
            'answer': answer,
            'stop_reason': response.stop_reason,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'request_id': response._request_id,
        }
        with open(os.path.join(out_dir, 'calls', f'{name}.json'), 'w', encoding='utf-8') as file:
            json.dump(log, file, ensure_ascii=False, indent=2)
            file.write('\n')
        written += 1
        tokens = response.usage.output_tokens
        print(f'{seed}/{calls}: wrote {question_path} after {attempt} attempt(s), {tokens} output tokens')

    skip_note = f'; skipped {", ".join(skipped)}, which already had a file' if skipped else ''
    print(f'Wrote {written} question files to {os.path.join(out_dir, "questions")}{skip_note}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-m', '--model', default='claude-opus-5-5')
    parser.add_argument('-t', '--train-path', default='data/tsm/train/english.csv')
    parser.add_argument('-p', '--prompt-path', default='experiments/instruction_induction/prompt.md')
    parser.add_argument('-o', '--out-dir', default='experiments/instruction_induction')
    parser.add_argument('-n', '--calls', type=int, default=10)
    parser.add_argument('-x', '--name-prefix', default='induced')

    args = parser.parse_args()
    main(args.model, args.train_path, args.prompt_path, args.out_dir, args.calls, args.name_prefix)
