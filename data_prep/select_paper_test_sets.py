"""Make data/lmr-sms/test/ hold exactly the LMR-SMS test sets that Kastrati et al. (2026) scored, without Malaysian.

The authors' Bosnian, Croatian and Serbian files hold the whole dataset, but the paper scored 20% samples, which the
authors later sent as .xlsx files in data/raw/lmr-sms/paper_samples/. The script picks the sample rows from the whole
file by row number, writes them to test/<Language>_ts<size>.csv and moves the whole file to data/raw/lmr-sms/full/.
It takes the rows from the CSV, not from the .xlsx file, because Excel changed the tweet IDs and some text. It also
moves the Malaysian file, which this study leaves out, to data/raw/lmr-sms/excluded/. Running it again changes nothing.

uv run python -m data_prep.select_paper_test_sets
"""

import argparse
import glob
import os

import pandas as pd

SAMPLED_LANGUAGES = ('Bosnian', 'Croatian', 'Serbian')
EXCLUDED_FILES = ('Malaysia_ts627.csv',)


def main(data_dir: str, raw_dir: str) -> None:
    test_dir = os.path.join(data_dir, 'test')

    for language in SAMPLED_LANGUAGES:
        full_path = os.path.join(raw_dir, 'full', f'{language}.csv')
        if not os.path.exists(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            os.replace(os.path.join(test_dir, f'{language}.csv'), full_path)

        rows = pd.read_csv(full_path, dtype=str, keep_default_na=False)
        [sample_path] = glob.glob(os.path.join(raw_dir, 'paper_samples', f'*-{language}-TestSet*.xlsx'))
        ids = set(pd.read_excel(sample_path, dtype=str, keep_default_na=False)['id'])

        # The first column is the row number, which has no name in the CSV
        sample = rows[rows.iloc[:, 0].isin(ids)].rename(columns={rows.columns[0]: ''})
        if len(sample) != len(ids):
            raise ValueError(f'{sample_path} has {len(ids)} row numbers, but only {len(sample)} are in {full_path}')

        sample.to_csv(os.path.join(test_dir, f'{language}_ts{len(sample)}.csv'), index=False)
        print(f'{language}: wrote {len(sample)} of {len(rows)} rows to test/{language}_ts{len(sample)}.csv')

    for name in EXCLUDED_FILES:
        if os.path.exists(os.path.join(test_dir, name)):
            os.makedirs(os.path.join(raw_dir, 'excluded'), exist_ok=True)
            os.replace(os.path.join(test_dir, name), os.path.join(raw_dir, 'excluded', name))
            print(f'Moved test/{name} to {raw_dir}/excluded/')

    print(f'{test_dir} now holds {len(glob.glob(os.path.join(test_dir, "*.csv")))} test files')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--data-dir', default='data/lmr-sms')
    parser.add_argument('-r', '--raw-dir', default='data/raw/lmr-sms')

    args = parser.parse_args()
    main(args.data_dir, args.raw_dir)
