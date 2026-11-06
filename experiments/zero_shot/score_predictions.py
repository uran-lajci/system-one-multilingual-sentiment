"""Score each model's zero-shot predictions with macro-F1 and compare them with the paper's five LLMs.

The script reads every <model>/<language>.csv in the results folder, computes macro-F1 (%) on the three labels per
language, adds the mean over the 10 languages and the paper's zero-shot LLM scores, and writes scores.csv to the
results folder.

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


def main(results_dir: str, paper_scores: str) -> None:
    order = [*JEV_MODELS, *CLEF_MODELS, *LAYA_REPOS]
    models = [model for model in order if os.path.isdir(os.path.join(results_dir, model))]
    scores = pd.DataFrame(index=pd.Index(list(CONFERENCE_TEST_FILES), name='language'), columns=models, dtype=float)
    items = pd.Series(0, index=scores.index, name='items')

    for model in models:
        for language in CONFERENCE_TEST_FILES:
            path = os.path.join(results_dir, model, f'{language}.csv')
            if not os.path.exists(path):
                continue
            predictions = pd.read_csv(path)
            scores.loc[language, model] = 100 * f1_score(
                predictions['gold'], predictions['prediction'], labels=list(LABELS), average='macro', zero_division=0
            )
            items[language] = max(items[language], len(predictions))

    table = pd.concat([items, scores, pd.read_csv(paper_scores).set_index('language')], axis=1)
    table.loc['Mean'] = table.drop(columns='items').mean(skipna=False)
    table['items'] = items.reindex(table.index).fillna(items.sum()).astype(int)

    table.round(1).to_csv(os.path.join(results_dir, 'scores.csv'))
    print(table.round(1).to_string())
    missing = scores.isna().sum().sum()
    missing_note = f'; {missing} model-language pairs have no predictions yet' if missing else ''
    print(f'Scored {len(models)} models on {len(CONFERENCE_TEST_FILES)} languages{missing_note}; wrote scores.csv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-r', '--results-dir', default='results/zero_shot')
    parser.add_argument('-p', '--paper-scores', default='experiments/zero_shot/paper_scores.csv')

    args = parser.parse_args()
    main(args.results_dir, args.paper_scores)
