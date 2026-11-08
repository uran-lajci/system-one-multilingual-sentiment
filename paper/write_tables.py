"""Write the paper's tables as LaTeX files from the result files, so that no score in the paper is typed by hand.

Table I lists the datasets with their test, train and validation sizes. Table II gives the zero-shot and few-shot
macro-F1 of the three System One models and the five LLMs of Kastrati et al. (2026). Table III compares Jev with a
tuned question against zero-shot Jev, few-shot Jev and the best LLM score on each language.

uv run python -m paper.write_tables
"""

import argparse
import os

import pandas as pd
from sklearn.metrics import f1_score

from data_prep.files import read_csv_any_encoding
from experiments.zero_shot.classify_sentiment import CONFERENCE_TEST_FILES, LABELS

LANGUAGE_CODES = {
    'English': 'EN',
    'German': 'DE',
    'French': 'FR',
    'Albanian': 'SQ',
    'Bosnian': 'BS',
    'Croatian': 'HR',
    'Serbian': 'SR',
    'Swedish': 'SV',
}

DATASETS = {
    'English': ('SemEval-2017~\\cite{rosenthal2017semeval,barbieri2022xlmt}', 'tweets', 'data/tsm/{split}/english.csv'),
    'German': ('SB-10K~\\cite{cieliebak2017sb10k,barbieri2022xlmt}', 'tweets', 'data/tsm/{split}/german.csv'),
    'French': ('DEFT 2017~\\cite{benamara2017deft,barbieri2022xlmt}', 'tweets', 'data/tsm/{split}/french.csv'),
    'Albanian': ('AlbAna~\\cite{kastrati2021albana}', 'comments', 'data/lmr-sms/{split}/Albanian.csv'),
    'Bosnian': ('Mozeti\\v{c} et al.~\\cite{mozetic2016multilingual}', 'tweets', 'data/lmr-sms/{split}/Bosnian.csv'),
    'Croatian': ('Mozeti\\v{c} et al.~\\cite{mozetic2016multilingual}', 'tweets', 'data/lmr-sms/{split}/Croatian.csv'),
    'Serbian': ('Mozeti\\v{c} et al.~\\cite{mozetic2016multilingual}', 'tweets', 'data/lmr-sms/{split}/Serbian.csv'),
    'Swedish': ('Mozeti\\v{c} et al.~\\cite{mozetic2016multilingual}', 'tweets', 'data/lmr-sms/{split}/Swedish.csv'),
}

SYSTEM_ONE = {'jev-1.14.0': 'Jev', 'clef': 'Clef', 'clef-flash': 'Clef-flash'}
LLMS = {'gpt-4o': 'GPT-4o', 'gemini': 'Gemini', 'deepseek': 'DeepSeek', 'mistral': 'Mistral', 'claude': 'Claude'}


def read_scores(path: str) -> dict[str, dict[str, float]]:
    """Read a scores.csv as {model: {language: macro-F1}}, with the mean as language 'Mean'."""
    frame = pd.read_csv(path).set_index('language').drop(columns='items')
    return {
        str(model): {str(language): float(score) for language, score in column.items()}
        for model, column in frame.to_dict().items()
    }


def tuned_scores() -> dict[str, float]:
    """Macro-F1 (%) on each test set of Jev with the question that the tuning run kept."""
    scores = {}
    for language in CONFERENCE_TEST_FILES:
        predictions = pd.read_csv(f'results/structured_tuning/{language.lower()}_01/jev-1.14.0/{language}.csv')
        scores[language] = 100 * float(
            f1_score(predictions['gold'], predictions['prediction'], labels=list(LABELS), average='macro')
        )
    return scores


def datasets_table() -> str:
    rows = []
    for language, (source, kind, pattern) in DATASETS.items():
        sizes = [len(read_csv_any_encoding(pattern.format(split=split))) for split in ('train', 'validation')]
        test = len(read_csv_any_encoding(CONFERENCE_TEST_FILES[language]))
        rows.append(f'{language} & {source} & {kind} & {test:,} & {sizes[0]:,} & {sizes[1]:,} \\\\')
    return '\n'.join(
        [
            '\\begin{table}[t]',
            '\\centering',
            '\\caption{The eight datasets. The Albanian texts are Facebook comments. Test is the sample that Kastrati '
            'et al.~\\cite{kastrati2026language} scored; train and validation exclude every test item.}',
            '\\label{tab:datasets}',
            '\\setlength{\\tabcolsep}{3pt}',
            '\\begin{tabular}{llrrrr}',
            '\\toprule',
            'Language & Source & Text & Test & Train & Valid. \\\\',
            '\\midrule',
            *rows,
            '\\bottomrule',
            '\\end{tabular}',
            '\\end{table}',
        ]
    )


def scores_block(scores: dict[str, dict[str, float]], setting: str) -> list[str]:
    """One block of Table II: a row per model, with the best score of each column in bold."""
    columns = [*CONFERENCE_TEST_FILES, 'Mean']
    names = {**SYSTEM_ONE, **LLMS}
    best = {column: max(scores[model][column] for model in names) for column in columns}
    lines = [f'\\multicolumn{{10}}{{l}}{{\\textit{{{setting}}}}} \\\\']
    for model, name in names.items():
        cells = [
            f'\\textbf{{{scores[model][column]:.1f}}}'
            if scores[model][column] == best[column]
            else f'{scores[model][column]:.1f}'
            for column in columns
        ]
        lines.append(f'{name} & {" & ".join(cells)} \\\\')
        if model == list(SYSTEM_ONE)[-1]:
            lines.append('\\cmidrule(lr){1-10}')
    return lines


def zero_few_shot_table() -> str:
    zero_shot = read_scores('results/zero_shot/baseline/scores.csv')
    few_shot = read_scores('results/few_shot/baseline/scores.csv')
    header = ' & '.join(LANGUAGE_CODES[language] for language in CONFERENCE_TEST_FILES)
    return '\n'.join(
        [
            '\\begin{table*}[t]',
            '\\centering',
            '\\caption{Macro-F1 (\\%) of the three System One models and of the five LLMs reported by Kastrati et '
            'al.~\\cite{kastrati2026language}, zero-shot and few-shot with the same three English examples. Bold marks '
            'the best score in each column of a block. The mean is unweighted over the eight languages.}',
            '\\label{tab:zero-few-shot}',
            '\\begin{tabular}{lrrrrrrrrr}',
            '\\toprule',
            f'Model & {header} & Mean \\\\',
            '\\midrule',
            *scores_block(zero_shot, 'Zero-shot'),
            '\\midrule',
            *scores_block(few_shot, 'Few-shot'),
            '\\bottomrule',
            '\\end{tabular}',
            '\\end{table*}',
        ]
    )


def tuned_table() -> str:
    zero_shot = read_scores('results/zero_shot/baseline/scores.csv')
    few_shot = read_scores('results/few_shot/baseline/scores.csv')
    tuned = tuned_scores()

    rows = []
    best_scores = []
    for language in CONFERENCE_TEST_FILES:
        candidates = [(zero_shot[model][language], name, 'ZS') for model, name in LLMS.items()]
        candidates += [(few_shot[model][language], name, 'FS') for model, name in LLMS.items()]
        best, name, setting = max(candidates)
        best_scores.append(best)
        jev = round(tuned[language], 1)
        tuned_cell = f'\\textbf{{{jev:.1f}}}' if jev > best else f'{jev:.1f}'
        rows.append(
            f'{language} & {zero_shot["jev-1.14.0"][language]:.1f} & {few_shot["jev-1.14.0"][language]:.1f} '
            f'& {tuned_cell} & {best:.1f} & {name} {setting} & ${jev - best:+.1f}$ \\\\'
        )
    best_mean = sum(best_scores) / len(best_scores)
    tuned_mean = round(sum(tuned.values()) / len(tuned), 1)
    rows.append('\\midrule')
    rows.append(
        f'Mean & {zero_shot["jev-1.14.0"]["Mean"]:.1f} & {few_shot["jev-1.14.0"]["Mean"]:.1f} '
        f'& {tuned_mean:.1f} & {best_mean:.1f} & & ${tuned_mean - best_mean:+.1f}$ \\\\'
    )
    return '\n'.join(
        [
            '\\begin{table}[t]',
            '\\centering',
            '\\caption{Macro-F1 (\\%) of Jev zero-shot (ZS), few-shot (FS) and with the tuned question, against the '
            'highest score any of the five LLMs reached on that language, zero-shot or few-shot. Bold marks a tuned '
            'score above the best LLM score.}',
            '\\label{tab:tuned}',
            '\\setlength{\\tabcolsep}{3pt}',
            '\\begin{tabular}{lrrrrlr}',
            '\\toprule',
            ' & \\multicolumn{3}{c}{Jev} & \\multicolumn{2}{c}{Best LLM} & \\\\',
            '\\cmidrule(lr){2-4}\\cmidrule(lr){5-6}',
            'Language & ZS & FS & Tuned & Score & Model & $\\Delta$ \\\\',
            '\\midrule',
            *rows,
            '\\bottomrule',
            '\\end{tabular}',
            '\\end{table}',
        ]
    )


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    tables = {'datasets.tex': datasets_table(), 'zero_few_shot.tex': zero_few_shot_table(), 'tuned.tex': tuned_table()}
    for name, table in tables.items():
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as file:
            file.write(table + '\n')
    print(f'Wrote {len(tables)} tables to {out_dir}: {", ".join(tables)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--out-dir', default='paper/tables')

    args = parser.parse_args()
    main(args.out_dir)
