# Background

## How the study started

Jev reached a weighted F1 of 75.7 on the 3,223 test comments of the AlbAna dataset, with no training on it. The best model from the AlbAna paper (Kastrati et al., 2021), mBERT, reaches 72.1 when re-trained on the same split, averaged over five seeds. A paired bootstrap puts Jev's lead at 3.6 points, with a 95% interval of 2.0 to 5.2.

Jev's weights never saw a comment from the dataset. I only tuned the wording of the question, using the 2,256 validation comments, and scored the test split once at the end. Pairs of human annotators agree with each other at a weighted F1 of 74.6 to 79.6 on the same comments, so Jev falls inside that range.

This result raised the question behind the project: how well do System One models handle sentiment analysis across many languages, without training? The code and full report for the AlbAna run are [here](https://lnkd.in/dU97NMkP).

## What System One models are

System One models, also called decision models, answer typed questions about an input instead of generating text. The name refers to the fast, intuitive "System 1" thinking described by Kahneman. Given a text and a question with fixed answers, the model returns a probability for each answer in a single forward pass.

Compared with LLMs, this gives them three practical advantages:

- **Lower cost:** Jev 1.13 charges USD 0.042 per million input tokens, and there is no generated output to pay for. Labelling all 10,742 AlbAna comments cost about USD 1.20.
- **Faster inference:** nothing is generated, so all questions about a text are answered at once. The full AlbAna dataset took about four minutes.
- **No training for general tasks:** every user gets the same weights, and a task is defined only by how the question is worded.

For text, a question has one of three types:

- **Noul:** a yes/no question. It returns the probability of "yes".
- **Choice:** picks one label from a fixed set, such as positive, neutral or negative. It returns the chosen label and a probability for each label.
- **Score:** places the text on an ordered scale, such as from very negative to very positive. It returns the expected level.

Jev also has a fourth type, Box, which locates objects in images and does not apply here.

A Choice question has two parts we can change: the **instructions**, which ask the question, and the **criteria**, which describe each label. Adapting a System One model to a task means rewriting these two parts, and that is all I did for AlbAna.

## Models

The conference paper uses five System One models. [Jev](https://typesafe.ai/) was the first to be published. [Clef](https://huggingface.co/Cloudflare/clef) and [Clef-flash](https://huggingface.co/Cloudflare/clef-flash) are open-weight models from Cloudflare, a large one and a smaller, faster one. [Laya](https://huggingface.co/convaiinnovations/laya) and [Laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual) are small open-weight models, one for English and one for 100+ languages.

| Model | Maker | Access | Version | Question types |
|---|---|---|---|---|
| Jev | TypeSafe AI | Commercial API | jev-1.14.0, pinned so results stay reproducible | Noul, Choice, Score, Box |
| Clef | Cloudflare | Open weights, Apache 2.0; we call it through Cloudflare Workers AI | revision `cfddda0` on Hugging Face; 27B parameters, fine-tuned from Qwen3.8-27B | Noul, Choice, Score |
| Clef-flash | Cloudflare | Open weights, Apache 2.0; we call it through Cloudflare Workers AI | revision `fb4417d` on Hugging Face; 9B parameters, fine-tuned from Qwen3.5-9B | Noul, Choice, Score |
| Laya | Convai Innovations | Open weights, Apache 2.0 | laya 0.4.22, 421M parameters, ModernBERT-large | Noul, Choice, Score |
| Laya-multilingual | Convai Innovations | Open weights, Apache 2.0 | laya 0.4.22, 322M parameters, mmBERT-base, 100+ languages | Noul, Choice, Score |

Cloudflare Workers AI has no dated snapshots of Clef, so its models may change without a new name. The table names the Hugging Face revisions that were current when we ran: Clef `cfddda043dd190ef3b01cff449d5ee8cff1e8ec6` and Clef-flash `fb4417d31c1d0f9e7e77f1141b40aaede7491e00`, both from 30 October 2026. With every prediction, we also save the response's `model` field, its `api-version` header (`2026-10-01.epoch` on 6 November 2026) and the date. If the header changes during a run, the model may have changed.

Many other System One models exist, and Experiment 4 could add some of them. The Ollama ["decision" category](https://ollama.com/search?c=decision) lists d3, tev1, nimble, clef, d1, clef-flash, nimble-v3, d1-omni, pplx-decider, kev, laya and strands-decider. The most downloaded on 27 October 2026 were tev1 (121k), nimble (62k), clef (47k) and clef-flash (42k). The curated [Awesome System One Models](https://github.com/andyrewlee/awesome-system-one) list also includes models that are not on Ollama.
