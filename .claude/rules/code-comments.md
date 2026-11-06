# Code comments

A comment goes stale when the code changes, and a stale comment misleads. Before writing one, try to make it unneeded:

1. Rename the variable, function or class.
2. Extract the confusing expression into a named variable or function.
3. Split the function so each part is obvious.

Write the comment only if all three fail.

## Allowed

- **Why**: the reason for a decision the code cannot show, such as a setting that is load-bearing.
- **Warning**: a non-obvious consequence, such as "keep in sync with X", "not thread-safe" or "mutates its input".
- **Regex**: one line of example matches, never a part-by-part breakdown of the pattern.

  ```python
  # Returns 'main' for `--base main`, `--base=main` or `-B main`
  ```
- **Third-party quirk**: an obscure value or behavior of code we cannot change.
- **TODO**: a real pending task with an issue number (`# TODO(#52): ...`). Remove it when the task is done.
- **Docstring**: on a module, class or function whose purpose the name and signature do not already say.

## Delete on sight

- A comment that restates the code (`# open the file`).
- Commented-out code. Git keeps it.
- Change logs, author names and dates. Git keeps them.
- Section banners (`# ===== HELPERS =====`).
- A vague note that leaves the reader guessing (`# handle later`).

When you change code, reread every comment next to it. In a review, for each comment ask whether a rename or an
extracted function would remove the need for it.
