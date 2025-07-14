import os
import json
import joblib
from sentence_transformers import SentenceTransformer
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv


class IntentClassifier:
    def __init__(self, repo_id: str):
        """
        Loads the KNN classifier and its artifacts from a Hugging Face Hub repository.

        Args:
            repo_id (str): The ID of the repository on the Hub (e.g., 'username/repo-name').
        """
        # Ensure the HF_TOKEN is available if the repo is private
        # For public repos, this is not strictly necessary but good practice
        hf_token = os.getenv("HF_TOKEN")

        # 1. Download the artifacts from the Hub.
        #    hf_hub_download returns the local path to the cached file.
        knn_model_path = hf_hub_download(
            repo_id=repo_id, filename="knn_model.joblib", token=hf_token
        )
        id2label_path = hf_hub_download(
            repo_id=repo_id, filename="id2label.json", token=hf_token
        )

        # 2. Load the Sentence Transformer model
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        # 3. Load the downloaded KNN model and label mapping
        self.knn = joblib.load(knn_model_path)
        with open(id2label_path, "r") as f:
            self.id_to_label = {int(k): v for k, v in json.load(f).items()}

    def predict(self, text: str) -> str:
        """
        Predicts the intent for a given text string using embeddings and KNN.
        """
        text_embedding = self.embedding_model.encode(
            text, convert_to_tensor=False
        ).reshape(1, -1)
        predicted_class_id = self.knn.predict(text_embedding)[0]
        return self.id_to_label[predicted_class_id]


if __name__ == "__main__":
    # Load the model from the Hub
    load_dotenv()
    model_repo_id = os.getenv("HUB_MODEL_ID")
    classifier = IntentClassifier(repo_id=model_repo_id)

    # Tests
    text1 = "I want to schedule a meeting with John for next Tuesday"
    intent1 = classifier.predict(text1)
    print(f"Text: '{text1}'\nPredicted Intent: '{intent1}'\n")

    text2 = "thanks, that's all"
    intent2 = classifier.predict(text2)
    print(f"Text: '{text2}'\nPredicted Intent: '{intent2}'\n")
