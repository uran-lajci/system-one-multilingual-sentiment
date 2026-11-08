Below are 150 short texts from one dataset. Human annotators labelled each one as positive, neutral or negative, 50 texts per label.

<texts>
{texts}
</texts>

Write a question that a text classification model can use to label new texts from the same dataset. The model reads your question and one text, and then picks the label whose criterion fits the text best. It sees only your question, with no labelled examples.

The question has two parts:

- `instructions`: what the model should judge about the text, in one to three sentences.
- `criteria`: for each label, positive, neutral and negative, a description of the texts that get that label.

Write the question so that a model using it would give each text above the same label as the annotators. In the question:

- State where these annotators draw the line between the labels, above all in cases where another reader might choose differently.
- Give cue words or short phrases that signal each label in these texts, in the language of the texts. If that language is not English, follow each one with its English meaning in brackets.

Write the question itself in English. Do not quote or paraphrase whole texts. Keep the whole question under 250 words.

Return the question as JSON with the fields `instructions` and `criteria`.
