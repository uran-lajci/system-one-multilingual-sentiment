# Next steps

The conference paper runs five System One models on 10 languages. It tests hand-written zero-shot questions, few-shot with the paper's three examples, and questions that Opus writes from English train data. Everything else waits until after the conference, in [future-work.md](future-work.md).

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
| Norwegian | `lmr-sms/test/Norwegian.csv` | 1,847 |
| Danish | `lmr-sms/test/Danish.csv` | 1,047 |
| **Total** | | **15,864** |

The models are Jev, Clef, Clef-flash, Laya and Laya-multilingual. [background.md](background.md) gives the version of each.

## Zero-shot run

We run all five models on these 15,864 test items with one Choice question, the same for every language, with no examples and no tuning. We compare the scores with the zero-shot scores of the five LLMs in [data-and-baselines.md](data-and-baselines.md).

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

A pilot run of Jev on 75,080 items, before we used the paper's exact samples, needed about 30.3 million input tokens, or about 404 per item. One run over the 15,864 items therefore needs about 6.4 million input tokens. That costs about USD 0.30 with Jev, USD 1.50 with Clef and USD 0.25 with Clef-flash. Laya runs locally for free.

We ran all five models on 6 November 2026. [results-zero-shot.md](results-zero-shot.md) gives the scores, the comparison and the commands to reproduce them.

## Question sensitivity

The zero-shot run uses one question, so we do not know how much the scores depend on its wording. We therefore run all five models on the same 10 test sets with 10 versions of the question: the original, `baseline.json`, and nine more, `v01.json` to `v09.json` in `experiments/zero_shot/questions/`. I wrote the nine in a separate Claude session that knew nothing about our results, and reviewed them myself. All ten stay zero-shot: the same three labels, plain-text criteria and no examples.

For each model, we report the 10-language mean macro-F1 of every version, and the mean, minimum and maximum across the 10 versions. The headline score stays the original question, which was fixed before the other versions existed. We do not pick the best version, so the test sets are not used for tuning, even though each test set is now scored once per version.

The nine new versions cost about USD 1.20 each for Jev, Clef and Clef-flash together, so about USD 11. Laya runs locally.

## Few-shot run

All five models run again on the same 10 test sets. The question is the baseline question plus the three examples that Kastrati et al. (2026) gave the LLMs, one per label. Our models and the LLMs then see the same examples, so we compare the scores directly with the paper's few-shot LLM column.

The paper kept the same three English examples for every dataset and language, and so do we. We copy them word for word from the paper. All three are tweets from `data/tsm/train/english.csv`, at lines 5, 33 and 37, and none is in a test set. The paper's text differs slightly from our train rows: it drops `#cincodemayo` from the positive example and adds a full stop to the neutral one.

Each criterion becomes an object. `description` holds the zero-shot wording word for word, and `examples` holds the paper's example for that label. We add nothing else, such as a `not_for` field. The key is `description` so that it comes before `examples`, since Clef sorts keys alphabetically.

```json
"positive": {
  "description": "The text expresses a positive opinion, emotion or attitude.",
  "examples": ["Not even 20 pages into Paper Towns and the book centers around the night of May 5th. I know its gonna be a good one now!"]
}
```

Our paper must state two more differences. The criteria change from plain strings to objects, so the shape changes as well as the examples. The LLMs saw the examples before the input text, and our models see them inside the criteria.

The nine other versions from the question sensitivity analysis get the same three examples. Each version then has a zero-shot and a few-shot score. The baseline stays the headline score and runs first. The nine others run later. For each version, we report the few-shot 10-language mean and its gain over the zero-shot mean of the same version, with the mean, minimum and maximum across versions. We select no version.

`experiments/few_shot/add_examples.py` writes the 10 few-shot question files to `experiments/few_shot/questions/`. It copies each zero-shot file and changes only the criteria, as above. `experiments/few_shot/paper_scores.csv` holds the paper's few-shot LLM scores.

```bash
uv run python -m experiments.few_shot.add_examples
uv run python -m experiments.zero_shot.classify_sentiment -m jev-1.14.0 -q experiments/few_shot/questions/baseline.json
uv run python -m experiments.zero_shot.score_predictions -r results/few_shot -p experiments/few_shot/paper_scores.csv
```

We estimate that the three examples add about 100 input tokens to each item. Zero-shot used 388 per item with Jev and 207 with Clef and Clef-flash, so few-shot costs about a quarter more with Jev and about half more with Clef. That is about USD 1.70 per version for Jev, Clef and Clef-flash together, or about USD 17 for all 10. Laya runs locally.

## Instruction induction

We wrote the 10 question versions by hand. Here Opus writes the question from labelled English train data instead. We ask two things. Does such a question score better than a hand-written one? Do examples add anything on top?

The method is instruction induction (Honovich et al., 2023): an LLM reads labelled examples and writes a description of the task. Opus reads more examples than in that paper, and it also writes the criteria for each label. We generate 10 questions and select none. The method is therefore not Automatic Prompt Engineer (APE; Zhou et al., 2023), which keeps the question that scores best.

Opus has read labelled train data, so its questions are not zero-shot. We compare them with the zero-shot baseline question and with the few-shot LLMs, not with the zero-shot LLMs.

### Generating the questions

1. Write one prompt for Opus in a session that knows nothing about our results. The prompt describes the task and the output format only, and never mentions the test sets or any score.
2. Make 10 separate calls to `claude-opus-5-5` with this prompt and the default sampling settings, numbered 1 to 10.
3. For call n, draw 50 tweets per label from `data/tsm/train/english.csv` with seed n. The file holds 1,839 tweets, 613 per label.
4. Take each answer as it is: one Choice question with `instructions` and plain-text `criteria` for `positive`, `neutral` and `negative`, in that order.
5. If an answer fails the format check of `load_questions`, repeat that call with the same seed. Do not filter or edit the answers in any other way.

We use 10 calls, not one call that asks for 10 questions, because one call would make the questions differ on purpose. Each call sees its own sample, so the spread across the 10 questions covers both Opus's randomness and the choice of tweets.

### Two versions of each question

- **Induced question:** Opus's question as it is, with no examples.
- **Induced question with examples:** each criterion becomes an object, as in the [few-shot run](#few-shot-run). `description` holds Opus's criterion word for word, and `examples` holds the paper's example for that label. All 10 questions get the same three examples, so the paired difference shows the effect of the examples alone.

This gives 20 question files.

### Run and report

All five models run each of the 20 question files on the same 10 test sets. Every language gets the same English questions. As in the question sensitivity analysis, each test set is scored once per question file, and we select no question.

For each model and question file, we report macro-F1 per language and the 10-language mean. The headline scores are the mean over the 10 induced questions and the mean over the 10 induced questions with examples, each with its minimum and maximum. We compare:

- the induced questions with the baseline question and with the spread of the 10 hand-written versions. This shows whether reading train data helps more than rewording does.
- both versions with the few-shot LLMs of Kastrati et al. (2026).

We commit the Opus prompt, the model ID, the date, the seeds, the row numbers of the sampled tweets, Opus's raw answers and the 20 question files.

The 10 Opus calls send about 150 tweets each, so they cost little. The 10 induced questions cost about USD 12 for Jev, Clef and Clef-flash together, as the hand-written versions do. The 10 with examples cost more, because the three examples add about 100 input tokens to every item. Laya runs locally.

## Open decisions

- **Venue and deadline:** we have not chosen the conference yet.
- **SOTA column:** if the paper shows it, we must first settle what the Albanian SOTA of 72.1 measures. data-and-baselines.md and background.md describe it differently.
