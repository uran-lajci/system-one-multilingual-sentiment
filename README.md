# system-one-multilingual-sentiment
Benchmark of five System One (decision) models: Jev, Clef, Clef-flash, Laya and Laya-multilingual, on three-class sentiment analysis, compared with five LLMs from Kastrati et al. (2026). The conference paper runs them zero-shot on 10 European languages. After the conference, the study extends to all 35 languages and to few-shot; the data for that is already prepared.

## Setup

```
uv sync
cp .env.example .env    # then fill in the API keys
uv run python -m data_prep.select_paper_test_sets    # after the datasets are in data/
uv run python -m data_prep.import_mozetic
uv run python -m data_prep.split_train_validation
uv run python -m data_prep.remove_test_leaks
```

## Repository layout

```
data/
  actual_dataset_resources.md   links to the original datasets
  afrisenti/                    train/ validation/ test/
  lmr-sms/                      train/ validation/ test/
  tsm/                          train/ validation/ test/
  raw/lmr-sms/                  sources the data_prep scripts build lmr-sms/ from:
                                mozetic/ paper_samples/ full/ excluded/ train_validation/
docs/                           study plan and working notes
papers/                         Kastrati et al. (2026)
```

## Data

The 35 test sets hold 52,859 items: every file in `data/tsm/test/` (6,960) and `data/lmr-sms/test/` (22,246), plus every file in `data/afrisenti/test/` (23,653). Malaysian is left out of the study; its file is in `data/raw/lmr-sms/excluded/`. The conference paper uses 10 of the 35 test sets (15,864 items), listed in `docs/next-steps.md`.

For Hausa, Igbo, Nigerian Pidgin, Mozambican Portuguese and Yoruba, the test file is the paper's stratified 50% subsample of the Hugging Face test set, named with its size, such as `hau_ts2652.csv`. For Bosnian, Croatian and Serbian, it is the paper's 20% sample, picked from the whole dataset in `data/raw/lmr-sms/full/`.

Train and validation data are on disk for 26 languages, with test items removed: the 8 TSM languages, 12 AfriSenti languages, and Albanian, Bosnian, Croatian, Macedonian, Serbian and Swedish. Oromo and Tigrinya have validation data only. We do not have train and validation data for Azerbaijani, Czech, Danish, Latvian and Roman Urdu; they can be downloaded after the conference. Greek and Norwegian have none, because the paper used every item as test data.

Column names and label formats differ between files. In `data_prep/files.py`, `text_column` finds each file's text, and `sentiment_labels` maps its labels to positive, neutral and negative.
