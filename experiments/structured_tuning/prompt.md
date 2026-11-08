You will improve a question for a text classification model. The model gets the description of the dataset below and one text. It reads the question, and then picks the label whose criterion fits the text best. It sees only the question, with no other labelled examples. It gets the labels in a different order each time. Human annotators labelled each text of the dataset as positive, neutral or negative. This is how the dataset describes its texts:

<context>
{context}
</context>

This is version 0 of the question:

{question}

The question has these fields:

- `question`: what the model should judge about the text, in one sentence.
- `rule`: where these annotators draw the line between the labels, above all in cases where another reader might choose differently, in one to four sentences.
- `criteria`: one object for each label, positive, neutral and negative, with these fields:
  - `what`: a description of the texts that get the label.
  - `examples`: one to four short texts that show the label clearly or show where its boundary lies.
  - `cues`: words and short phrases that signal the label, in the language of the texts.
  - `not_for`: texts that look like they get this label but get another one, and which label they get.

After each version, you get its results on a labelled development set, drawn at random from the dataset: the macro-F1 on the three labels, the confusion matrix, and every text the model labelled wrong. Each wrong text comes with the annotators' label, the model's label and the model's probability for each label.

At each turn:

1. In `analysis`, study the errors. Find the patterns behind them, and decide what to change so the model fixes them without breaking the texts it already labels right.
2. Write the next version of the question in `question`, `rule` and `criteria`.

Rules for the question:

- Write it in English, apart from the examples and cues.
- Copy each example word for word from a text you have seen. If the texts are not in English, follow each example and each cue with its English meaning in brackets.
- Do not refer to the order of the labels.
- Keep the whole question, examples included, under 400 words, not counting the English meanings in brackets.
- Write for new texts from the same dataset, not only for these development texts.

You will write 10 new versions in total. At each turn, return JSON with the fields `analysis`, `question`, `rule` and `criteria`.

{feedback}
