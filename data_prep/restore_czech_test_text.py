"""Restore the Czech letters in the Czech test file from the Facebook CZ Corpus of Habernal et al. (2013).

The test file we received is cp1252 with every letter outside that code page replaced by '?'. Its ids are 0-based line
numbers of gold-posts.txt, so the script replaces each text with the corpus line of the same id, after checking that
the ASCII letters and digits of both agree, and rewrites the file as UTF-8 with the ids, labels and order unchanged.
The damaged copy is kept as data/raw/lmr-sms/habernal/Czech_ts1950_as_sent.csv.

uv run python -m data_prep.restore_czech_test_text
"""

import argparse
import os
import re
import shutil

from data_prep.files import find_test_file, read_csv_any_encoding


def ascii_skeleton(text: str) -> str:
    """Lowercase ASCII letters and digits only, which the damaged and the clean text share."""
    return re.sub(r'[^a-z0-9]', '', text.lower())


def main(raw_dir: str, data_dir: str) -> None:
    corpus_dir = os.path.join(raw_dir, 'habernal')
    with open(os.path.join(corpus_dir, 'facebook', 'gold-posts.txt'), encoding='utf-8', newline='') as file:
        posts = file.read().split('\r\n')

    test_path = find_test_file(os.path.join(data_dir, 'test'), 'Czech')
    backup = os.path.join(corpus_dir, 'Czech_ts1950_as_sent.csv')
    if not os.path.exists(backup):
        shutil.copyfile(test_path, backup)
    rows = read_csv_any_encoding(backup)

    restored = [posts[int(row_id)] for row_id in rows['id']]
    mismatches = [
        int(row_id)
        for row_id, damaged, clean in zip(rows['id'], rows['text'], restored, strict=True)
        if ascii_skeleton(str(damaged)) != ascii_skeleton(clean)
    ]
    if mismatches:
        raise ValueError(f'{len(mismatches)} test rows do not match their corpus line, first ids: {mismatches[:5]}')

    rows.assign(text=restored).to_csv(test_path, index=False)
    changed = sum(damaged != clean for damaged, clean in zip(rows['text'], restored, strict=True))
    print(f'Czech: restored {changed} of {len(rows)} texts in {test_path}; the damaged copy is {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-r', '--raw-dir', default='data/raw/lmr-sms')
    parser.add_argument('-d', '--data-dir', default='data/lmr-sms')

    args = parser.parse_args()
    main(args.raw_dir, args.data_dir)
