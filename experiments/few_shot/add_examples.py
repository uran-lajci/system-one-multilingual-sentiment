"""Write a few-shot version of each zero-shot question file, with the same name, by adding examples to its criteria.

Each plain-text criterion becomes {"description": <the criterion, word for word>, "examples": <the examples for that
label>}. The default examples are the three that Kastrati et al. (2026) gave the LLMs, one per label.

uv run python -m experiments.few_shot.add_examples
"""

import argparse
import glob
import json
import os

from experiments.zero_shot.classify_sentiment import LABELS, QUESTION_ID, load_questions


def main(questions_dir: str, examples_path: str, out_dir: str) -> None:
    with open(examples_path, encoding='utf-8') as file:
        examples: object = json.load(file)
    if (
        not isinstance(examples, dict)
        or tuple(examples) != LABELS
        or not all(isinstance(texts, list) for texts in examples.values())
        or not all(isinstance(text, str) for texts in examples.values() for text in texts)
    ):
        raise ValueError(f'{examples_path} must hold a list of text examples for each of {LABELS}, in that order')

    paths = sorted(glob.glob(os.path.join(questions_dir, '*.json')))
    os.makedirs(out_dir, exist_ok=True)

    for path in paths:
        load_questions(path)
        with open(path, encoding='utf-8') as file:
            questions: object = json.load(file)
        question = questions.get(QUESTION_ID) if isinstance(questions, dict) else None
        criteria = question.get('criteria') if isinstance(question, dict) else None
        if not isinstance(question, dict) or not isinstance(criteria, dict):
            raise ValueError(f'{path} has no criteria for {QUESTION_ID!r}')
        if not all(isinstance(text, str) for text in criteria.values()):
            raise ValueError(f'{path} must have plain-text criteria, as a zero-shot question does')

        question['criteria'] = {
            label: {'description': criteria[label], 'examples': examples[label]} for label in LABELS
        }

        out_path = os.path.join(out_dir, os.path.basename(path))
        with open(out_path, 'w', encoding='utf-8') as file:
            json.dump(questions, file, ensure_ascii=False, indent=2)
            file.write('\n')
        load_questions(out_path)
        print(f'Wrote {out_path}')

    print(f'Wrote {len(paths)} few-shot question files to {out_dir}, with examples from {examples_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-q', '--questions-dir', default='experiments/zero_shot/questions')
    parser.add_argument('-e', '--examples-path', default='experiments/few_shot/paper_examples.json')
    parser.add_argument('-o', '--out-dir', default='experiments/few_shot/questions')

    args = parser.parse_args()
    main(args.questions_dir, args.examples_path, args.out_dir)
