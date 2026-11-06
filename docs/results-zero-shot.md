# Zero-shot results for the conference paper

On 6 November 2026 we ran five System One models zero-shot on the 10 conference languages, 15,864 test items in total. Every model got the same Choice question for every language, with no examples and no tuning. [next-steps.md](next-steps.md) gives the question.

## What we compare against

We compare with the five LLMs of Kastrati et al. (2026), evaluated **zero-shot**. We did not run the LLMs ourselves. Their scores come from the "Zero-Shot" rows of the paper's Tables 4 and 6, and `experiments/zero_shot/paper_scores.csv` holds them.

- **LLMs:** gpt-4o-2024-08-06, gemini-2.0-flash, deepseek-chat (DeepSeek-V3), mistral-large-2411 and claude-3-7-sonnet-20250219.
- **Same test items:** our 10 test files are the files the authors scored. For Bosnian, Croatian and Serbian, they are the 20% samples that Zenun Kastrati sent.
- **Same metric:** macro-F1 on the three labels, the unweighted mean of the per-class F1 scores, as in the paper.
- **Different input format:** each kind of model gets its own format. The LLMs got one shared prompt, "Given a piece of text, classify its sentiment as negative, positive, or neutral. Return only a single word, either POSITIVE, NEGATIVE or NEUTRAL." The System One models got a Choice question with a description of each label, and return a probability for each label.

We do not compare with the paper's few-shot LLM scores or with the SOTA column. A comparison with few-shot LLMs needs a few-shot run of the System One models, which [next-steps.md](next-steps.md#few-shot-run) plans with the paper's three examples.

## Models

| Model | Version | Access |
|---|---|---|
| Jev | `jev-1.14.0` | TypeSafe API |
| Clef | Hugging Face revision `cfddda0`; Cloudflare `api-version` `2026-10-01.epoch` | Cloudflare Workers AI |
| Clef-flash | Hugging Face revision `fb4417d`; Cloudflare `api-version` `2026-10-01.epoch` | Cloudflare Workers AI |
| Laya | `convaiinnovations/laya@55cf4c4`, laya 0.4.22 | local GPU |
| Laya-multilingual | `convaiinnovations/laya-multilingual@e4e9ddf`, laya 0.4.22 | local GPU |

The Cloudflare `api-version` stayed the same for the whole run.

## Results

Macro-F1 (%), zero-shot. The five LLM columns are from Kastrati et al. (2026). Bold marks a score where Jev beats all five LLMs.

| Language | Items | Jev | Clef | Clef-flash | Laya | Laya-multilingual | GPT-4o | Gemini | DeepSeek | Mistral | Claude |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| English | 870 | 68.0 | 64.9 | 61.1 | 53.7 | 38.0 | 70.1 | 65.1 | 71.9 | 62.5 | 73.3 |
| German | 870 | 73.3 | 65.9 | 55.1 | 45.2 | 36.7 | 71.0 | 61.4 | 70.8 | 60.9 | 75.6 |
| French | 870 | 63.7 | 39.9 | 38.7 | 45.7 | 29.1 | 55.8 | 64.9 | 58.2 | 51.7 | 52.6 |
| Albanian | 2,148 | 58.2 | 55.4 | 45.7 | 36.9 | 36.2 | 69.8 | 53.4 | 54.0 | 50.3 | 64.8 |
| Bosnian | 782 | 59.2 | 48.0 | 41.8 | 26.3 | 27.2 | 58.3 | 54.6 | 55.6 | 43.8 | 59.2 |
| Croatian | 2,790 | **56.9** | 40.1 | 36.6 | 25.0 | 23.7 | 50.5 | 55.1 | 56.3 | 37.6 | 53.5 |
| Serbian | 2,272 | 52.5 | 49.7 | 47.9 | 29.4 | 30.7 | 58.1 | 50.1 | 47.6 | 45.9 | 57.1 |
| Swedish | 2,368 | 61.4 | 68.7 | 61.0 | 49.8 | 37.3 | 78.7 | 72.9 | 69.1 | 66.4 | 76.7 |
| Norwegian | 1,847 | 66.5 | 64.7 | 64.4 | 41.8 | 37.3 | 76.8 | 61.6 | 57.1 | 64.8 | 72.5 |
| Danish | 1,047 | **72.3** | 56.0 | 50.6 | 38.2 | 28.5 | 68.7 | 66.3 | 69.0 | 58.7 | 72.1 |
| **Mean** | **15,864** | **63.2** | **55.3** | **50.3** | **39.2** | **32.5** | **65.8** | **60.5** | **61.0** | **54.3** | **65.7** |

The mean is the unweighted mean over the 10 languages.

## Observations

- Jev ranks third of the ten models on the mean, behind GPT-4o and Claude and ahead of DeepSeek, Gemini and Mistral. It is the best model in Croatian and Danish, and ties Claude in Bosnian.
- Clef scores about the same as Mistral. Clef-flash, Laya and Laya-multilingual score below all five LLMs.
- Clef, Clef-flash, Laya and Laya-multilingual predict "neutral" far too often. About 37% of the test items are neutral, but they predict neutral for 67%, 74%, 76% and 86% of the items. Jev predicts it for 27%. This explains much of their lower scores.
- Laya-multilingual scores below the English-only Laya in 8 of the 10 languages, although it was trained for many languages.
- On the 7 languages whose test items did not change since the pilot run, Jev's scores moved by at most 0.6 points, for example Danish from 72.9 to 72.3. Jev is close to, but not fully, deterministic.
- In 34 of the 15,864 items, Jev's probabilities tie at two decimals, such as 0.49, 0.49 and 0.02, and Jev picks one of the tied labels. We score Jev's own choice.

## Question sensitivity

On 6 and 7 November 2026 we ran the same five models on the same 10 test sets with 10 versions of the question: the original (`baseline`) and nine more (`v01` to `v09` in `experiments/zero_shot/questions/`). The nine were written in a separate Claude session that knew nothing about our results, and reviewed by hand. All ten are zero-shot: the same three labels, plain-text criteria and no examples. We select no version; the headline scores above stay those of the original question.

10-language mean macro-F1 (%) per question version:

| Version | Jev | Clef | Clef-flash | Laya | Laya-multilingual |
|---|---:|---:|---:|---:|---:|
| baseline | 63.2 | 55.3 | 50.3 | 39.2 | 32.5 |
| v01 | 63.8 | 59.1 | 52.8 | 43.9 | 45.4 |
| v02 | 62.4 | 50.6 | 48.8 | 41.8 | 37.3 |
| v03 | 62.8 | 57.0 | 54.4 | 40.9 | 37.2 |
| v04 | 61.7 | 51.1 | 51.7 | 25.9 | 29.9 |
| v05 | 64.2 | 60.9 | 53.3 | 41.6 | 42.7 |
| v06 | 62.9 | 42.0 | 39.9 | 36.6 | 42.1 |
| v07 | 62.9 | 53.7 | 50.8 | 32.4 | 31.2 |
| v08 | 63.4 | 50.7 | 51.7 | 37.8 | 34.6 |
| v09 | 61.7 | 55.4 | 53.1 | 35.8 | 43.3 |
| **Mean** | **62.9** | **53.6** | **50.7** | **37.6** | **37.6** |
| **Minimum** | 61.7 | 42.0 | 39.9 | 25.9 | 29.9 |
| **Maximum** | 64.2 | 60.9 | 54.4 | 43.9 | 45.4 |
| **Spread** | 2.5 | 18.9 | 14.5 | 18.0 | 15.5 |

- Jev hardly depends on the wording: all ten versions fall within 2.5 points. Its worst version (61.7) is still above DeepSeek (61.0), Gemini (60.5) and Mistral (54.3), and its best (64.2) is still below GPT-4o (65.8) and Claude (65.7). So Jev's rank, third of ten models, holds for every version.
- Clef, Clef-flash, Laya and Laya-multilingual depend strongly on the wording, with spreads of 14.5 to 18.9 points. Clef ranges from below Mistral (42.0) to about Gemini's level (60.9).
- Some versions hurt particular models: v06, which asks for the dominant emotional tone, lowers both Clef models by about 12 points against the mean of their other versions, and v04, the longest version, gives Laya its lowest score.
- The original question is an ordinary version, not a lucky one. It ranks between 4th and 8th of the ten versions for each model.
- Two runs stopped once with a passing error (Clef on v07, Clef-flash on v03). Both resumed and finished, and all 450 result files are complete. The Cloudflare `api-version` stayed `2026-10-01.epoch` throughout.

## Cost

| Model | Input tokens | Cost |
|---|---:|---:|
| Jev | 6,156,912 | about USD 0.26 |
| Clef | 3,290,131 | about USD 0.79 |
| Clef-flash | 3,290,131 | about USD 0.13 |
| Laya, Laya-multilingual | – | free, local |

The nine extra question versions cost about USD 11.80 in total:

| Model | Input tokens | Cost |
|---|---:|---:|
| Jev | 59,489,256 | about USD 2.50 |
| Clef | 33,497,859 | about USD 8.00 |
| Clef-flash | 33,497,859 | about USD 1.30 |

## Files and how to reproduce

- `results/zero_shot/<version>/<model>/<language>.csv`: one row per test item, with the row number, gold label, predicted label, the three probabilities, the model version and the date. `<version>` is `baseline` or `v01` to `v09`. The files hold no text.
- `results/zero_shot/<version>/scores.csv`: the per-language table for one version, like the results table above for `baseline`.
- `results/zero_shot/sensitivity.csv`: the question sensitivity table.

```
uv run python -m experiments.zero_shot.classify_sentiment -m <model> -q experiments/zero_shot/questions/<version>.json    # -q defaults to baseline.json
uv run python -m experiments.zero_shot.score_predictions    # scores every question version, baseline included
```

The runner skips a language whose results file already exists, so delete a model's folder before running it again.
