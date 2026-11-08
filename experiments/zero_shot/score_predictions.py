"""Score each model's zero-shot predictions with macro-F1, per question version and across versions.

For every question folder in the results folder, such as baseline or v03, the script reads each
<model>/<language>.csv, computes macro-F1 (%) on the three labels per language, adds the mean over the conference
languages and the paper's LLM scores, and writes the table to <question>/scores.csv. With 2 or more question versions,
it then writes sensitivity.csv with each model's mean for every version, and the mean, minimum and maximum across
versions.

uv run python -m experiments.zero_shot.score_predictions
"""

import argparse
import os

import pandas as pd
from sklearn.metrics import f1_score

from experiments.zero_shot.classify_sentiment import (
    CLEF_MODELS,
    CONFERENCE_TEST_FILES,
    JEV_MODELS,
    LABELS,
    LAYA_REPOS,
)

MODEL_ORDER = [*JEV_MODELS, *CLEF_MODELS, *LAYA_REPOS]


def score_question(question_dir: str, paper: pd.DataFrame) -> pd.DataFrame:
    models = [model for model in MODEL_ORDER if os.path.isdir(os.path.join(question_dir, model))]
    scores = pd.DataFrame(index=pd.Index(list(CONFERENCE_TEST_FILES), name='language'), columns=models, dtype=float)
    items = pd.Series(0, index=scores.index, name='items')

    for model in models:
        for language in CONFERENCE_TEST_FILES:
            path = os.path.join(question_dir, model, f'{language}.csv')
            if not os.path.exists(path):
                continue
            predictions = pd.read_csv(path)
            scores.loc[language, model] = 100 * f1_score(
                predictions['gold'], predictions['prediction'], labels=list(LABELS), average='macro', zero_division=0
            )
            items[language] = max(items[language], len(predictions))

    table = pd.concat([items, scores, paper], axis=1)
    table.loc['Mean'] = table.drop(columns='items').mean(skipna=False)
    table['items'] = items.reindex(table.index).fillna(items.sum()).astype(int)
    table.round(1).to_csv(os.path.join(question_dir, 'scores.csv'))
    return table


def main(results_dir: str, paper_scores: str) -> None:
    paper = pd.read_csv(paper_scores).set_index('language')
    folders = [name for name in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, name))]
    questions = sorted(folders, key=lambda name: (name != 'baseline', name))

    means = {}
    for question in questions:
        table = score_question(os.path.join(results_dir, question), paper)
        means[question] = table.loc['Mean', [model for model in MODEL_ORDER if model in table.columns]]
        print(f'{question}: wrote {question}/scores.csv')

    if len(questions) < 2:
        print(f'Scored {len(questions)} question version; wrote no sensitivity.csv, which needs 2 or more')
        return

    per_version = pd.DataFrame(means).T
    per_version = per_version[[model for model in MODEL_ORDER if model in per_version.columns]]
    summary = pd.DataFrame(
        {
            'mean': per_version.mean(skipna=False),
            'min': per_version.min(skipna=False),
            'max': per_version.max(skipna=False),
        }
    ).T
    sensitivity = pd.concat([per_version, summary])

    sensitivity.round(1).to_csv(os.path.join(results_dir, 'sensitivity.csv'))
    print(sensitivity.round(1).to_string())
    print(f'Scored {len(questions)} question versions; wrote sensitivity.csv to {results_dir}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-r', '--results-dir', default='results/zero_shot')
    parser.add_argument('-p', '--paper-scores', default='experiments/zero_shot/paper_scores.csv')

    args = parser.parse_args()
    main(args.results_dir, args.paper_scores)
