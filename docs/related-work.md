# Related studies

## System One models

- Deußer, Sparrenberg and Sifa (2026). [Evaluating and Benchmarking the System One Model Jev](https://arxiv.org/abs/2609.37647). arXiv:2609.37647. Tests jev-1.13.0 zero-shot on 37 datasets, including Belebele across 122 languages (86.7% accuracy). Jev beats Qwen3.8-27B on 27 of 37 datasets, and all models tested do worse on low-resource languages.
- Zhang and Yu (2026). [Emo-Jev: Probabilistic Reasoning for Emotion Classification with Jev](https://arxiv.org/abs/2610.08829). arXiv:2610.08829. Eight datasets on sentiment, emotion, sarcasm and humor. Plain Jev averages 62.93 macro-F1 against 67.28 for the strongest LLM, with lower latency and generally lower cost.
- Zhang et al. (2026). [Decide, Don't Generate: Competitive Dimensional ABSA with Jev's Typed Decisions](https://arxiv.org/abs/2609.35293). arXiv:2609.35293. Splits SemEval-2026 Task III Track A into Jev decisions, with no text generation and no fine-tuning. It reaches the lowest valence–arousal error of any participating system, over ten corpora in six languages.

## Data and baselines

- Kastrati M., Manaf, Imran, Kastrati Z., Daudpota and Biba (2026). [Do Language Families Matter? Evaluating LLMs for Sentiment Analysis through a Hierarchical Cross-Lingual Lens](https://doi.org/10.3389/frai.2026.1854873). Frontiers in Artificial Intelligence 9:1854873. The source of our 35 test sets, the LLM results and the SOTA column.
- Kastrati Z., Ahmedi, Kurti, Kadriu, Murtezaj and Gashi (2021). [A Deep Learning Sentiment Analyser for Social Media Comments in Low-Resource Languages](https://doi.org/10.3390/electronics10101133). Electronics 10(10):1133. The AlbAna paper; the data and code are at [lule-ahmedi/AlbAna](https://github.com/lule-ahmedi/AlbAna).
- Kadriu, Murtezaj, Gashi, Ahmedi, Kurti and Kastrati Z. (2022). [Human-Annotated Dataset for Social Media Sentiment Analysis for Albanian Language](https://doi.org/10.1016/j.dib.2022.108436). Data in Brief 43:108436. The anonymized 2022 release of AlbAna.
- Barbieri et al. (2022), [Tweet Sentiment Multilingual](https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_multilingual), and Muhammad et al. (2023), [AfriSenti](https://huggingface.co/datasets/shmuhammad/AfriSenti-twitter-sentiment). Two of the three collections behind our test sets.
