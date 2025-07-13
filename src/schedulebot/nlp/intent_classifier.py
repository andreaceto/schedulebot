import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch


class IntentClassifier:
    def __init__(self, model_repo_id: str):
        """
        Loads the fine-tuned model and tokenizer from the Hugging Face Hub.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_repo_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_repo_id)
        self.id_to_label = self.model.config.id2label

    def predict(self, text: str) -> str:
        """
        Predicts the intent for a given text string.
        """
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True, truncation=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits

        predicted_class_id = torch.argmax(logits, dim=1).item()
        return self.id_to_label[predicted_class_id]


if __name__ == "__main__":
    # Load the model from the Hub
    load_dotenv()
    model_repo_id = os.getenv("HUB_MODEL_ID")
    classifier = IntentClassifier(model_repo_id=model_repo_id)

    # Tests
    text1 = "I want to schedule a meeting with John for next Tuesday"
    intent1 = classifier.predict(text1)
    print(f"Text: '{text1}'\nPredicted Intent: '{intent1}'\n")

    text2 = "thanks, that's all"
    intent2 = classifier.predict(text2)
    print(f"Text: '{text2}'\nPredicted Intent: '{intent2}'\n")
