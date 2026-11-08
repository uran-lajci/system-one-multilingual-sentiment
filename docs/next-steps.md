# Next steps

The conference paper runs five System One models on 10 languages. It tests hand-written zero-shot questions, few-shot with the paper's three examples, and questions that Opus writes from train data. Opus writes one set from English train data for every language, and one set per dataset from that dataset's own train data. Opus then tunes the per-dataset questions for Jev on validation data, and writes structured per-dataset questions that come with a description of the dataset. Opus also tunes the structured Albanian questions on train and validation data. Everything else waits until after the conference, in [future-work.md](future-work.md).

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

## Per-dataset instruction induction

Instruction induction gives every language the same questions, written from English train data. These questions cannot know each dataset's own labelling rules. In AlbAna, for example, neutral covers more than "no feeling". Calm criticism is neutral, and open mockery or distrust is negative. Banter that ranks towns by case counts is also neutral. A generic question would call calm criticism negative.

Here Opus writes the questions for each dataset from that dataset's own train data. This runs after [instruction induction](#instruction-induction) and follows its method, with these changes:

- **Train data:** for each dataset, call n draws 50 texts per label from that dataset's train file with seed n. 8 of the 10 languages have train data, with at least 1,070 texts per label: `tsm/train/` English, German and French, and `lmr-sms/train/` Albanian, Bosnian, Croatian, Serbian and Swedish.
- **Boundary rules:** the prompt also asks Opus to state where the annotators draw the line between labels, as the AlbAna rules above do.
- **Cue words:** the prompt asks for cue words in the text's language, each with its English meaning. In Albanian these could be `rrena` (lies), `urime` (congratulations) and `ma gjall` (cheering a town). The rest of the question stays in English.
- **Norwegian and Danish:** they have no train data, so they get questions written for another dataset. See [Open decisions](#open-decisions).
- **No version with examples:** we skip the version with the paper's three examples. The cue words already give examples in the text's language.

This gives 80 question files, 10 for each of the 8 datasets.

### Run and report

All five models run each dataset's 10 questions on that dataset's test set. As before, each test set is scored once per question file, and we select no question.

For each model, the 10 languages' questions from call n form one set. We report macro-F1 per language and the 10-language mean of each set, with the mean, minimum and maximum across the 10 sets. We compare them with the English-induced questions, with the baseline question and with the few-shot LLMs of Kastrati et al. (2026).

Our models then get information about each dataset's labelling that the LLMs never had. Our paper must say so.

We commit the same files as for instruction induction: the Opus prompt, the model ID, the date, the seeds, the row numbers of the sampled texts, Opus's raw answers and the 80 question files.

The 80 Opus calls cost about USD 10. Each test set again gets 10 questions, so scoring costs about USD 12 for Jev, Clef and Clef-flash together. Cue words make the questions longer, so the real cost may be higher. Laya runs locally.

## Iterative tuning

The induced questions come from one pass over train data, and Opus never sees how Jev answers them. Here Opus also reads Jev's errors on validation data and rewrites the question, up to 10 times. Only then do we score the test set, once.

We start with English. We decide on the other 7 languages with validation data after we see the English result. Norwegian and Danish have no validation data, so they cannot be tuned.

### The loop

Each run is one conversation with `claude-opus-5-5`, with effort `medium`. The conversation sees train and validation data only, and never a test set or a test score. Run r starts from the per-dataset question `english_0r.json`, which Opus wrote from train data with seed r.

1. Score the current question with `jev-1.14.0` on `data/tsm/validation/english.csv` (324 items).
2. Send Opus the macro-F1, the confusion matrix and every misclassified text, with its gold label, Jev's label and Jev's three probabilities.
3. Opus writes an error analysis, then a new question.
4. Repeat from step 1 until Opus has written 10 new questions.

Every run makes all 10 rewrites, so the 5 runs stay comparable. The new questions keep the format: one Choice question with plain-text criteria for positive, neutral and negative. Each stays under 300 words and quotes no whole text. If a question fails the format check of `load_questions`, Opus gets the error and writes it again.

### Selection and test

A run scores 11 questions on validation: the start question and the 10 rewrites. We keep the one with the highest validation macro-F1, and on a tie, the earlier one. Jev then scores that question once on the English test set.

We do 5 runs, starting from `english_01` to `english_05`. We report each run's validation curve, the validation and test score of each kept question, and the mean, minimum and maximum test score over the 5 runs.

Opus reads the validation errors, and we select on the same 324 items. The validation score of a kept question is therefore optimistic, and only the test score counts. Our paper must say that the tuning used validation data for both.

Only Jev is tuned. A tuned Jev has seen labelled data, so we compare it with zero-shot Jev and with the few-shot LLMs of Kastrati et al. (2026), not with the zero-shot LLMs.

### Logs and cost

We commit the prompt, the model ID, the date, every message of each conversation and every question with its validation score. TSM is public, so the English logs may hold validation texts. For datasets we may not share, the logs hold row numbers instead of texts.

A run scores 11 questions on 324 validation items with Jev, which costs about USD 0.15. Opus reads a longer conversation at each turn, so a run costs about USD 1.50 for Opus. The 5 runs cost about USD 8, and the 5 test scorings cost about USD 0.15.

## Structured per-dataset induction

So far every question has plain-text `instructions`, and criteria that are plain text or text with a list of examples. Our AlbAna work used a richer input, and it scored well there. Here Opus writes per-dataset questions in that richer shape. We start with English and Jev.

### The input

- **State:** a JSON object with `context` and `text`. `context` describes the dataset in one to three sentences: its source, its time and its language. We write it from the dataset's paper, not from labelled data, so it is the same for every seed. The contexts are in `experiments/structured_induction/contexts.json`.
- **Instructions:** a JSON object with `question` and `rule`. `rule` says where the annotators draw the line between the labels.
- **Criteria:** one JSON object per label with `what`, `examples`, `cues` and `not_for`.
  - `what` describes the texts that get the label.
  - `examples` holds 1 to 4 short texts that Opus copies from the 150 train texts it sees. A text that is not in English gets its English meaning in brackets.
  - `cues` lists words and short phrases that signal the label, with their English meaning if they are not in English.
  - `not_for` says what looks like the label but belongs to another one.
- **Option orders:** Jev gets the same question three times in one request, with the labels in three orders: neutral, positive, negative; positive, negative, neutral; and negative, neutral, positive. We average the three probabilities of each label and take the most probable label, because Jev leans toward the label listed first.

### Generating the questions

The method follows [per-dataset induction](#per-dataset-instruction-induction). Opus makes 10 calls, and call n draws 50 texts per label from the train file with seed n. For English, the calls therefore see the same tweets as `english_01` to `english_10`.

The prompt gives Opus the context and describes the fields above. It shows no question from our AlbAna work, so no rule tuned by hand on AlbAna reaches other datasets. Each question stays under 400 words. Opus returns the fields as JSON, and the script builds the three orders.

### Run and report

Jev scores each of the 10 questions once on the English test set. For each question, we report macro-F1 twice: with the three orders averaged, and with the first order alone. The first-order score comes from the same responses, so it costs nothing extra. It shows what the averaging adds. The other changes come together, so this run cannot tell which of them helps.

We report the mean, minimum and maximum over the 10 questions. We compare them with per-dataset induction on the same seeds, with zero-shot Jev and with the few-shot LLMs.

The examples are train texts, so these questions are few-shot. Our paper must say that Jev saw up to 12 train texts, while the LLMs saw 3.

Only Jev runs. Clef and Laya may not accept JSON instructions, JSON criteria or three questions in one request. We add them only after we check that they do.

We commit the prompt, the contexts, the model ID, the date, the seeds, the row numbers, Opus's raw answers and the question files.

### Cost

The 10 Opus calls cost about USD 0.60. Three orders of a question of up to 400 words need about 2,000 input tokens per item, so Jev on the 8,700 English test items costs about USD 0.80.

## Iterative tuning of structured questions on Albanian

On English, [iterative tuning](#iterative-tuning) raised the validation score but not the test score. Opus read the errors on the same 324 items that we selected on, so it fitted those items. Here we tune the structured Albanian questions, and we keep the selection data away from Opus.

### The loop

Run r starts from the structured question `albanian_0r.json`, for r from 1 to 5. Each run is one conversation with `claude-opus-5-5`, with effort `medium`.

1. Draw a development set of 600 comments from `data/lmr-sms/train/Albanian.csv` with seed r, leaving out the 150 comments that Opus saw when it wrote `albanian_0r`. The draw is simple random sampling, so the labels keep their train proportions, which are mostly neutral.
2. Score the current version with `jev-1.14.0` on the development set and on the 1,705 comments of `data/lmr-sms/validation/Albanian.csv`.
3. Send Opus the development results only: the macro-F1, the confusion matrix and every misclassified comment, with its gold label, Jev's label and Jev's three probabilities. Opus never sees a validation comment or a validation score.
4. Opus writes an error analysis, then a new version in the structured format.
5. Repeat from step 2 until Opus has written 10 new versions.

While tuning, Jev gets only the first label order, with neutral first, which costs a third as much. The new versions follow the rules of structured induction. They stay under 400 words, not counting the English meanings in brackets. They take their examples word for word from comments Opus has seen.

### Selection and test

We keep the version with the highest validation macro-F1, and on a tie, the earlier one. Jev scores that version once on the 2,148 Albanian test comments, with the three label orders averaged.

We report each run's development and validation curves, and the mean, minimum and maximum test score over the 5 runs. We compare them with structured induction on the same seeds, with zero-shot Jev and with the few-shot LLMs.

The development set comes from train data and validation stays unseen, so the validation score of a kept question is a fair estimate, apart from the selection among 11 versions.

### Logs and cost

The code and outputs are in `experiments/structured_tuning/` and `results/structured_tuning/`. We commit the prompts, every message of each conversation, every version and the train row numbers of each development set. AlbAna is public, so the logs may hold its comments.

A run scores 11 versions on 2,305 comments with one label order, about 1,100 input tokens per comment. That costs about USD 1.30 for Jev and about USD 1.50 for Opus. The 5 runs cost about USD 14, and the test scoring about USD 1.50.

### English

We run the same loop on English, starting from the structured questions `english_01` to `english_05`. Each development set holds 600 of the 1,689 tweets in `data/tsm/train/english.csv` that Opus did not see for that seed. We select on the 324 tweets of `data/tsm/validation/english.csv`, which Opus never sees. That set is about 5 times smaller than the Albanian one, so picking the best of 11 versions on it is noisier. The 5 runs and the test scoring cost about USD 9.

## Open decisions

- **Venue and deadline:** we have not chosen the conference yet.
- **SOTA column:** if the paper shows it, we must first settle what the Albanian SOTA of 72.1 measures. data-and-baselines.md and background.md describe it differently.
- **Norwegian and Danish in per-dataset induction:** they have no train data. They could get the English questions, or the Swedish ones, since Swedish is close to both.
