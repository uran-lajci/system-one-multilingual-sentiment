---
name: incremental-review
description: Make code changes one reviewable chunk at a time, stopping after each for the user to confirm, change or reject it. Use for any implementation, refactor, bug fix or migration that touches more than one place, and whenever the user says "step by step", "one at a time", "let me review as you go" or asks to approve changes before they land.
---

# Incremental review

Every change must stay small enough for the user to read and answer yes, no, or not like that, before the next change
buries it.

## Plan first

For more than two chunks, show the plan before touching code and wait for confirmation:

```
1. <chunk title>: <what and where, one line>
2. ...
```

If the plan changes, show the updated remaining steps.

## One chunk at a time

A chunk is one logical change, usually one file or one function. If it takes more than two lines to explain, split it.

```
**Step N/M: <title>**
What: <the change, and where>
Why: <one line, including why this over the alternative>
Watch out: <only if something could break, or an assumption is made>

[the edit]

Verify: <command to run, or what to look at>
Next: <the following step, one line>
```

Then stop and wait for the answer.

- Do not combine two chunks because they are small or related.
- Do not do the next thing "while in this file".
- If a chunk needs an unplanned change elsewhere, stop and say so.

## Answers

- **Confirmed**: do the next chunk.
- **Change it**: revise only that chunk, show it again, and wait.
- **Rejected**: drop it, say what that means for the rest of the plan, and show the revised remaining steps.

## When to skip

- A single edit, a typo, a one-line fix.
- Read-only work: questions, explanations, reviews.
- The user asks for everything at once. Do it, then list what changed.
