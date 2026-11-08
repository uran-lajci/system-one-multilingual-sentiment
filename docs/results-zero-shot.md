# Zero-shot results for the conference paper

On 6 November 2026 we ran five System One models zero-shot on 10 languages. This file reports the three models of the conference paper, Jev, Clef and Clef-flash, on the 8 conference languages, 12,970 test items in total. It leaves out Laya and Laya-multilingual, and Norwegian and Danish, which have no train or validation data. Every model got the same Choice question for every language, with no examples and no tuning. [next-steps.md](next-steps.md) gives the question.

## What we compare against

We compare with the five LLMs of Kastrati et al. (2026), evaluated **zero-shot**. We did not run the LLMs ourselves. Their scores come from the "Zero-Shot" rows of the paper's Tables 4 and 6, and `experiments/zero_shot/paper_scores.csv` holds them.

- **LLMs:** gpt-4o-2024-08-06, gemini-2.0-flash, deepseek-chat (DeepSeek-V3), mistral-large-2411 and claude-3-7-sonnet-20250219.
- **Same test items:** our 8 test files are the files the authors scored. For Bosnian, Croatian and Serbian, they are the 20% samples that Zenun Kastrati sent.
- **Same metric:** macro-F1 on the three labels, the unweighted mean of the per-class F1 scores, as in the paper.
- **Different input format:** each kind of model gets its own format. The LLMs got one shared prompt, "Given a piece of text, classify its sentiment as negative, positive, or neutral. Return only a single word, either POSITIVE, NEGATIVE or NEUTRAL." The System One models got a Choice question with a description of each label, and return a probability for each label.

We do not compare with the paper's few-shot LLM scores or with the SOTA column. A comparison with few-shot LLMs needs a few-shot run of the System One models, which [next-steps.md](next-steps.md#few-shot-run) plans with the paper's three examples.

## Models

| Model | Version | Access |
|---|---|---|
| Jev | `jev-1.14.0` | TypeSafe API |
| Clef | Hugging Face revision `cfddda0`; Cloudflare `api-version` `2026-10-01.epoch` | Cloudflare Workers AI |
| Clef-flash | Hugging Face revision `fb4417d`; Cloudflare `api-version` `2026-10-01.epoch` | Cloudflare Workers AI |

The Cloudflare `api-version` stayed the same for the whole run.

## Results

Macro-F1 (%), zero-shot. The five LLM columns are from Kastrati et al. (2026). Bold marks a score where Jev beats all five LLMs.

| Language | Items | Jev | Clef | Clef-flash | GPT-4o | Gemini | DeepSeek | Mistral | Claude |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| English | 870 | 68.0 | 64.9 | 61.1 | 70.1 | 65.1 | 71.9 | 62.5 | 73.3 |
| German | 870 | 73.3 | 65.9 | 55.1 | 71.0 | 61.4 | 70.8 | 60.9 | 75.6 |
| French | 870 | 63.7 | 39.9 | 38.7 | 55.8 | 64.9 | 58.2 | 51.7 | 52.6 |
| Albanian | 2,148 | 58.2 | 55.4 | 45.7 | 69.8 | 53.4 | 54.0 | 50.3 | 64.8 |
| Bosnian | 782 | 59.2 | 48.0 | 41.8 | 58.3 | 54.6 | 55.6 | 43.8 | 59.2 |
| Croatian | 2,790 | **56.9** | 40.1 | 36.6 | 50.5 | 55.1 | 56.3 | 37.6 | 53.5 |
| Serbian | 2,272 | 52.5 | 49.7 | 47.9 | 58.1 | 50.1 | 47.6 | 45.9 | 57.1 |
| Swedish | 2,368 | 61.4 | 68.7 | 61.0 | 78.7 | 72.9 | 69.1 | 66.4 | 76.7 |
| **Mean** | **12,970** | **61.7** | **54.1** | **48.5** | **64.0** | **59.7** | **60.4** | **52.4** | **64.1** |

The mean is the unweighted mean over the 8 languages.

## Observations

- Jev ranks third of the eight models on the mean, behind Claude and GPT-4o and ahead of DeepSeek, Gemini and Mistral. It is the best model in Croatian, and ties Claude in Bosnian.
- Clef scores slightly above Mistral. Clef-flash scores below all five LLMs.
- Clef and Clef-flash predict "neutral" far too often. About 34% of the test items are neutral, but they predict neutral for 65% and 73% of the items. Jev predicts it for 27%. This explains much of their lower scores.
- On the languages whose test items did not change since the pilot run, Jev's scores moved by at most 0.6 points. Jev is close to, but not fully, deterministic.
- In 53 of the 12,970 items, two labels share Jev's highest probability at two decimals, such as 0.49, 0.49 and 0.02, and Jev picks one of the tied labels. We score Jev's own choice.

## Cost

The costs are those of the whole run, on 10 languages. Laya and Laya-multilingual ran locally for free.

| Model | Input tokens | Cost |
|---|---:|---:|
| Jev | 6,156,912 | about USD 0.26 |
| Clef | 3,290,131 | about USD 0.79 |
| Clef-flash | 3,290,131 | about USD 0.13 |

## Files and how to reproduce

- `results/zero_shot/baseline/<model>/<language>.csv`: one row per test item, with the row number, gold label, predicted label, the three probabilities, the model version and the date. The files hold no text.
- `results/zero_shot/baseline/scores.csv`: the results table above.

```
uv run python -m experiments.zero_shot.classify_sentiment -m <model>
uv run python -m experiments.zero_shot.score_predictions
```

The runner skips a language whose results file already exists, so delete a model's folder before running it again.
