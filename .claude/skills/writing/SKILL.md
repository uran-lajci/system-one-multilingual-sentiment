---
name: writing
description: Plain-English rules for prose in this repository, such as docs, study notes, READMEs, rules files, skills, commit messages, PR descriptions, GitHub issues and code comments. Never for code or identifiers. Use whenever writing or editing any of these, when asked to make text clearer or shorter, or when text reads like AI.
---

# Writing

Readers here are researchers and reviewers, many writing in their second or third language.
Write so a reader with intermediate English understands each sentence on the first read.

## Words

- Use the short common word: use (not utilize or leverage), start (not initiate), help (not facilitate), make sure (not
  ensure), before (not prior to), about (not regarding), get (not obtain), show (not demonstrate), also (not
  additionally or furthermore).
- Give one thing one name. Do not alternate "test set" and "evaluation split" for the same data.
- Keep technical names exact: macro-F1, zero-shot, Choice, `jev-1.14.0`, `arq`. Do not swap a precise term for a vaguer
  common word.
- No marketing words: seamless, robust, powerful, cutting-edge, effortless, comprehensive. "Robustness" is fine for a
  property the study measures.
- No filler: "it is important to note that", "in order to", "basically", "simply".
- American spelling: behavior, serialize, analyze, license.

## Sentences

- Active voice, with the actor named: "the script writes the predictions", not "the predictions are written".
- An action is a verb: "check the text", not "perform a check of the text".
- Keep sentences under about 20 words. Split a longer one into two.
- One instruction per sentence. Put a condition before its instruction: "If a request fails, retry it."
- Steps go in a numbered list, one action per step, in the imperative.
- One topic per paragraph.

## Commits, PRs and issues

- Commit title: `<type>: <summary>` (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`). The summary is imperative and
  lowercase, with no period.
- A commit body or PR description says why the change is needed and what a reviewer should check. The diff already
  shows what changed.

## Before you return text

1. Write only what was asked: no preamble, no closing summary.
2. Read each sentence once more. Split any over 20 words, make passive voice active, and replace any word from the
   lists above.
