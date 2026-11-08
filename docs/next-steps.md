# Next steps

The conference paper runs five System One models on 8 languages, zero-shot and few-shot with the paper's three examples. All 8 have train and validation data, and the paper also tunes Jev's question for each of them. Everything else waits until after the conference, in [future-work.md](future-work.md).

## Conference scope

| Language | Test file in `data/` | Items |
|---|---|---:|
| English | `tsm/test/english.csv` | 870 |
| German | `tsm/test/german.csv` | 870 |
| French | `tsm/test/french.csv` | 870 |
| Albanian | `lmr-sms/test/Albanian_ts2148.csv` | 2,148 |
| Bosnian | `lmr-sms/test/Bosnian_ts782.csv` | 782 |
| Croatian | `lmr-sms/test/Croatian_ts2790.csv` | 2,790 |
| Serbian | `lmr-sms/test/Serbian_ts2272.csv` | 2,272 |
| Swedish | `lmr-sms/test/Swedish.csv` | 2,368 |
| **Total** | | **12,970** |

The models are Jev, Clef, Clef-flash, Laya and Laya-multilingual. [background.md](background.md) gives the version of each.

## Zero-shot run

We run all five models on these 12,970 test items with one Choice question, the same for every language, with no examples and no tuning. We compare the scores with the zero-shot scores of the five LLMs in [data-and-baselines.md](data-and-baselines.md).

```json
{
  "sentiment": {
    "type": "choice",
    "instructions": "What is the overall sentiment expressed by the author of text ?",
    "criteria": {
      "positive": "The text expresses a positive opinion, emotion or attitude.",
      "neutral": "The text is factual or expresses neither a clearly positive nor a clearly negative sentiment.",
      "negative": "The text expresses a negative opinion, emotion or attitude."
    }
  }
}
```

A pilot run of Jev on 75,080 items, before we used the paper's exact samples, needed about 30.3 million input tokens, or about 404 per item. One run over the 12,970 items therefore needs about 5.2 million input tokens. That costs about USD 0.25 with Jev, USD 1.20 with Clef and USD 0.20 with Clef-flash. Laya runs locally for free.

We ran all five models on 6 November 2026, also on Norwegian and Danish, which the paper no longer reports. [results-zero-shot.md](results-zero-shot.md) gives the scores, the comparison and the commands to reproduce them.

## Few-shot run

All five models run again on the same 8 test sets. The question is the baseline question plus the three examples that Kastrati et al. (2026) gave the LLMs, one per label. Our models and the LLMs then see the same examples, so we compare the scores directly with the paper's few-shot LLM column.

The paper kept the same three English examples for every dataset and language, and so do we. We copy them word for word from the paper. All three are tweets from `data/tsm/train/english.csv`, at lines 5, 33 and 37, and none is in a test set. The paper's text differs slightly from our train rows: it drops `#cincodemayo` from the positive example and adds a full stop to the neutral one.

Each criterion becomes an object. `description` holds the zero-shot wording word for word, and `examples` holds the paper's example for that label. We add nothing else, such as a `not_for` field. The key is `description` so that it comes before `examples`, since Clef sorts keys alphabetically.

```json
"positive": {
  "description": "The text expresses a positive opinion, emotion or attitude.",
  "examples": ["Not even 20 pages into Paper Towns and the book centers around the night of May 5th. I know its gonna be a good one now!"]
}
```

Our paper must state two more differences. The criteria change from plain strings to objects, so the shape changes as well as the examples. The LLMs saw the examples before the input text, and our models see them inside the criteria.

`experiments/few_shot/add_examples.py` writes `experiments/few_shot/questions/baseline.json` from the zero-shot question and changes only the criteria, as above. `experiments/few_shot/paper_scores.csv` holds the paper's few-shot LLM scores.

```bash
uv run python -m experiments.few_shot.add_examples
uv run python -m experiments.zero_shot.classify_sentiment -m jev-1.14.0 -q experiments/few_shot/questions/baseline.json
uv run python -m experiments.zero_shot.score_predictions -r results/few_shot -p experiments/few_shot/paper_scores.csv
```

The three examples add about 100 input tokens to each item. Zero-shot used 388 per item with Jev and 207 with Clef and Clef-flash, so the run costs about USD 1.70 for Jev, Clef and Clef-flash together. Laya runs locally.

## Structured iterative tuning

Opus writes a structured question for each dataset from its train data, and then tunes it on Jev's errors on other train data. We pick the version on validation data, which Opus never sees, and score the test set once.

This covers all 8 languages.

Only Jev is tuned. Clef and Laya may not accept JSON instructions, JSON criteria or three questions in one request. A tuned Jev has seen labelled data, so we compare it with zero-shot Jev and with the few-shot LLMs, not with the zero-shot LLMs. Our paper must say that Jev used 750 labelled train texts and the validation set, while the LLMs saw 3 examples.

### The input

- **State:** a JSON object with `context` and `text`. `context` describes the dataset in one to three sentences: its source, its time and its language. We write it from the dataset's paper, not from labelled data. The contexts are in `experiments/structured_tuning/contexts.json`, which so far holds English and Albanian.
- **Instructions:** a JSON object with `question` and `rule`. `rule` says where the annotators draw the line between the labels.
- **Criteria:** one JSON object per label with `what`, `examples`, `cues` and `not_for`.
  - `what` describes the texts that get the label.
  - `examples` holds 1 to 4 train texts, copied word for word. A text that is not in English gets its English meaning in brackets.
  - `cues` lists words and short phrases that signal the label, with their English meaning if they are not in English.
  - `not_for` says what looks like the label but belongs to another one.
- **Label orders:** Jev gets the same question three times in one request, with the labels in three orders: neutral, positive, negative; positive, negative, neutral; and negative, neutral, positive. We average the three probabilities of each label and take the most probable label, because Jev leans toward the label listed first.

A question stays under 400 words, not counting the English meanings in brackets.

### Step 1: the start questions

For each dataset, Opus (`claude-opus-5-5`, effort `medium`) writes one start question. It reads 50 texts per label, drawn from the train file with seed 1, and the dataset's context. The prompt describes the fields above. It shows no question from our AlbAna work, so no rule tuned by hand on AlbAna reaches other datasets. Opus returns the fields as JSON, and the script builds the three label orders. If an answer fails the format check, the script repeats the call with the same seed.

### Step 2: the tuning loop

Each dataset gets one tuning run, which starts from its start question. The run is one conversation with `claude-opus-5-5`, with effort `medium`.

1. Draw a development set of 600 train texts with seed 1, leaving out the 150 texts that Opus saw for the start question. The draw is simple random sampling, so the labels keep their train proportions.
2. Score the current version with `jev-1.14.0` on the development set and on the validation set.
3. Send Opus the development results only: the macro-F1, the confusion matrix and every misclassified text, with its gold label, Jev's label and Jev's three probabilities. Opus never sees a validation text or a validation score.
4. Opus writes an error analysis, then a new version in the structured format, with examples copied from texts it has seen.
5. Repeat from step 2 until Opus has written 10 new versions.

While tuning, Jev gets only the first label order, with neutral first, which costs a third as much.

### Selection and test

We keep the version with the highest validation macro-F1, and on a tie, the earlier one. Jev scores that version once on the test set, with the three label orders averaged. We report this one test score per dataset. A single run shows no spread: on English and Albanian, 5 runs with seeds 1 to 5 differed by up to 3 points on test.

The validation sets of English, German and French hold about 324 texts each. Picking the best of 11 versions on them is therefore noisier than on the larger LMR-SMS validation sets.

### Commands, logs and cost

The code and outputs are in `experiments/structured_tuning/` and `results/structured_tuning/`. The start questions and their Opus logs are in `experiments/structured_tuning/start/`, and the kept questions in `experiments/structured_tuning/questions/`. For Albanian:

```bash
uv run python -m experiments.structured_tuning.induce_questions -l Albanian -t data/lmr-sms/train/Albanian.csv -x albanian -n 1
uv run python -m experiments.structured_tuning.tune_question -s 1 -x albanian_01 -q experiments/structured_tuning/start/questions/albanian_01.json
uv run python -m experiments.structured_tuning.classify_sentiment -q experiments/structured_tuning/questions/albanian_01.json -l Albanian
```

We commit the prompts, the contexts, every message of each conversation, every version and the train row numbers of each development set. The English and Albanian logs name the paths these files had before we moved them, under `experiments/structured_induction/`.

English and Albanian were done on 8 November 2026. The other 6 languages are next, and each needs its context first. On English and Albanian, a tuning run cost about USD 2.50 to 3.50, mostly for Opus, and a test scoring up to USD 0.50.

## Open decisions

- **Venue and deadline:** we have not chosen the conference yet.
- **SOTA column:** if the paper shows it, we must first settle what the Albanian SOTA of 72.1 measures. data-and-baselines.md and background.md describe it differently.
