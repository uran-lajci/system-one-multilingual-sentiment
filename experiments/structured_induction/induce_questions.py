"""Ask Opus to write a structured per-dataset question from labelled train texts, and save it in three label orders.

Call n draws 50 texts per label from the train file with seed n, as instruction induction does, and sends them with the
dataset's context from contexts.json. Opus answers with a question, a rule and, for each label, what, examples, cues and
not_for. The script writes the same question in each label order of OPTION_ORDERS to
<out-dir>/questions/<prefix>_<n>.json and a log to <out-dir>/calls/<prefix>_<n>.json. The log holds the seed, the
0-based row numbers of the drawn texts, the raw answer and every example that Opus did not copy word for word from them.
A call whose question file already exists is skipped. If an answer fails the format check, the call is repeated with
the same seed.

uv run python -m experiments.structured_induction.induce_questions
"""

import argparse
import datetime
import json
import os
import re
from typing import Final

import anthropic
from dotenv import load_dotenv
from typesafe_sdk import Questions

from data_prep.files import read_csv_any_encoding, text_column
from experiments.instruction_induction.induce_questions import draw_texts
from experiments.zero_shot.classify_sentiment import LABELS

OPTION_ORDERS = (
    ('neutral', 'positive', 'negative'),
    ('positive', 'negative', 'neutral'),
    ('negative', 'neutral', 'positive'),
)
QUESTION_IDS = tuple(f'sentiment_{order[0]}_first' for order in OPTION_ORDERS)
CRITERION_FIELDS = ('what', 'examples', 'cues', 'not_for')
EFFORT: Final = 'medium'
MAX_WORDS = 400
MAX_EXAMPLES = 4
MAX_ATTEMPTS = 3

CRITERION_SCHEMA: dict[str, object] = {
    'type': 'object',
    'properties': {
        'what': {'type': 'string'},
        'examples': {'type': 'array', 'items': {'type': 'string'}},
        'cues': {'type': 'string'},
        'not_for': {'type': 'string'},
    },
    'required': list(CRITERION_FIELDS),
    'additionalProperties': False,
}

ANSWER_SCHEMA: dict[str, object] = {
    'type': 'object',
    'properties': {
        'question': {'type': 'string'},
        'rule': {'type': 'string'},
        'criteria': {
            'type': 'object',
            'properties': {label: CRITERION_SCHEMA for label in LABELS},
            'required': list(LABELS),
            'additionalProperties': False,
        },
    },
    'required': ['question', 'rule', 'criteria'],
    'additionalProperties': False,
}


def load_structured_questions(path: str) -> Questions:
    """Load a question file, and stop unless it holds the same structured Choice question in each of OPTION_ORDERS."""
    with open(path, encoding='utf-8') as file:
        questions: object = json.load(file)

    error = (
        f'{path} must hold the same structured Choice question as {QUESTION_IDS}, in the label orders {OPTION_ORDERS}'
    )
    if not isinstance(questions, dict) or tuple(questions) != QUESTION_IDS:
        raise ValueError(error)

    first = questions[QUESTION_IDS[0]]
    for question_id, order in zip(QUESTION_IDS, OPTION_ORDERS):
        question = questions[question_id]
        criteria = question.get('criteria') if isinstance(question, dict) else None
        if (
            not isinstance(question, dict)
            or tuple(question) != ('type', 'instructions', 'criteria')
            or question['type'] != 'choice'
            or question['instructions'] != first['instructions']
            or not isinstance(criteria, dict)
            or tuple(criteria) != order
            or any(criteria[label] != first['criteria'][label] for label in order)
        ):
            raise ValueError(error)

    instructions = first['instructions']
    if not (
        isinstance(instructions, dict)
        and tuple(instructions) == ('question', 'rule')
        and all(isinstance(text, str) and text.strip() for text in instructions.values())
    ):
        raise ValueError(f'{path}: instructions must hold a non-empty question and rule')
    for label, criterion in first['criteria'].items():
        if not (
            isinstance(criterion, dict)
            and tuple(criterion) == CRITERION_FIELDS
            and all(isinstance(criterion[field], str) for field in ('what', 'cues', 'not_for'))
            and isinstance(criterion['examples'], list)
            and 1 <= len(criterion['examples']) <= MAX_EXAMPLES
            and all(isinstance(example, str) for example in criterion['examples'])
        ):
            raise ValueError(
                f'{path}: the {label} criterion must hold {CRITERION_FIELDS}, with 1 to {MAX_EXAMPLES} examples'
            )
    return questions


def count_words(answer: dict[str, object]) -> int:
    """Count the question's words, leaving out bracketed text in examples and cues, which holds the English meaning."""
    criteria = answer['criteria']
    texts = [str(answer['question']), str(answer['rule'])]
    if isinstance(criteria, dict):
        for criterion in criteria.values():
            glossed = [*criterion['examples'], criterion['cues']]
            texts += [criterion['what'], criterion['not_for'], *(re.sub(r'\([^()]*\)', '', text) for text in glossed)]
    return len(' '.join(texts).split())


def examples_not_copied(answer: dict[str, object], drawn_texts: list[str]) -> list[str]:
    """Return the examples that are not part of any drawn text, also after removing a final bracketed translation."""
    criteria = answer['criteria']
    examples = (
        [example for criterion in criteria.values() for example in criterion['examples']]
        if isinstance(criteria, dict)
        else []
    )
    # Strips a final translation, so 'Faleminderit (Thank you)' becomes 'Faleminderit'
    untranslated = [re.sub(r'\s*\([^()]*\)\s*$', '', example) for example in examples]
    return [
        example
        for example, bare in zip(examples, untranslated)
        if not any(example.strip() in text or bare.strip() in text for text in drawn_texts)
    ]


def write_question_file(answer: dict[str, object], path: str) -> int:
    """Write Opus's answer as the same question in each label order, check the file, and return its word count.

    Raises ValueError if the question is too long or the file fails the format check.
    """
    words = count_words(answer)
    if words > MAX_WORDS:
        raise ValueError(f'{words} words, more than {MAX_WORDS}')
    criteria = answer['criteria']
    if not isinstance(criteria, dict):
        raise ValueError('criteria must be an object')

    instructions = {'question': answer['question'], 'rule': answer['rule']}
    questions = {
        question_id: {
            'type': 'choice',
            'instructions': instructions,
            'criteria': {label: criteria[label] for label in order},
        }
        for question_id, order in zip(QUESTION_IDS, OPTION_ORDERS)
    }
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(questions, file, ensure_ascii=False, indent=2)
        file.write('\n')
    load_structured_questions(path)
    return words


def main(model: str, language: str, train_path: str, out_dir: str, calls: int, name_prefix: str) -> None:
    load_dotenv('.env')
    client = anthropic.Anthropic(max_retries=5)
    with open(os.path.join(os.path.dirname(__file__), 'prompt.md'), encoding='utf-8') as file:
        template = file.read()
    with open(os.path.join(os.path.dirname(__file__), 'contexts.json'), encoding='utf-8') as file:
        context = json.load(file)[language]['context']
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
        drawn_texts = texts[drawn.index].tolist()
        lines = [f'<text label="{label}">{text}</text>' for text, label in zip(drawn_texts, drawn)]
        prompt = template.replace('{context}', context).replace('{texts}', '\n'.join(lines))

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
            raw = ''.join(block.text for block in response.content if isinstance(block, anthropic.types.TextBlock))

            try:
                answer = json.loads(raw)
                words = write_question_file(answer, question_path)
                break
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                if os.path.exists(question_path):
                    os.remove(question_path)
                failed_answers.append({'answer': raw, 'error': str(error)})
        else:
            failed_path = os.path.join(out_dir, 'calls', f'{name}_failed.json')
            with open(failed_path, 'w', encoding='utf-8') as file:
                json.dump({'seed': seed, 'failed_answers': failed_answers}, file, ensure_ascii=False, indent=2)
                file.write('\n')
            errors = '; '.join(failed['error'] for failed in failed_answers)
            raise RuntimeError(f'{name}: no answer passed the format check in {MAX_ATTEMPTS} attempts ({errors})')

        log = {
            'call': seed,
            'seed': seed,
            'model': model,
            'response_model': response.model,
            'effort': EFFORT,
            'date': datetime.date.today().isoformat(),
            'language': language,
            'context': context,
            'train_path': train_path,
            'rows': [int(row) for row in drawn.index],
            'attempts': attempt,
            'failed_answers': failed_answers,
            'answer': raw,
            'words': words,
            'examples_not_copied': examples_not_copied(answer, drawn_texts),
            'stop_reason': response.stop_reason,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'request_id': response._request_id,
        }
        with open(os.path.join(out_dir, 'calls', f'{name}.json'), 'w', encoding='utf-8') as file:
            json.dump(log, file, ensure_ascii=False, indent=2)
            file.write('\n')
        written += 1
        print(f'{seed}/{calls}: wrote {question_path} after {attempt} attempt(s), {words} words')

    skip_note = f'; skipped {", ".join(skipped)}, which already had a file' if skipped else ''
    print(f'Wrote {written} question files to {os.path.join(out_dir, "questions")}{skip_note}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-m', '--model', default='claude-opus-5-5')
    parser.add_argument('-l', '--language', default='English')
    parser.add_argument('-t', '--train-path', default='data/tsm/train/english.csv')
    parser.add_argument('-o', '--out-dir', default='experiments/structured_induction')
    parser.add_argument('-n', '--calls', type=int, default=10)
    parser.add_argument('-x', '--name-prefix', default='english')

    args = parser.parse_args()
    main(args.model, args.language, args.train_path, args.out_dir, args.calls, args.name_prefix)
