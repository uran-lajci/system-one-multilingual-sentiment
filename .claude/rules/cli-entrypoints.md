# CLI entry points

An entry point is any module with an `if __name__ == '__main__'` block. Everything else in the file follows
`python.md`.

## Name

The module name says what running it does, as a verb on a noun: `classify_sentiment.py`, `score_predictions.py`,
`merge_csv_files.py`. The experiment folder above it carries the experiment name: `experiments/zero_shot/`.

## Structure

Imports, helper functions, `main`, then the `__main__` block. Nothing runs at import time. `main` holds the whole run and
takes plain arguments, never the argparse `Namespace`.

```python
"""Run a System One model over the test sets with one zero-shot Choice question.

uv run python -m experiments.zero_shot.classify_sentiment --model jev-1.14.0
"""

import argparse
import asyncio


async def main(model: str, concurrency: int, out: str) -> None: ...


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-m', '--model', required=True)
    parser.add_argument('-c', '--concurrency', type=int, default=16)
    parser.add_argument('-o', '--out', default='results')

    args = parser.parse_args()
    asyncio.run(main(args.model, args.concurrency, args.out))
```

- Every argument has a short flag and a long flag. The long flag matches the `main` argument it feeds.
- An argument is either `required=True` or has a `default=`. Defaults live only in the parser, never as a fallback
  inside `main`.
- `type=` parses anything that is not a string, so `main` never parses its own arguments.
- A `main` that awaits anything is `async def`, started by exactly one `asyncio.run(...)` as the last line.
- Every entry point opens with a docstring holding one line of purpose and the exact run command, and passes it as
  `description=__doc__`.
- Run entry points as modules from the repository root (`uv run python -m experiments.<experiment>.<module>`), so their
  imports of shared code resolve.

## Output

Entry points use `print`. A long run prints a counted line per batch, and every run ends with one line saying what it
did: rows written, rows skipped and why, files created.
