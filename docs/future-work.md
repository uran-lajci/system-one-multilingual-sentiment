# Future work

- Was the Jev model contaminated by the datasets

## After the conference

The conference paper covers 10 languages, with hand-written zero-shot questions, few-shot with the paper's three examples, and instruction induction. These steps extend the study to all 35 languages and to more few-shot examples. The data for them is ready, except the training data still to download.

### Zero-shot run on all 35 languages

The same five models and the same question run on the other 25 test sets, so the study covers all 35 languages and 52,859 items.

### More few-shot runs

The conference few-shot run ([next-steps.md](next-steps.md#few-shot-run)) uses the paper's three examples on 10 languages. These runs extend it:

- **All 35 languages:** the same question with the paper's three examples on all 52,859 test items.
- **Five train tweets per label:** we draw them at random, with a fixed seed, from `data/tsm/train/english.csv`. The examples stay English and the same for all 35 languages, because some test languages have no training data. Our paper must say that the LLMs saw one example per label and our models see five.
- **Several draws:** we repeat the five-tweet run with 3 to 5 seeds and report the mean, minimum and maximum, as in the question sensitivity analysis. One draw alone does not show how much the score depends on which tweets we pick. We select no seed.
- **Synthetic examples:** Claude writes five examples per label, so none comes from train data. Our paper must say they are synthetic.

The question shape stays as in the conference run: `description` holds the zero-shot wording word for word, and `examples` holds the tweets for that label.

### Fine-tune transformers on our splits

Each SOTA score comes from the dataset's own paper, often on a different split or with a different metric. To get baselines on the same test items, we fine-tune transformer models on our train and validation data. Their scores then replace the SOTA column.

1. Download the missing training data for Azerbaijani, Czech, Danish, Latvian and Roman Urdu.
2. Remove every test item from the new training data.
3. Fine-tune one model per language on its train data.
4. Choose the number of epochs and the learning rate on validation data only.
5. Score each model once on its test set, with macro-F1 on the three labels.

Training data is on disk for 26 languages: the 8 TSM languages, 12 AfriSenti languages, Albanian, Bosnian, Croatian, Macedonian, Serbian and Swedish. No training data exists for Oromo and Tigrinya, because AfriSenti released only validation data for them. None exists for Greek and Norwegian either, because the paper used every item of these datasets as test data.

Open questions for this step:

- **Transformer models:** which models do we fine-tune? XLM-R-base fits our 6 GB GPU, but larger models may need a rented GPU.
- **Oromo and Tigrinya:** with no training data, we could train on the other AfriSenti languages and score them cross-lingually, or leave them out.

## Possible follow-up experiments

Experiments 2 to 6 are options for after the conference, not commitments.

### 2. Prompt ablation

The conference paper now includes this as a sensitivity analysis with 10 versions on the 10 conference languages; see the "Question sensitivity" section of [next-steps.md](next-steps.md). After the conference, it can extend to the other 25 languages.

The five LLMs were tested with one fixed prompt. If we try many versions for Jev, we should report the mean and spread across versions and choose the best version on validation data, never on test data.

### 3. Automatic tuning with Claude Code

The conference paper includes a version for Jev, with Opus as the tuner; see the "Iterative tuning" section of [next-steps.md](next-steps.md).

We build a protocol in which Claude Code tunes the instructions and criteria by itself. It reads the model's errors on validation data, rewrites the question, scores it again and keeps the changes that help, which is what I did by hand for AlbAna. We develop the protocol in English, Albanian and Swedish, which we can judge as human readers, and then apply it unchanged to the other languages.

Only train and validation data are used, and each test set is scored once at the end. Train or validation data are on disk for 28 languages, with test items removed. These are the 8 TSM languages, the 14 AfriSenti languages and six LMR-SMS languages: Albanian, Bosnian, Croatian, Macedonian, Serbian and Swedish. Oromo and Tigrinya have validation data only. Azerbaijani, Czech, Danish, Latvian and Roman Urdu still need downloading, and Greek and Norwegian have none.

A tuned Jev has seen labelled data, so it should be compared with zero-shot Jev and with the few-shot LLMs, not with the zero-shot LLMs.

### 4. More System One models

We add more models, for example one per model family. Several of the popular models come in pairs of the same model (d1 and d1-omni, nimble and nimble-v3), so taking one per family avoids near-duplicates. Each new model means another run over the 52,859 items, so we should only pick models that support Choice questions and many languages.

### 5. Score and Noul instead of Choice

Choice fits our three labels exactly and gives numbers that compare directly with the LLM results, which is why the conference paper uses it. Score treats sentiment as an ordered scale, so its expected level must be mapped back to three labels with two thresholds set on validation data. Noul answers only yes or no, so it needs one question per label, with the most probable label taken as the answer.

### 6. Error analysis on AlbAna

AlbAna keeps all three annotations for every comment, so we can relate model errors to human disagreement. For example, do the models fail mostly on comments where annotators disagree, or also where all three agree? We would compare System One models, LLMs and fine-tuned transformers on the same comments.

We already have per-comment outputs for all three groups. The LLM outputs are in the published data of Kastrati et al. (2026), and the predictions of Jev, mBERT and the 19 other AlbAna models are in our AlbAna results. The LLM outputs cover the 2,148-comment sample, but the transformers were trained on part of it: only about 30% of those comments are in the AlbAna test split. We can analyse that overlap, or re-train the transformers on AlbAna without the 2,148 sample.
