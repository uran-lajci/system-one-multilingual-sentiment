"""Helpers for reading the dataset files, whose names, encodings, column names and label formats differ."""

import os
import re

import pandas as pd

LABEL_PREFIXES = {'pos': 'positive', 'neu': 'neutral', 'neg': 'negative'}

# The same integer code means a different label in different datasets
LABEL_CODES = {
    'tsm': {'0': 'negative', '1': 'neutral', '2': 'positive'},
    'afrisenti': {'0': 'positive', '1': 'neutral', '2': 'negative'},
    'Macedonian': {'-1': 'negative', '0': 'neutral', '1': 'positive'},
}


def find_test_file(test_dir: str, language: str) -> str:
    # Matches 'amh' to 'Amh.csv' and 'hau' to 'hau_ts2652.csv', but 'por' not to 'pcm_ts2078.csv'
    names = [name for name in os.listdir(test_dir) if re.match(rf'{re.escape(language)}[._]', name, re.IGNORECASE)]
    if len(names) != 1:
        raise ValueError(f'Expected one test file for {language!r} in {test_dir}, found {names}')
    return os.path.join(test_dir, names[0])


def read_csv_any_encoding(path: str) -> pd.DataFrame:
    # Some LMR-SMS test files are cp1252, not UTF-8
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='cp1252')


def text_column(rows: pd.DataFrame) -> 'pd.Series[str]':
    """Return the column that holds the text, which the datasets call text, Text, tweet, Tweet or tweet_text."""
    for name in ('text', 'Text', 'tweet', 'Tweet', 'tweet_text'):
        if name in rows.columns:
            return rows[name]
    raise ValueError(f'No text column in: {list(rows.columns)}')


def sentiment_labels(rows: pd.DataFrame, path: str) -> 'pd.Series[str]':
    """Return the labels of rows read from path as positive, neutral or negative. The path decides what codes mean."""
    column = next((name for name in ('label', 'HandLabel', 'Polarity1', 'sentiment') if name in rows.columns), None)
    if column is None:
        raise ValueError(f'No label column in {path}: {list(rows.columns)}')
    values = rows[column].astype(str).str.strip()

    codes = next((codes for name, codes in LABEL_CODES.items() if name in path), {})
    labels = values.map(codes).fillna(values.str[:3].str.lower().map(LABEL_PREFIXES))

    if labels.isna().any():
        raise ValueError(f'Unknown labels in {path}: {sorted(set(values[labels.isna()]))}')
    return labels
