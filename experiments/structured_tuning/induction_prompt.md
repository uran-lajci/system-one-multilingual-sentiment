Below are 150 short texts from one dataset. Human annotators labelled each one as positive, neutral or negative, 50 texts per label. This is how the dataset describes its texts:

<context>
{context}
</context>

<texts>
{texts}
</texts>

Write a question that a text classification model can use to label new texts from the same dataset. The model gets the description above and one text. It reads your question, and then picks the label whose criterion fits the text best. It sees only your question, with no other labelled examples. It gets the labels in a different order each time, so do not refer to their order.

The question has these fields:

- `question`: what the model should judge about the text, in one sentence.
- `rule`: where these annotators draw the line between the labels, above all in cases where another reader might choose differently, in one to four sentences.
- `criteria`: one object for each label, positive, neutral and negative, with these fields:
  - `what`: a description of the texts that get the label.
  - `examples`: one to four short texts from above that show the label clearly or show where its boundary lies. Copy each one word for word. If a text is not in English, follow it with its English meaning in brackets.
  - `cues`: words and short phrases that signal the label in these texts, in the language of the texts. If that language is not English, follow each one with its English meaning in brackets.
  - `not_for`: texts that look like they get this label but get another one, and which label they get.

Write the question so that a model using it would give each text above the same label as the annotators, and so that it also works for new texts from the same dataset. Write the question itself in English, apart from the examples and cues. Keep the whole question, examples included, under 400 words.

Return the question as JSON with the fields `question`, `rule` and `criteria`.
