from src.schedulebot.core.conversation_manager import ConversationManager
import os
from dotenv import load_dotenv


def main():
    """
    Main loop to interact with the chatbot from the command line.
    """
    # Load environment variables
    load_dotenv()
    repo_id = os.getenv("HUB_MODEL_ID")

    print("Initializing ConversationManager...")
    manager = ConversationManager(nlu_model_repo=repo_id)

    print("\nScheduleBOT+ is active! Type 'exit' to quit.")
    print("--------------------------------------------------")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        bot_response = manager.get_response(user_input)
        print(f"Bot: {bot_response}")


if __name__ == "__main__":
    main()
