# CLAUDE.md

Guidance for Claude Code in this repository. These rules apply to every interaction: questions, explanations, and code changes.

## Why

Answers and diffs must be small enough for a human to read and review fully. Long answers and large changes get skimmed, and skimmed changes ship bugs.

## 1. Think before answering

- If a question or task can be read more than one way, ask one short clarifying question before answering. Do not guess.
- If it is clear, answer directly without asking for confirmation.

## 2. Simplicity first

- Give the shortest answer that fully answers the question.
- No preamble, no restating the question, no closing summary.
- Use a few sentences or a short list. Add detail only when asked.

## 3. Surgical

- Answer only what was asked. Mention related issues in one line at most; do not act on them.
- For code: change only the lines needed. No unrequested refactors, renames, formatting, or extra features.
- No comments or docstrings where the code or config already says what it does. Comment only what a reader cannot see, such as why a setting is needed.

## 4. Goal-driven

- For code changes, state in one line how to verify the change (test, command, or expected behavior).
- Keep each change small enough to review in one sitting. If a task needs more, propose the steps first and do them one at a time, as the `incremental-review` skill describes.

## The study

This repository benchmarks System One models on three-class sentiment analysis. It compares them with the LLM and SOTA scores in Kastrati et al. (2026), in `papers/`. The conference paper runs five models zero-shot on 10 languages (`docs/next-steps.md`); the 35-language and few-shot work waits until after it (`docs/future-work.md`). The study plan is in `docs/`. The README lists the repository layout and which files are the test sets.

- Choose questions and tune them on train and validation data only. Score each test set once, at the end.
- Report macro-F1 on the three labels, so scores compare directly with the paper.
- Compare a tuned model with zero-shot Jev and the few-shot LLMs, not with the zero-shot LLMs.
- Pin the exact model version in every run, such as `jev-1.14.0`, so results stay reproducible.
- Ask before any run that calls a paid API. Say which model, how many items, and the expected cost.

## Keeping this file short

This file is loaded into every session, so every line costs attention. When it passes about 200 lines, or a section only matters for certain files, propose moving that section to `.claude/rules/<topic>.md` (scoped with `paths:` frontmatter when it applies to specific files).

## Setup commands

Every command a new contributor must run after cloning goes in the "Setup" section of README.md. When a change adds or changes such a command, update that section in the same change.

## Python environment

uv manages Python and all dependencies. Add packages with `uv add <package>` (`uv add --dev <package>` for tools), run
anything with `uv run <command>`, and commit `uv.lock` with the change. Never use `pip`, and never edit dependency lists
in `pyproject.toml` by hand.

- Declare a lower bound only (`uv add` writes `>=`). `uv.lock` pins the exact versions, so an upper bound or `==` only
  adds a second copy that goes stale.
- Cap a version only when a known release breaks this code: `uv add 'pkg>=2,<3'`, then add a comment saying why. That
  comment is the one allowed hand edit.
- A package used without being imported (such as `pyarrow`, which `pandas` loads) gets a
  `[tool.deptry.per_rule_ignores]` `DEP002` entry with a comment saying who uses it.
- Upgrade with `uv lock --upgrade-package <package>`. Touch `pyproject.toml` only when the code needs a newer lower bound.
- Remove a package as soon as nothing uses it: `uv remove <package>` (`uv remove --dev <package>` for tools). deptry
  catches unused main packages, but not unused dev packages, so check those by hand whenever you delete code.
