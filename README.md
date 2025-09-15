# **ScheduleBOT: An Intelligent Appointment Scheduling Chatbot**

ScheduleBOT is a sophisticated, task-oriented chatbot designed for managing appointments. It leverages a modern, modular architecture to understand user requests, manage conversation context, and interact with a real calendar backend that enforces configurable business rules.

The project showcases a complete end-to-end development process, from custom dataset creation and advanced model training to building a fully functional and interactive application.

## **🚀 Features**

- **Advanced Natural Language Understanding (NLU)**: A hybrid NLU pipeline that fuses results from a custom-trained multitask model, spaCy, and Duckling for high-accuracy intent and entity recognition.
- **Stateful Dialogue Management**: A rule-based state machine that maintains conversation context, handles multi-turn dialogues, and gracefully manages missing information.
- **Configurable Calendar Backend**: Interacts with a real SQLite database that acts as a calendar, enforcing user-defined business logic at runtime.
- **Customizable Business Rules**: Users can define slot duration, working hours, lunch breaks, non-working days, and more through a startup UI.
- **Data-Driven Model Training**: The core NLU model is trained on a custom-built, augmented, and balanced dataset (HASD) to ensure robust performance.
- **Interactive User Interface**: A user-friendly web interface built with Gradio, featuring a two-stage setup for configuration and chat.
- **Reproducible Setup**: The entire application and its services are containerized with Docker and managed with a simple `Makefile`.

## **🏛️ Architecture**

The chatbot is built on a modern, three-part pipeline architecture (**NLU -> DM -> NLG**) which ensures a clear separation of concerns, making the system robust, predictable, and maintainable.

1. **Natural Language Understanding (NLU)**: The `NLUProcessor`'s sole responsibility is to convert raw user text into a structured JSON object. It intelligently fuses results from three parallel modules:
    - **Custom Multitask Model**: A fine-tuned `distilbert-base-uncased` model for domain-specific intent classification and entity recognition.
    - **spaCy**: For general-purpose named entities (like `PERSON`).
    - **Duckling**: For robust time/date extraction.
2. **Dialogue Management (DM)**: The `DialogueManager` acts as the "brain" of the chatbot. It is a rule-based state machine that takes the structured output from the NLU and, based on its internal state and logic, determines the bot's next logical action (e.g., `confirm_booking`, `request_information`).
3. **Natural Language Generation (NLG)**: The `NLG Module` is responsible for generating the final, human-like text response. It takes the structured action from the Dialogue Manager and uses a template-based system to create a friendly and natural-sounding message for the user.

## **🛠️ Installation & Setup**

### **Prerequisites**

- Docker and Docker Compose
- Python 3.10+
- A Hugging Face account (for downloading the NLU model)

### **1. Clone the Repository**

```bash
git clone <your-repo-url>
cd schedulebot

```

### **2. Set Up Environment Variables**

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env

```

Edit the `.env` file and add your Hugging Face Hub model ID:

```
HUB_MODEL_ID="andreaceto/schedulebot-nlu-engine"

```

### **3. Build Docker Services**

This command will build the Docker image for the application, installing all necessary dependencies, including the spaCy model.

```bash
make build

```

## **▶️ How to Run the Application**

1. **Start Backend Services**: This command starts the Duckling service in the background.

    ```bash
    make up

    ```

2. **Run the Gradio App**: This command starts the main application.

    ```bash
    make run

    ```

3. **Open the UI**: Navigate to the local URL provided in your terminal (usually `http://127.0.0.1:7860`).
4. **Configure the Calendar**: Use the startup screen to set your desired business rules for the calendar and click "Save Configuration and Start Chatbot".
5. **Chat!**: The chat interface will appear, ready for you to interact with.

When you are finished, you can stop the backend services with:

```bash
make down

```

## **🤖 Model Training and Data**

The core NLU model was trained on the custom **HASD (Hybrid Appointment Scheduling Dataset)**, which is publicly available [here](https://huggingface.co/datasets/andreaceto/hasd).

- **Data Strategy**: The dataset was built using a hybrid approach. Simple intents (`greeting`, `oos`, etc.) were sourced from the [`clinc/clinc_oos`](https://huggingface.co/datasets/clinc/clinc_oos) dataset and **down-sampled** to prevent class imbalance. Complex, entity-rich intents (`schedule`, `cancel`, etc.) were generated from templates.
- **Data Augmentation**: To increase diversity, **Contextual Word Replacement** was applied to the templates using a `distilbert-base-uncased` model to generate paraphrased variations while preserving placeholders.
- **Training Strategy**: The model was trained using a two-stage process:
    1. **Head Training**: The DistilBERT base was frozen, and only the custom MLP classification heads were trained with a high learning rate.
    2. **Fine-Tuning**: The top two layers of the DistilBERT base were unfrozen, and the entire model was fine-tuned with a low learning rate, using **Early Stopping** to prevent overfitting.

The Jupyter notebooks detailing this entire process can be found in the `notebooks/` directory.

The final trained NLU model, along with more specific informations and practical how-to-use instructions, is available [here](https://huggingface.co/andreaceto/schedulebot-nlu-engine).

## **🧪 Evaluation**

The chatbot was evaluated at both the component and end-to-end levels.

- **NLU Model**: Achieved excellent F1-scores for both intent classification and NER on the held-out test set.
- **Dialogue Manager**: The logical correctness was verified with a suite of unit tests located in `tests/test_dialogue_manager.py`.
- **End-to-End**: The chatbot achieved a **100% Task Success Rate** on a set of predefined core conversational scenarios.
