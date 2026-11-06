"""Classify the sentiment of one text with a System One model.

uv run python -m experiments.zero_shot.classify_sentiment -m jev-1.14.0 -t 'I love this phone'
"""

import argparse
import json
import os

import httpx
from dotenv import load_dotenv
from laya import Router
from typesafe_sdk import ChoiceAnswer, Questions, TypeSafeClient

QUESTION_ID = 'sentiment'


def load_questions(path: str) -> Questions:
    with open(path, encoding='utf-8') as file:
        questions: object = json.load(file)

    if not isinstance(questions, dict) or QUESTION_ID not in questions:
        raise ValueError(f'No {QUESTION_ID!r} question in {path}')
    return questions


def predict_jev(text: str, model: str, questions: Questions) -> tuple[ChoiceAnswer, str]:
    with TypeSafeClient() as client:
        response = client.system_one(text, questions, model=model)
    return response.choices[QUESTION_ID], response.model


def predict_clef(text: str, model: str, questions: Questions) -> tuple[ChoiceAnswer, str]:
    account = os.environ['CLOUDFLARE_ACCOUNT_KEY']
    url = f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}'
    headers = {'Authorization': f'Bearer {os.environ["CLOUDFLARE_API_TOKEN"]}'}
    body = {'model': model, 'state': text, 'questions': questions}

    response = httpx.post(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()

    result = response.json()['result']
    return ChoiceAnswer.model_validate(result['answers'][QUESTION_ID]), result['model']


def predict_laya(text: str, model: str, questions: Questions) -> tuple[ChoiceAnswer, str]:
    result = Router().predict(text, questions, model=model)
    return ChoiceAnswer.model_validate(result['answers'][QUESTION_ID]), result['routing']['model']


def main(text: str, model: str, questions: str) -> None:
    load_dotenv()
    question_set = load_questions(questions)

    if model.startswith('jev'):
        answer, version = predict_jev(text, model, question_set)
    elif model.startswith('clef'):
        answer, version = predict_clef(text, model, question_set)
    else:
        answer, version = predict_laya(text, model, question_set)

    print(version, answer.choice, answer.confidence, answer.probabilities)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-t', '--text', required=True)
    parser.add_argument('-m', '--model', required=True)
    parser.add_argument('-q', '--questions', default='experiments/zero_shot/questions/baseline.json')

    args = parser.parse_args()
    main(args.text, args.model, args.questions)
