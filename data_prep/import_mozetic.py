"""Turn the Mozetič et al. (2016) tweet files into LMR-SMS train_validation files.

For each language, the script renames the columns to text and label, drops every row whose text loosely matches an
item of our test file, and writes data/raw/lmr-sms/train_validation/<Language>_train_val.csv. Test files are only read.

uv run python -m data_prep.import_mozetic
"""

import argparse
import html
import os
import re

import pandas as pd

from data_prep.files import find_test_file, text_column

LANGUAGES = ('Bosnian', 'Croatian', 'Serbian', 'Swedish')


def letters_only(text: str) -> str:
    """Reduce a tweet to its letters, so it matches our test files, which were lowercased and lost URLs and mentions."""
    text = html.unescape(text).lower()
    text = re.sub(r'https?://\S+', '', text)
    # Removes '@koji' from '@koji_lik', as the test files' preprocessing did
    text = re.sub(r'@[a-z0-9]+', '', text)
    text = re.sub(r'\brt\b', '', text)
    return re.sub(r'[\W\d_]+', '', text)


def main(raw_dir: str, data_dir: str) -> None:
    for language in LANGUAGES:
        rows = pd.read_csv(
            os.path.join(raw_dir, 'mozetic', f'{language}_tweet_label.csv'), dtype=str, keep_default_na=False
        )
        rows = rows.rename(columns={'Tweet text': 'text', 'SentLabel': 'label'})

        test = pd.read_csv(find_test_file(os.path.join(data_dir, 'test'), language), dtype=str, keep_default_na=False)
        test_keys = set(text_column(test).map(letters_only))

        in_test = rows['text'].map(letters_only).isin(test_keys)
        rows[~in_test].to_csv(os.path.join(raw_dir, 'train_validation', f'{language}_train_val.csv'), index=False)

        print(
            f'{language}: wrote {(~in_test).sum()} rows to train_validation/{language}_train_val.csv; '
            f'dropped {in_test.sum()} rows that match our test set'
        )

    print(f'Imported {len(LANGUAGES)} languages from {raw_dir}/mozetic')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-r', '--raw-dir', default='data/raw/lmr-sms')
    parser.add_argument('-d', '--data-dir', default='data/lmr-sms')

    args = parser.parse_args()
    main(args.raw_dir, args.data_dir)
