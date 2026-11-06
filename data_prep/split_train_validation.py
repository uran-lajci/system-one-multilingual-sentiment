"""Split each LMR-SMS train_validation file into train and validation sets, stratified by label.

The script drops rows whose text is also in the language's test set, and keeps one copy of each duplicate text, so
no text appears in two sets.

uv run python -m data_prep.split_train_validation
"""

import argparse
import glob
import os

import pandas as pd
from sklearn.model_selection import train_test_split

from data_prep.files import read_csv_any_encoding, text_column


def main(data_dir: str, raw_dir: str, validation_size: float, seed: int) -> None:
    paths = sorted(glob.glob(os.path.join(raw_dir, 'train_validation', '*_train_val.csv')))

    for path in paths:
        language = os.path.basename(path).removesuffix('_train_val.csv')
        [test_path] = glob.glob(os.path.join(data_dir, 'test', f'{language}*.csv'))

        rows = pd.read_csv(path)
        test_texts = set(text_column(read_csv_any_encoding(test_path)).str.strip().str.lower())

        texts = rows['text'].str.strip().str.lower()
        in_test = texts.isin(test_texts)
        repeated = texts.duplicated() & ~in_test
        kept = rows[~in_test & ~repeated]

        train, validation = train_test_split(kept, test_size=validation_size, stratify=kept['label'], random_state=seed)

        for split, split_rows in (('train', train), ('validation', validation)):
            os.makedirs(os.path.join(data_dir, split), exist_ok=True)
            split_rows.to_csv(os.path.join(data_dir, split, f'{language}.csv'), index=False)

        print(
            f'{language}: wrote {len(train)} rows to train/{language}.csv and {len(validation)} to '
            f'validation/{language}.csv; dropped {in_test.sum()} train/validation rows whose text is also in the '
            f'test set and {repeated.sum()} duplicate texts'
        )

    print(f'Split {len(paths)} files into {data_dir}/train and {data_dir}/validation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--data-dir', default='data/lmr-sms')
    parser.add_argument('-r', '--raw-dir', default='data/raw/lmr-sms')
    parser.add_argument('-v', '--validation-size', type=float, default=0.2)
    parser.add_argument('-s', '--seed', type=int, default=42)

    args = parser.parse_args()
    main(args.data_dir, args.raw_dir, args.validation_size, args.seed)
