---
paths:
  - "**/*.py"
---

# Python Style

These rules apply to every `.py` file.

## Tooling

`ruff` lints and formats, `mypy` type-checks. `pyproject.toml` holds these settings, which enforce the mechanical rules:

| Setting | Effect |
|---|---|
| `requires-python = ">=3.12,<3.13"` | Code targets Python 3.12. |
| `line-length = 120` | Lines wrap at 120. |
| lint `select = ["E", "F", "I", "W", …]` | Imports are sorted; unused and undefined names fail. |
| lint `"Q"` with `inline-quotes = "single"`, format `quote-style = "single"` | Single quotes. `ruff format` rewrites them, `ruff check` fails on them. Docstrings use `"""`. |
| lint `"TID"` with `banned-api` | Importing `typing.Any`, `pathlib` or `sys` fails. |
| lint `"TID"` with `ban-relative-imports = "all"` | Relative imports fail. |
| mypy `strict = true`, `disallow_any_explicit = true` | Every function is fully annotated, and an explicit `Any` anywhere fails. |

The tools enforce these, so this guide does not restate them as things to remember. What follows is the part no tool
checks.

## Less is more

Write the minimum code that solves the problem. No speculative abstractions, no configuration hook nothing asks for, no
layer added because a second caller might arrive.

## Functions

Wrap code in a helper only when it holds something non-obvious — a formula, a regex, a multi-step transformation. A
one-liner that reads as what it does stays where it is.

```python
# WRONG — too simple to warrant a function
def get_output_path(directory: str, filename: str) -> str:
    return os.path.join(directory, filename)


# RIGHT — wrap a regex, because the pattern is not readable at the call site
def extract_invoice_number(text: str) -> str:
    match = re.search(r'INV-(\d+)', text)
    if match is None:
        raise ValueError(f'No invoice number in: {text!r}')
    return match.group(1)
```

## Type hints

Annotate function parameters and return types, not variables.

Use the lowercase built-in generics — `list`, `dict`, `tuple` — not their `typing` equivalents, and `X | Y` for unions.

```python
def process_records(records: list[dict[str, str]], limit: int) -> list[str]: ...
```

Never `Any`. It turns strict mode off for everything it touches. The ban has no exemptions, and it is never silenced with
`# noqa` or `# type: ignore`.

When a value's type is unknown, such as the result of `json.load` or a payload from outside, annotate it `object` and
narrow it where it is used. `object` forces the check that `Any` skips.

```python
def read_count(payload: object) -> int:
    count = payload.get('count') if isinstance(payload, dict) else None
    if not isinstance(count, int):
        raise ValueError(f'No integer count in: {payload!r}')
    return count
```

## Paths

`os.path`, not `pathlib`. A single `Path` spreads through every signature it meets.

```python
# WRONG
from pathlib import Path

output = Path(directory) / 'output.csv'

# RIGHT
import os

output = os.path.join(directory, 'output.csv')
```

## CSV files

`pandas` reads and writes CSV: `pd.read_csv(path)`, `df.to_csv(path, index=False)`. The `.tsv` files in
`data/afrisenti/` also need `sep='\t'`.

## Shebang

Never write a shebang line (`#!/usr/bin/env python3`). Run Python files with `uv run` or `python3 <file>`.

## Spacing

Blank lines group related statements: the work that reads, the work that transforms, the work that writes.

A signature that does not fit on one line takes one argument per line. End the last argument with a trailing comma, so
`ruff format` keeps one argument per line instead of packing them onto one.

```python
async def complete(
    prompt: str,
    model_id: str,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> str: ...
```

## Zen of Python

- Beautiful is better than ugly.
- Simple is better than complex.
- Flat is better than nested.
- Readability counts.
- Errors should never pass silently.
- There should be one obvious way to do it.
- If the implementation is hard to explain, it's a bad idea.
