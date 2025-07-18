import spacy


class NERExtractor:
    def __init__(self, model_name="en_core_web_sm"):
        """
        Initializes the extractor by loading a spaCy model.
        """
        self.nlp = spacy.load(model_name)
        # We only care about a few general-purpose entities
        self.relevant_entities = {"PERSON", "GPE", "ORG", "EVENT"}

    def extract_entities(self, text: str) -> list[dict]:
        """
        Processes text to find named entities using spaCy.
        """
        doc = self.nlp(text)
        entities = []
        for ent in doc.ents:
            if ent.label_ in self.relevant_entities:
                entities.append(
                    {"entity": ent.label_, "value": ent.text, "extractor": "spacy"}
                )
        return entities


if __name__ == "__main__":
    extractor = NERExtractor()
    text = "Can we book a meeting with Andrea Aceto in Rome about the Google project for the 2026 Olympic Games?"
    entities = extractor.extract_entities(text)
    print(f"Text: '{text}'")
    print(f"Extracted Entities: {entities}")
