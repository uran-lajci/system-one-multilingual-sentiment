"""Drop train and validation rows whose text is also in the test set of the same language.

For every file in data/<collection>/train/ and data/<collection>/validation/, the script drops each row whose text
(stripped, lowercased) also appears in that language's test file, and saves the file in place. Test files are only
read.

uv run python -m data_prep.remove_test_leaks
"""

import argparse
import glob
import os

import pandas as pd

from data_prep.files import find_test_file, read_csv_any_encoding, text_column


def main(data_dir: str) -> None:
    paths = sorted(
        path
        for split in ('train', 'validation')
        for pattern in ('*.csv', '*.tsv')
        for path in glob.glob(os.path.join(data_dir, '*', split, pattern))
    )
    dropped_total = 0

    for path in paths:
        language = os.path.splitext(os.path.basename(path))[0]
        test_dir = os.path.join(os.path.dirname(os.path.dirname(path)), 'test')
        test_texts = set(text_column(read_csv_any_encoding(find_test_file(test_dir, language))).str.strip().str.lower())

        sep = '\t' if path.endswith('.tsv') else ','
        rows = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)
        in_test = text_column(rows).str.strip().str.lower().isin(test_texts)
        dropped = int(in_test.sum())

        if dropped:
            rows[~in_test].to_csv(path, sep=sep, index=False)
        dropped_total += dropped
        print(f'{os.path.relpath(path, data_dir)}: dropped {dropped} of {len(rows)} rows also in the test set')

    print(f'Dropped {dropped_total} train/validation rows from {len(paths)} files; test files are unchanged')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--data-dir', default='data')

    args = parser.parse_args()
    main(args.data_dir)
