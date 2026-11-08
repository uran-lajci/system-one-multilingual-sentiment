"""Run one System One model with one question file over the 10 conference test sets and save each item's prediction.

The question file must sit in experiments/<experiment>/questions/, and the script writes
results/<experiment>/<question>/<model>/<language>.csv. <experiment> is, for example, zero_shot or few_shot, and
<question> is the question file's name, such as baseline. Each file holds the row number, the gold and predicted labels,
the three probabilities and the model version, but no text, so the test text never leaves data/. A language whose file
already exists is skipped, so a stopped run can be started again. With -n, it scores only the first n items of each
test set and writes to results/smoke_<n>/<experiment>/ instead. With -l, it runs only the named languages.

uv run python -m experiments.zero_shot.classify_sentiment -m jev-1.14.0
"""

import argparse
import asyncio
import datetime
import json
import os
from collections.abc import Awaitable, Callable

import httpx
import laya
import pandas as pd
from dotenv import load_dotenv
from typesafe_sdk import AsyncTypeSafeClient, ChoiceAnswer, Questions, RetryPolicy

from data_prep.files import read_csv_any_encoding, sentiment_labels, text_column

QUESTION_ID = 'sentiment'
LABELS = ('positive', 'neutral', 'negative')

CONFERENCE_TEST_FILES = {
    'English': 'data/tsm/test/english.csv',
    'German': 'data/tsm/test/german.csv',
    'French': 'data/tsm/test/french.csv',
    'Albanian': 'data/lmr-sms/test/Albanian_ts2148.csv',
    'Bosnian': 'data/lmr-sms/test/Bosnian_ts782.csv',
    'Croatian': 'data/lmr-sms/test/Croatian_ts2790.csv',
    'Serbian': 'data/lmr-sms/test/Serbian_ts2272.csv',
    'Swedish': 'data/lmr-sms/test/Swedish.csv',
    'Norwegian': 'data/lmr-sms/test/Norwegian.csv',
    'Danish': 'data/lmr-sms/test/Danish.csv',
}

JEV_MODELS = ('jev-1.14.0',)
CLEF_MODELS = ('clef', 'clef-flash')
LAYA_REPOS = {'laya': 'convaiinnovations/laya', 'laya-multilingual': 'convaiinnovations/laya-multilingual'}

Prediction = dict[str, str | float | int | None]
Predictor = Callable[[list[str]], Awaitable[list[Prediction]]]


def is_criterion(criterion: object) -> bool:
    """Plain text, as in zero-shot, or an object with a text `description` and a list of text `examples`."""
    if isinstance(criterion, str):
        return True
    return (
        isinstance(criterion, dict)
        and tuple(criterion) == ('description', 'examples')
        and isinstance(criterion['description'], str)
        and isinstance(criterion['examples'], list)
        and all(isinstance(example, str) for example in criterion['examples'])
    )


def load_questions(path: str) -> Questions:
    """Load a question file, and stop unless it is one Choice question with a valid criterion for each of our labels."""
    with open(path, encoding='utf-8') as file:
        questions: object = json.load(file)

    error = (
        f'{path} must hold one Choice question {QUESTION_ID!r} with criteria for {LABELS}, '
        'each plain text or {"description": text, "examples": [text, ...]}'
    )
    if not isinstance(questions, dict) or len(questions) != 1:
        raise ValueError(error)

    question = questions.get(QUESTION_ID)
    criteria = question.get('criteria') if isinstance(question, dict) else None
    if (
        not isinstance(question, dict)
        or question.get('type') != 'choice'
        or not isinstance(question.get('instructions'), str)
        or not isinstance(criteria, dict)
        or tuple(criteria) != LABELS
        or not all(is_criterion(criterion) for criterion in criteria.values())
    ):
        raise ValueError(error)
    return questions


def to_prediction(answer: ChoiceAnswer, version: str, api_version: str | None, input_tokens: int | None) -> Prediction:
    prediction: Prediction = {'prediction': answer.choice}
    prediction |= {f'p_{label}': answer.probabilities[label] for label in LABELS}
    return prediction | {'model_version': version, 'api_version': api_version, 'input_tokens': input_tokens}


async def gather_limited(
    texts: list[str], concurrency: int, predict_one: Callable[[str], Awaitable[Prediction]]
) -> list[Prediction]:
    semaphore = asyncio.Semaphore(concurrency)

    async def limited(text: str) -> Prediction:
        async with semaphore:
            return await predict_one(text)

    return await asyncio.gather(*(limited(text) for text in texts))


def jev_predictor(model: str, questions: Questions, concurrency: int) -> Predictor:
    client = AsyncTypeSafeClient()
    retry = RetryPolicy(max_retries=5, backoff_max=30.0, timeout=60.0)

    async def predict_one(text: str) -> Prediction:
        response = await client.system_one(text, questions, model=model, retry=retry)
        tokens = response.usage.input_tokens if response.usage else None
        return to_prediction(response.choices[QUESTION_ID], response.model, None, tokens)

    return lambda texts: gather_limited(texts, concurrency, predict_one)


def clef_predictor(model: str, questions: Questions, concurrency: int) -> Predictor:
    account = os.environ['CLOUDFLARE_ACCOUNT_KEY']
    url = f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}'
    headers = {'Authorization': f'Bearer {os.environ["CLOUDFLARE_API_TOKEN"]}'}
    client = httpx.AsyncClient(headers=headers, timeout=60, transport=httpx.AsyncHTTPTransport(retries=3))

    async def predict_one(text: str) -> Prediction:
        # Rate limits and server errors are retried with growing waits; anything else stops the run
        for attempt in range(6):
            response = await client.post(url, json={'model': model, 'state': text, 'questions': questions})
            if response.status_code != 429 and response.status_code < 500:
                break
            await asyncio.sleep(2**attempt)
        response.raise_for_status()

        result: object = response.json()['result']
        if not isinstance(result, dict):
            raise ValueError(f'Unexpected Cloudflare response: {response.text[:300]}')
        answer = ChoiceAnswer.model_validate(result['answers'][QUESTION_ID])
        return to_prediction(
            answer, str(result['model']), response.headers.get('api-version'), result['usage']['input_tokens']
        )

    return lambda texts: gather_limited(texts, concurrency, predict_one)


def laya_predictor(model: str, questions: Questions) -> Predictor:
    repo = LAYA_REPOS[model]
    revision = laya.PINNED_REVISIONS[repo]
    agent = laya.load(repo, revision=revision, device='cuda')
    version = f'{repo}@{revision} (laya {laya.__version__})'

    async def predict(texts: list[str]) -> list[Prediction]:
        results = await asyncio.to_thread(agent.predict_batch, texts, questions, batch_size=64)
        return [
            to_prediction(ChoiceAnswer.model_validate(r['answers'][QUESTION_ID]), version, None, None) for r in results
        ]

    return predict


def make_predictor(model: str, questions: Questions, concurrency: int) -> Predictor:
    if model in JEV_MODELS:
        return jev_predictor(model, questions, concurrency)
    if model in CLEF_MODELS:
        return clef_predictor(model, questions, concurrency)
    if model in LAYA_REPOS:
        return laya_predictor(model, questions)
    raise ValueError(f'Unknown model {model!r}; use one of {JEV_MODELS + CLEF_MODELS + tuple(LAYA_REPOS)}')


async def main(model: str, concurrency: int, out: str, limit: int, questions_path: str, languages: list[str]) -> None:
    load_dotenv('.env')
    questions_dir = os.path.dirname(os.path.abspath(questions_path))
    if os.path.basename(questions_dir) != 'questions':
        raise ValueError(f'{questions_path} must sit in experiments/<experiment>/questions/')
    experiment = os.path.basename(os.path.dirname(questions_dir))
    question_name = os.path.splitext(os.path.basename(questions_path))[0]
    run_dir = experiment if limit == 0 else os.path.join(f'smoke_{limit}', experiment)
    out_dir = os.path.join(out, run_dir, question_name, model)

    predict = make_predictor(model, load_questions(questions_path), concurrency)
    os.makedirs(out_dir, exist_ok=True)
    written, skipped = 0, []

    for language in languages:
        path = CONFERENCE_TEST_FILES[language]
        out_path = os.path.join(out_dir, f'{language}.csv')
        if os.path.exists(out_path):
            skipped.append(language)
            continue

        rows = read_csv_any_encoding(path)
        rows = rows.head(limit) if limit else rows
        texts = text_column(rows).astype(str).tolist()

        predictions = await predict(texts)

        table = pd.DataFrame(predictions)
        table.insert(0, 'row', range(len(rows)))
        table.insert(1, 'gold', sentiment_labels(rows, path).to_numpy())
        table['date'] = datetime.date.today().isoformat()
        table.to_csv(out_path, index=False)
        written += len(table)
        print(f'{language}: wrote {len(table)} predictions to {out_path}')

    skip_note = f'; skipped {", ".join(skipped)}, which already had a file' if skipped else ''
    print(f'{model}: wrote {written} predictions to {out_dir}{skip_note}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-m', '--model', required=True)
    parser.add_argument('-c', '--concurrency', type=int, default=16)
    parser.add_argument('-o', '--out', default='results')
    parser.add_argument('-n', '--limit', type=int, default=0)
    parser.add_argument('-q', '--questions-path', default='experiments/zero_shot/questions/baseline.json')
    parser.add_argument(
        '-l', '--languages', nargs='+', choices=list(CONFERENCE_TEST_FILES), default=list(CONFERENCE_TEST_FILES)
    )

    args = parser.parse_args()
    asyncio.run(main(args.model, args.concurrency, args.out, args.limit, args.questions_path, args.languages))
