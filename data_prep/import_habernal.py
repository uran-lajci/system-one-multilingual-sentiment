"""Turn the Facebook CZ Corpus of Habernal et al. (2013) into the LMR-SMS train_validation file for Czech.

The script pairs gold-posts.txt with gold-labels.txt line by line, drops the bipolar posts and every post whose
0-based line number is an id in our Czech test file, and writes data/raw/lmr-sms/train_validation/Czech_train_val.csv.
The test file is only read.

uv run python -m data_prep.import_habernal
"""

import argparse
import os

import pandas as pd

from data_prep.files import find_test_file, read_csv_any_encoding

LABELS = {'p': 'Positive', 'n': 'Negative', '0': 'Neutral'}


def main(raw_dir: str, data_dir: str) -> None:
    corpus_dir = os.path.join(raw_dir, 'habernal', 'facebook')
    with open(os.path.join(corpus_dir, 'gold-posts.txt'), encoding='utf-8', newline='') as file:
        posts = file.read().split('\r\n')
    with open(os.path.join(corpus_dir, 'gold-labels.txt'), encoding='utf-8', newline='') as file:
        labels = file.read().split('\r\n')
    if len(posts) != len(labels):
        raise ValueError(f'{len(posts)} posts but {len(labels)} labels')

    rows = pd.DataFrame({'text': posts, 'label': labels})
    rows = rows[rows['text'] != '']
    test_ids = set(read_csv_any_encoding(find_test_file(os.path.join(data_dir, 'test'), 'Czech'))['id'].astype(int))

    in_test = rows.index.isin(test_ids)
    bipolar = rows['label'] == 'b'
    kept = rows[~in_test & ~bipolar]
    unknown = set(kept['label']) - set(LABELS)
    if unknown:
        raise ValueError(f'Unknown labels: {sorted(unknown)}')
    kept = kept.assign(label=kept['label'].map(LABELS))

    kept.to_csv(os.path.join(raw_dir, 'train_validation', 'Czech_train_val.csv'), index=False)
    print(
        f'Czech: wrote {len(kept)} rows to train_validation/Czech_train_val.csv; dropped {in_test.sum()} test posts '
        f'and {(bipolar & ~in_test).sum()} bipolar posts'
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-r', '--raw-dir', default='data/raw/lmr-sms')
    parser.add_argument('-d', '--data-dir', default='data/lmr-sms')

    args = parser.parse_args()
    main(args.raw_dir, args.data_dir)
