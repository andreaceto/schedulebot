import json
import torch
import os
from transformers import AutoTokenizer, AutoConfig
from dotenv import load_dotenv

# Import NLU components
from src.schedulebot.nlu.multitask_model import MultitaskModel
from src.schedulebot.nlu.ner_extractor import NERExtractor
from src.schedulebot.nlu.slot_filler import SlotFiller


class NLUProcessor:
    """
    Orchestrates the multitask model, spaCy, and Duckling to produce a
    single, structured NLU output.
    """

    def __init__(self, multitask_model_repo: str):
        """
        Initializes all components of the NLU pipeline.
        """
        print("\nInitializing NLU Processor...\n")
        # Load the tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(multitask_model_repo)
        # Load the multitask model
        self.multitask_model = MultitaskModel.from_pretrained(multitask_model_repo)
        # Initialize other extractors
        self.spacy_extractor = NERExtractor()
        self.duckling_extractor = SlotFiller()

        # Get NER labels for decoding predictions
        self.id2ner = self.multitask_model.config.id2label_ner

        print("\nNLU Processor ready.\n")

    def _decode_ner_predictions(self, text, ner_logits, encoding):
        """
        Decodes and groups token-level NER predictions into complete entities
        using a more robust BIO grouping logic.
        """
        predictions = torch.argmax(ner_logits, dim=-1)[0].tolist()

        entities = []
        current_entity_group = []

        for i, token_pred_id in enumerate(predictions):
            tag = self.id2ner[str(token_pred_id)]

            # This handles special tokens like [CLS] and [SEP]
            if encoding.token_to_chars(i) is None:
                continue

            if tag.startswith("B-"):  # Beginning of a new entity
                # If we were tracking a previous entity, finalize it first.
                if current_entity_group:
                    entities.append(current_entity_group)
                # Start a new entity group with the current token index and tag.
                current_entity_group = [(i, tag)]

            elif tag.startswith("I-"):  # Inside an existing entity
                # This is a crucial check. We only add the 'I-' tag if it follows
                # a 'B-' or 'I-' tag of the *same entity type*.
                if current_entity_group:
                    base_tag_type = current_entity_group[0][1][
                        2:
                    ]  # e.g., "practitioner_name"
                    if tag[2:] == base_tag_type:
                        current_entity_group.append((i, tag))
                    else:
                        # This is an invalid I- tag. Finalize the previous entity and discard this one.
                        entities.append(current_entity_group)
                        current_entity_group = []
                # If there's no preceding B- tag, we discard this invalid I- tag.

            else:  # Outside of any entity ('O' tag)
                # If we were tracking an entity, this is the end of it.
                if current_entity_group:
                    entities.append(current_entity_group)
                current_entity_group = []

        # Add the last entity if the sentence ends with one
        if current_entity_group:
            entities.append(current_entity_group)

        # Convert the grouped token indices into final entity objects
        final_entities = []
        for group in entities:
            start_token_index = group[0][0]
            end_token_index = group[-1][0]
            label = group[0][1][2:]  # Get label from the B- tag

            start_char = encoding.token_to_chars(start_token_index).start
            end_char = encoding.token_to_chars(end_token_index).end

            final_entities.append(
                {
                    "entity": label,
                    "value": text[start_char:end_char],
                    "extractor": "multitask_model",
                }
            )

        return final_entities

    def _fuse_practitioner_entities(self, all_entities, text):
        """
        Merges practitioner_name and PERSON entities by concatenating their
        unique values to avoid simple repetition.
        """
        # Collect all fragments from both sources
        practitioner_frags = [
            e["value"]
            for e in all_entities
            if e["entity"] in ["practitioner_name", "PERSON"]
        ]
        other_entities = [
            e
            for e in all_entities
            if e["entity"] not in ["practitioner_name", "PERSON"]
        ]

        if not practitioner_frags:
            return other_entities

        # Use dict.fromkeys to get unique fragments while preserving their order of appearance
        unique_frags = list(dict.fromkeys(practitioner_frags))

        # remove redundant substrings
        cleaned_frags = []
        for frag in unique_frags:
            is_redundant = False
            # Check if this fragment is a substring of any other, longer fragment
            for other_frag in unique_frags:
                if frag != other_frag and frag in other_frag:
                    is_redundant = True
                    break
            if not is_redundant:
                cleaned_frags.append(frag)

        # Join the cleaned, meaningful parts
        fused_name = " ".join(cleaned_frags)

        final_entities = other_entities
        final_entities.append(
            {
                "entity": "practitioner_name",
                "value": fused_name,
                "extractor": "multitask_model+spacy",  # Indicate it was a result of fusion
            }
        )

        return final_entities

    def process(self, text: str) -> dict:
        """
        Processes text with all NLU components and merges the results.
        """
        inputs = self.tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            outputs = self.multitask_model(**inputs)

        intent_logits = outputs["intent_logits"]
        intent_id = torch.argmax(intent_logits, dim=-1).item()
        intent_name = self.multitask_model.config.id2label_intent[str(intent_id)]

        ner_logits = outputs["ner_logits"]
        custom_entities = self._decode_ner_predictions(text, ner_logits, inputs)

        spacy_entities = self.spacy_extractor.extract_entities(text)
        time_entity = self.duckling_extractor.parse_time(text)

        # First, combine all extracted entities (except time)
        initial_entities = custom_entities + spacy_entities
        # Then, fuse the practitioner name fragments
        fused_entities = self._fuse_practitioner_entities(initial_entities, text)

        # Add the time entity back in
        all_entities = fused_entities

        if time_entity:
            all_entities.append(
                {
                    "entity": "time",
                    "value": time_entity["value"],
                    "extractor": "duckling",
                }
            )

        return {
            "text": text,
            "intent": {
                "name": intent_name,
                "confidence": torch.nn.functional.softmax(intent_logits, dim=-1)
                .max()
                .item(),
            },
            "entities": all_entities,  # The entities are already grouped correctly
        }


# Standalone test block to see it in action
if __name__ == "__main__":
    # Make sure you are logged into Hugging Face if the model is private
    # from huggingface_hub import login; login()
    load_dotenv()
    repo_id = os.getenv("HUB_MODEL_ID")

    # Ensure Duckling container is running via `make up`
    nlu_processor = NLUProcessor(multitask_model_repo=repo_id)

    test_text = "I would like to book a meeting with Dr. Caruccio for tomorrow at 5pm?"

    print(f"\nProcessing text: '{test_text}'")
    structured_data = nlu_processor.process(test_text)

    # Pretty-print the JSON output
    print("\n--- Unified NLU Output ---")
    print(json.dumps(structured_data, indent=2))
    print("--------------------------")
