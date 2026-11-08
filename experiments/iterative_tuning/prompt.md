You will improve a question for a text classification model. The model reads the question and one text, and then picks the label whose criterion fits the text best. It sees only the question, with no labelled examples. The texts come from one dataset, and human annotators labelled each one as positive, neutral or negative.

This is version 0 of the question:

{question}

After each version, you get its results on a labelled validation set: the macro-F1 on the three labels, the confusion matrix, and every text the model labelled wrong. Each wrong text comes with the annotators' label, the model's label and the model's probability for each label.

At each turn:

1. In `analysis`, study the errors. Find the patterns behind them, and decide what to change so the model fixes them without breaking the texts it already labels right.
2. Write the next version of the question in `instructions` and `criteria`.

The question has two parts:

- `instructions`: what the model should judge about the text, in one to three sentences.
- `criteria`: for each label, positive, neutral and negative, a description of the texts that get that label.

Rules for the question:

- Write it in English.
- Keep the whole question under 300 words.
- Do not quote or paraphrase whole texts. Cue words and short phrases are fine.
- Write for new texts from the same dataset, not only for these validation texts.

You will write 10 new versions in total. At each turn, return JSON with the fields `analysis`, `instructions` and `criteria`.

{feedback}
