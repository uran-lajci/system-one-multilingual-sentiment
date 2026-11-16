"""Write the Opus token counts of each tuning run to results/structured_tuning/<run>/opus_usage.json.

The start-question logs and tuning conversations quote train texts, and for Bosnian, Croatian and Serbian
they stay out of git. The usage files hold only token counts, so they can be committed, and paper/write_tables.py
computes the tuning cost from them on any clone.

uv run python -m experiments.structured_tuning.write_opus_usage
"""

import argparse
import glob
import json
import os

TOKEN_KINDS = ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')


def total_tokens(calls: list[dict[str, object]]) -> dict[str, int]:
    return {kind: sum(int(str(call.get(kind) or 0)) for call in calls) for kind in TOKEN_KINDS} | {'calls': len(calls)}


def main(experiment_dir: str, results_dir: str) -> None:
    run_dirs = sorted(glob.glob(os.path.join(experiment_dir, 'runs', '*')))
    for run_dir in run_dirs:
        name = os.path.basename(run_dir)
        with open(os.path.join(experiment_dir, 'start', 'calls', f'{name}.json'), encoding='utf-8') as file:
            start_call = json.load(file)
        with open(os.path.join(run_dir, 'log.json'), encoding='utf-8') as file:
            log = json.load(file)
        tuning_calls = [call for version in log['versions'] for call in version.get('opus_calls', [])]

        usage = {
            'model': log['model'],
            'start_question': total_tokens([start_call]),
            'tuning': total_tokens(tuning_calls),
        }
        out_path = os.path.join(results_dir, name, 'opus_usage.json')
        with open(out_path, 'w', encoding='utf-8') as file:
            json.dump(usage, file, indent=2)
            file.write('\n')
        print(f'{name}: wrote {out_path}')

    print(f'Wrote Opus usage for {len(run_dirs)} runs to {results_dir}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-e', '--experiment-dir', default='experiments/structured_tuning')
    parser.add_argument('-r', '--results-dir', default='results/structured_tuning')

    args = parser.parse_args()
    main(args.experiment_dir, args.results_dir)
