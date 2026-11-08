Below are 150 short texts. Human annotators labelled each one as positive, neutral or negative, 50 texts per label.

<texts>
{texts}
</texts>

Write a question that a text classification model can use to label new texts like these. The model reads your question and one text, and then picks the label whose criterion fits the text best. It sees only your question, with no labelled examples. The new texts may be in English or in other languages.

The question has two parts:

- `instructions`: what the model should judge about the text, in one to three sentences.
- `criteria`: for each label, positive, neutral and negative, a description of the texts that get that label.

Write the question so that a model using it would give each text above the same label as the annotators. Write in English. Do not quote or paraphrase any of the texts. Keep the whole question under 200 words.

Return the question as JSON with the fields `instructions` and `criteria`.
