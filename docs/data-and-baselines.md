# Data and baselines

We use 35 of the 36 test sets from [Kastrati et al. (2026)](https://doi.org/10.3389/frai.2026.1854873), "Do Language Families Matter? Evaluating LLMs for Sentiment Analysis through a Hierarchical Cross-Lingual Lens". That paper ran five LLMs on these sets, zero-shot and few-shot, and reports the best task-specific (SOTA) score for each language. Using the same test items lets us compare against all of these without re-running the LLMs.

| Collection | Languages | Test items | Source |
|---|---:|---:|---|
| TSM (Tweet Sentiment Multilingual) | 8 | 6,960 | Barbieri et al. (2022); 870 tweets per language |
| LMR-SMS | 13 | 22,246 | 13 low- and medium-resource datasets; Albanian and Czech are Facebook comments, the rest are tweets |
| AfriSenti | 14 | 23,653 | Muhammad et al. (2023), SemEval-2023 Task 12 |
| **Total** | **35** | **52,859** | |

We leave out Malaysian. Our file holds 626 items, but the paper's Table 1 says it scored about 1.4k, so we cannot score the same items.

The authors' files hold the whole Bosnian, Croatian and Serbian datasets, but the paper scored 20% samples. Zenun Kastrati later sent these samples, and our test files hold exactly them (782, 2,790 and 2,272 items).

In the Azerbaijani and Czech test files, many letters appear as `?`, for example `mahn?s?` for *mahnısı* and `n?kdo` for *někdo*. The authors' own files have the same text, so the LLMs most likely saw it too. We keep the text as it is, so all models get the same input, and our paper should mention it.

Every item has one of three labels: positive, neutral or negative. The metric is macro-F1, the unweighted mean of the per-class F1 scores. The five LLMs are gpt-4o-2024-08-06, gemini-2.0-flash, deepseek-chat (DeepSeek-V3), mistral-large-2411 and claude-3-7-sonnet-20250219, all prompted with one shared template.

The SOTA column is only a loose reference. Each SOTA score comes from the dataset's own paper, often on a different split or with a different metric. The Albanian SOTA of 72.1, for example, is the weighted F1 of the BiLSTM model in the AlbAna paper, measured on its validation split.

Kastrati et al. (2026) swap two language names. Its Table 1 calls the AfriSenti `ary` data (2,962 test tweets) Algerian and the `arq` data (959) Moroccan. ISO 639-3 and AfriSenti use the reverse, and we follow them: `arq` is Algerian Arabic and `ary` is Moroccan Arabic. So the paper's numbers for "Algerian" belong to our Moroccan Arabic, and the reverse.

Table 1 also lists one item more than the source for each AfriSenti test file without `_ts` in its name, such as 2,000 for Amharic. Our nine files match the Hugging Face test splits exactly, in size and in label counts, so the paper probably counted the header line.

## Scores from Kastrati et al. (2026)

Macro-F1 (%) on the three labels, from the paper's Tables 4 to 6. **ZS** is zero-shot and **FS** is few-shot. **Best few-shot** is the highest of the five FS scores. **SOTA** is the best task-specific model the paper reports; "–" means none, and for Roman Urdu the paper gives a range. The mean rows are unweighted means over our 35 languages, which differ from means over the paper's 36, and over the 8 languages of the conference paper.

| Family | Language | GPT-4o ZS | Gemini ZS | DeepSeek ZS | Mistral ZS | Claude ZS | GPT-4o FS | Gemini FS | DeepSeek FS | Mistral FS | Claude FS | Best few-shot | SOTA |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Indo-European | Albanian | 69.8 | 53.4 | 54.0 | 50.3 | 64.8 | 70.2 | 70.0 | 63.6 | 53.8 | 65.4 | 70.2 | 72.1 |
| Indo-European | Bosnian | 58.3 | 54.6 | 55.6 | 43.8 | 59.2 | 61.7 | 61.2 | 62.2 | 61.3 | 64.4 | 64.4 | 60.6 |
| Indo-European | Croatian | 50.5 | 55.1 | 56.3 | 37.6 | 53.5 | 56.6 | 53.3 | 59.4 | 63.5 | 61.9 | 63.5 | 60.6 |
| Indo-European | Czech | 80.0 | 67.3 | 55.3 | 63.9 | 69.9 | 76.4 | 75.7 | 66.4 | 63.9 | 67.5 | 76.4 | 69.0 |
| Indo-European | Danish | 68.7 | 66.3 | 69.0 | 58.7 | 72.1 | 70.5 | 68.2 | 71.1 | 70.8 | 72.7 | 72.7 | 63.7 |
| Indo-European | English | 70.1 | 65.1 | 71.9 | 62.5 | 73.3 | 70.8 | 66.4 | 69.7 | 68.4 | 72.4 | 72.4 | 66.9 |
| Indo-European | French | 55.8 | 64.9 | 58.2 | 51.7 | 52.6 | 65.1 | 63.2 | 48.7 | 66.3 | 63.0 | 66.3 | 68.2 |
| Indo-European | German | 71.0 | 61.4 | 70.8 | 60.9 | 75.6 | 74.8 | 68.6 | 75.1 | 76.0 | 77.2 | 77.2 | 76.1 |
| Indo-European | Greek | 82.9 | 84.7 | 83.0 | 81.2 | 82.1 | 86.1 | 86.0 | 85.1 | 89.3 | 88.3 | 89.3 | 80.6 |
| Indo-European | Hindi | 66.9 | 65.6 | 62.8 | 54.0 | 65.8 | 67.4 | 68.4 | 65.1 | 64.3 | 65.4 | 68.4 | 40.3 |
| Indo-European | Italian | 79.5 | 75.9 | 71.1 | 63.9 | 79.4 | 79.9 | 80.2 | 77.3 | 80.5 | 79.9 | 80.5 | 70.9 |
| Indo-European | Latvian | 71.1 | 68.0 | 64.2 | 47.9 | 67.7 | 72.8 | 73.2 | 69.9 | 67.7 | 70.7 | 73.2 | 61.2 |
| Indo-European | Mozambican Portuguese | 67.5 | 43.0 | 29.4 | 58.6 | 52.8 | 72.5 | 52.2 | 65.5 | 59.5 | 50.1 | 72.5 | 75.0 |
| Indo-European | Macedonian | 63.7 | 66.0 | 63.1 | 43.2 | 65.8 | 65.3 | 68.6 | 71.5 | 68.8 | 70.6 | 71.5 | 63.0 |
| Indo-European | Norwegian | 76.8 | 61.6 | 57.1 | 64.8 | 72.5 | 74.4 | 70.1 | 71.4 | 69.8 | 69.9 | 74.4 | 71.0 |
| Indo-European | Portuguese | 79.7 | 67.2 | 73.8 | 68.5 | 74.1 | 76.8 | 80.5 | 74.2 | 68.1 | 73.5 | 80.5 | 76.0 |
| Indo-European | Roman Urdu | 64.9 | 61.4 | 54.4 | 48.2 | 59.6 | 65.7 | 63.3 | 61.8 | 58.5 | 62.7 | 65.7 | 68–80 |
| Indo-European | Serbian | 58.1 | 50.1 | 47.6 | 45.9 | 57.1 | 59.1 | 56.3 | 56.5 | 51.8 | 54.5 | 59.1 | 60.6 |
| Indo-European | Spanish | 73.7 | 61.1 | 70.3 | 63.8 | 68.0 | 71.9 | 70.5 | 66.8 | 64.2 | 65.2 | 71.9 | 68.5 |
| Indo-European | Swedish | 78.7 | 72.9 | 69.1 | 66.4 | 76.7 | 79.6 | 76.1 | 76.6 | 78.5 | 75.5 | 79.6 | 47.0 |
| Afro-Asiatic | Algerian Arabic* | 65.6 | 74.1 | 64.3 | 44.0 | 63.7 | 69.2 | 71.4 | 66.5 | 67.0 | 70.4 | 71.4 | 74.2 |
| Afro-Asiatic | Amharic | 74.7 | 76.1 | 75.2 | 56.7 | 75.5 | 76.4 | 78.7 | 77.4 | 71.1 | 79.3 | 79.3 | 78.4 |
| Afro-Asiatic | Arabic | 71.0 | 72.7 | 67.9 | 52.1 | 67.2 | 70.2 | 73.4 | 70.4 | 71.4 | 75.1 | 75.1 | 67.7 |
| Afro-Asiatic | Hausa | 63.7 | 49.5 | 50.2 | 33.2 | 52.5 | 72.3 | 72.6 | 65.0 | 57.7 | 67.9 | 72.6 | 82.6 |
| Afro-Asiatic | Moroccan Arabic* | 58.6 | 54.8 | 46.3 | 30.9 | 61.8 | 65.8 | 66.5 | 55.6 | 48.1 | 66.0 | 66.5 | 64.8 |
| Afro-Asiatic | Oromo | 44.1 | 35.3 | 33.1 | 36.3 | 43.3 | 45.8 | 41.6 | 44.4 | 38.0 | 38.6 | 45.8 | – |
| Afro-Asiatic | Tigrinya | 61.4 | 64.5 | 57.9 | 35.3 | 67.5 | 63.2 | 72.5 | 62.6 | 50.0 | 71.9 | 72.5 | – |
| Niger-Congo | Igbo | 64.9 | 50.4 | 51.8 | 38.9 | 51.7 | 71.4 | 63.5 | 60.9 | 59.0 | 63.1 | 71.4 | 83.0 |
| Niger-Congo | Kinyarwanda | 67.7 | 65.6 | 50.6 | 40.5 | 60.7 | 70.8 | 70.2 | 59.4 | 52.7 | 63.8 | 70.8 | 72.6 |
| Niger-Congo | Swahili | 62.0 | 48.3 | 42.8 | 43.5 | 59.2 | 61.6 | 58.3 | 53.3 | 48.4 | 53.2 | 61.6 | 65.7 |
| Niger-Congo | Twi | 46.2 | 44.3 | 43.5 | 26.4 | 39.4 | 51.9 | 52.9 | 38.3 | 49.8 | 60.8 | 60.8 | 68.3 |
| Niger-Congo | Xitsonga | 33.8 | 40.3 | 45.0 | 23.1 | 35.1 | 46.6 | 55.5 | 42.9 | 50.5 | 54.4 | 55.5 | 60.7 |
| Niger-Congo | Yoruba | 60.4 | 61.2 | 53.4 | 27.9 | 50.4 | 73.1 | 74.7 | 60.9 | 60.5 | 78.6 | 78.6 | 80.2 |
| Creole | Nigerian Pidgin | 63.4 | 67.2 | 63.5 | 50.6 | 67.2 | 69.7 | 73.9 | 69.7 | 69.5 | 74.4 | 74.4 | 76.0 |
| Turkic | Azerbaijani | 41.1 | 37.5 | 37.1 | 32.7 | 38.3 | 42.0 | 39.0 | 37.3 | 37.6 | 43.3 | 43.3 | – |
| **All 35** | **Mean** | **64.8** | **60.2** | **57.7** | **48.8** | **62.2** | **67.6** | **66.8** | **63.5** | **62.2** | **66.6** |  |  |
| **Conference 10** | **Mean** | **65.8** | **60.5** | **61.0** | **54.3** | **65.7** | **68.3** | **65.3** | **65.4** | **66.0** | **67.7** |  |  |

\*Named by ISO 639-3, not by the paper. See the note on swapped names above.
