"""Write the paper's tables as LaTeX files from the result files, so that no score in the paper is typed by hand.

Table I lists the datasets with their test, train and validation sizes. Table II gives the zero-shot and few-shot
macro-F1 of Jev, Clef and the five LLMs of Kastrati et al. (2026). Table III compares Jev with a
tuned question against zero-shot Jev, few-shot Jev, the best LLM score and the best fine-tuned transformer score on
each language. Table IV gives the cost of our runs, from the recorded input tokens and the providers' prices.

uv run python -m paper.write_tables
"""

import argparse
import glob
import json
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

SYSTEM_ONE = {'jev-1.14.0': 'Jev', 'clef': 'Clef'}
LLMS = {'gpt-4o': 'GPT-4o', 'gemini': 'Gemini', 'deepseek': 'DeepSeek', 'mistral': 'Mistral', 'claude': 'Claude'}
# Best macro-F1 (%) on our TSM test sets in Table 4 of the XLM-T paper (Barbieri et al., 2022): XLM-T fine-tuned on all
# eight TSM languages for English and German, XLM-R fine-tuned on French and Spanish for French. No other language has
# a fine-tuned transformer score on our test items. The paper gives 70.63, 77.35 and 73.55; these are rounded half up,
# because float formatting would round 77.35 and 73.55 down.
FINE_TUNED = {'English': 70.6, 'German': 77.4, 'French': 73.6}

# US$ per input token: typesafe.ai, and the Workers AI model page of Clef; neither charges for output
INPUT_PRICES = {'jev-1.14.0': 0.042e-6, 'clef': 0.24e-6}
# US$ per token for claude-opus-5-5: input, output, input written to the prompt cache, input read from it
OPUS_PRICES = {
    'input_tokens': 4e-6,
    'output_tokens': 20e-6,
    'cache_creation_input_tokens': 5e-6,
    'cache_read_input_tokens': 0.2e-6,
}


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
            '\\caption{The eight datasets. The Albanian texts are Facebook comments. Test is the sample that the LLMs '
            'were scored on; train and validation exclude every test item.}',
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
            '\\caption{Macro-F1 (\\%) of the System One models Jev and Clef and of the five LLMs reported by Kastrati '
            'et al.~\\cite{kastrati2026language}, zero-shot and few-shot with the same three English examples. Bold '
            'marks the best score in each column of a block. The mean is unweighted over the eight languages.}',
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
        fine_tuned = f'{FINE_TUNED[language]:.1f}' if language in FINE_TUNED else '--'
        rows.append(
            f'{language} & {zero_shot["jev-1.14.0"][language]:.1f} & {few_shot["jev-1.14.0"][language]:.1f} '
            f'& {tuned_cell} & {best:.1f} & {name} {setting} & ${jev - best:+.1f}$ & {fine_tuned} \\\\'
        )
    best_mean = sum(best_scores) / len(best_scores)
    tuned_mean = round(sum(tuned.values()) / len(tuned), 1)
    rows.append('\\midrule')
    rows.append(
        f'Mean & {zero_shot["jev-1.14.0"]["Mean"]:.1f} & {few_shot["jev-1.14.0"]["Mean"]:.1f} '
        f'& {tuned_mean:.1f} & {best_mean:.1f} & & ${tuned_mean - best_mean:+.1f}$ & \\\\'
    )
    return '\n'.join(
        [
            '\\begin{table}[t]',
            '\\centering',
            '\\caption{Macro-F1 (\\%) of Jev zero-shot (ZS), few-shot (FS) and with the tuned question, against the '
            'highest score any of the five LLMs reached on that language, zero-shot or few-shot. Bold marks a tuned '
            'score above the best LLM score. Fine-tuned is the best score that a fine-tuned XLM-T or XLM-R model '
            'reached on the same test set~\\cite{barbieri2022xlmt}; no such score exists for the other languages.}',
            '\\label{tab:tuned}',
            '\\setlength{\\tabcolsep}{3pt}',
            '\\begin{tabular}{lrrrrlrr}',
            '\\toprule',
            ' & \\multicolumn{3}{c}{Jev} & \\multicolumn{2}{c}{Best LLM} & & Fine-tuned \\\\',
            '\\cmidrule(lr){2-4}\\cmidrule(lr){5-6}\\cmidrule(lr){8-8}',
            'Language & ZS & FS & Tuned & Score & Model & $\\Delta$ & Score \\\\',
            '\\midrule',
            *rows,
            '\\bottomrule',
            '\\end{tabular}',
            '\\end{table}',
        ]
    )


def tuning_costs() -> tuple[float, float, int]:
    """The one-time tuning cost over all languages: Opus (start questions and rewrites), Jev, and Jev's input tokens."""
    opus, jev_tokens = 0.0, 0
    for language in CONFERENCE_TEST_FILES:
        run_dir = f'results/structured_tuning/{language.lower()}_01'
        with open(f'{run_dir}/opus_usage.json', encoding='utf-8') as file:
            usage = json.load(file)
        for step in ('start_question', 'tuning'):
            opus += sum(usage[step][kind] * price for kind, price in OPUS_PRICES.items())
        for path in glob.glob(f'{run_dir}/tuning/*.csv'):
            jev_tokens += int(pd.read_csv(path)['input_tokens'].sum())
    return opus, jev_tokens * INPUT_PRICES['jev-1.14.0'], jev_tokens


def costs_table() -> str:
    items = sum(len(read_csv_any_encoding(path)) for path in CONFERENCE_TEST_FILES.values())
    rows = []
    for setting, results in [('Zero-shot', 'results/zero_shot/baseline'), ('Few-shot', 'results/few_shot/baseline')]:
        for model, name in SYSTEM_ONE.items():
            tokens = sum(
                int(pd.read_csv(f'{results}/{model}/{language}.csv')['input_tokens'].sum())
                for language in CONFERENCE_TEST_FILES
            )
            cost = tokens * INPUT_PRICES[model]
            label = setting if model == 'jev-1.14.0' else ''
            rows.append(f'{label} & {name} & {tokens / 1e6:.1f} & {cost:.2f} & {1000 * cost / items:.3f} \\\\')
        rows.append('\\midrule')
    test_tokens = sum(
        int(
            pd.read_csv(f'results/structured_tuning/{language.lower()}_01/jev-1.14.0/{language}.csv')[
                'input_tokens'
            ].sum()
        )
        for language in CONFERENCE_TEST_FILES
    )
    test_cost = test_tokens * INPUT_PRICES['jev-1.14.0']
    rows.append(f'Tuned & Jev & {test_tokens / 1e6:.1f} & {test_cost:.2f} & {1000 * test_cost / items:.3f} \\\\')
    rows.append('\\midrule')
    opus, jev, jev_tokens = tuning_costs()
    rows.append(f'Tuning & Opus & & {opus:.2f} & \\\\')
    rows.append(f' & Jev & {jev_tokens / 1e6:.1f} & {jev:.2f} & \\\\')
    return '\n'.join(
        [
            '\\begin{table}[t]',
            '\\centering',
            '\\caption{Cost of our runs on the 12,970 test texts, and the one-time cost of tuning the questions of all '
            'eight languages. Input tokens are in millions. Prices per million tokens: Jev US\\$0.042 and Clef '
            'US\\$0.24 for input, with output free; Claude Opus 5.5 US\\$4 for input and US\\$20 for output.}',
            '\\label{tab:costs}',
            '\\setlength{\\tabcolsep}{4pt}',
            '\\begin{tabular}{llrrr}',
            '\\toprule',
            'Run & Model & Tokens & US\\$ & US\\$ per 1,000 texts \\\\',
            '\\midrule',
            *rows,
            '\\bottomrule',
            '\\end{tabular}',
            '\\end{table}',
        ]
    )


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    tables = {
        'datasets.tex': datasets_table(),
        'zero_few_shot.tex': zero_few_shot_table(),
        'tuned.tex': tuned_table(),
        'costs.tex': costs_table(),
    }
    for name, table in tables.items():
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as file:
            file.write(table + '\n')
    print(f'Wrote {len(tables)} tables to {out_dir}: {", ".join(tables)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--out-dir', default='paper/tables')

    args = parser.parse_args()
    main(args.out_dir)
