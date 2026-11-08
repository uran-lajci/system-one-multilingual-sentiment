"""Run Jev with one structured question file over one conference test set, with the dataset's context in the state.

Each request sends {"context": <the language's context from contexts.json>, "text": <the item>} as state, and the same
question in the three label orders of OPTION_ORDERS. Jev leans toward the label listed first, so the prediction is the
label with the highest probability averaged over the three orders. prediction_first is the prediction of the first
order alone, from the same response. The script writes results/<experiment>/<question>/<model>/<language>.csv
with the row number, the gold label, both predictions, the averaged probabilities and the probabilities of each order,
but no text. A file that already exists is skipped. With -n, it scores only the first n items and writes to
results/smoke_<n>/<experiment>/ instead. The question file must sit in experiments/<experiment>/questions/.

uv run python -m experiments.structured_tuning.classify_sentiment \\
    -q experiments/structured_tuning/questions/english_01.json
"""

import argparse
import asyncio
import datetime
import json
import os

import pandas as pd
from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient, Questions, RetryPolicy

from data_prep.files import read_csv_any_encoding, sentiment_labels, text_column
from experiments.structured_tuning.induce_questions import load_structured_questions
from experiments.zero_shot.classify_sentiment import (
    CONFERENCE_TEST_FILES,
    LABELS,
    Prediction,
    Predictor,
    gather_limited,
)


def structured_predictor(model: str, questions: Questions, context: str, concurrency: int) -> Predictor:
    """Ask Jev every question in questions about each text, with the context in the state.

    The questions are one question in different label orders. The prediction is the label with the highest probability
    averaged over them, and prediction_first is the top label of the first question alone.
    """
    client = AsyncTypeSafeClient()
    retry = RetryPolicy(max_retries=5, backoff_max=30.0, timeout=60.0)
    question_ids = list(questions)

    async def predict_one(text: str) -> Prediction:
        response = await client.system_one({'context': context, 'text': text}, questions, model=model, retry=retry)
        per_order = {question_id: response.choices[question_id].probabilities for question_id in question_ids}
        averaged = {label: sum(p[label] for p in per_order.values()) / len(per_order) for label in LABELS}
        first = per_order[question_ids[0]]

        prediction: Prediction = {
            'prediction': max(LABELS, key=lambda label: averaged[label]),
            'prediction_first': max(LABELS, key=lambda label: first[label]),
        }
        prediction |= {f'p_{label}': averaged[label] for label in LABELS}
        for question_id, probabilities in per_order.items():
            prediction |= {f'p_{label}_{question_id}': probabilities[label] for label in LABELS}
        tokens = response.usage.input_tokens if response.usage else None
        return prediction | {'model_version': response.model, 'input_tokens': tokens}

    return lambda texts: gather_limited(texts, concurrency, predict_one)


async def main(model: str, questions_path: str, language: str, concurrency: int, out: str, limit: int) -> None:
    load_dotenv('.env')
    questions: Questions = load_structured_questions(questions_path)
    with open(os.path.join(os.path.dirname(__file__), 'contexts.json'), encoding='utf-8') as file:
        context = json.load(file)[language]['context']

    questions_dir = os.path.dirname(os.path.abspath(questions_path))
    if os.path.basename(questions_dir) != 'questions':
        raise ValueError(f'{questions_path} must sit in experiments/<experiment>/questions/')
    experiment = os.path.basename(os.path.dirname(questions_dir))
    question_name = os.path.splitext(os.path.basename(questions_path))[0]
    run_dir = experiment if limit == 0 else os.path.join(f'smoke_{limit}', experiment)
    out_dir = os.path.join(out, run_dir, question_name, model)
    out_path = os.path.join(out_dir, f'{language}.csv')
    if os.path.exists(out_path):
        print(f'{model}: skipped {language}, {out_path} already exists')
        return

    path = CONFERENCE_TEST_FILES[language]
    rows = read_csv_any_encoding(path)
    rows = rows.head(limit) if limit else rows
    texts = text_column(rows).astype(str).tolist()

    predict = structured_predictor(model, questions, context, concurrency)
    table = pd.DataFrame(await predict(texts))
    table.insert(0, 'row', range(len(rows)))
    table.insert(1, 'gold', sentiment_labels(rows, path).to_numpy())
    table['date'] = datetime.date.today().isoformat()

    os.makedirs(out_dir, exist_ok=True)
    table.to_csv(out_path, index=False)
    print(f'{model}: wrote {len(table)} predictions to {out_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-m', '--model', default='jev-1.14.0')
    parser.add_argument('-q', '--questions-path', required=True)
    parser.add_argument('-l', '--language', default='English', choices=list(CONFERENCE_TEST_FILES))
    parser.add_argument('-c', '--concurrency', type=int, default=16)
    parser.add_argument('-o', '--out', default='results')
    parser.add_argument('-n', '--limit', type=int, default=0)

    args = parser.parse_args()
    asyncio.run(main(args.model, args.questions_path, args.language, args.concurrency, args.out, args.limit))
