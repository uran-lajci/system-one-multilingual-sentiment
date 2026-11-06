# Next steps

The conference paper runs five System One models zero-shot on 10 languages. Everything else waits until after the conference, in [future-work.md](future-work.md).

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

## Open decisions

- **Venue and deadline:** we have not chosen the conference yet.
- **SOTA column:** if the paper shows it, we must first settle what the Albanian SOTA of 72.1 measures. data-and-baselines.md and background.md describe it differently.
