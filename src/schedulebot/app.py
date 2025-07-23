import logging
import json
from src.schedulebot.core.dialogue_manager import DialogueManager
from src.schedulebot.nlu.nlu_processor import NLUProcessor
from src.schedulebot.nlg.rule_based import NLGModule
from src.schedulebot.core.tools import (
    initialize_tools,
)  # Import the new initializer function

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="chatbot.log",
    filemode="a",
)
logger = logging.getLogger(__name__)


class ChatbotApp:
    """
    Orchestrates the entire NLU -> DM -> NLG pipeline for the chatbot.
    """

    def __init__(self, nlu_model_repo: str, calendar_config: dict):
        """
        Initializes all three core modules of the chatbot.
        """
        self.nlu_processor = NLUProcessor(multitask_model_repo=nlu_model_repo)
        self.dialogue_manager = DialogueManager()
        self.nlg_module = NLGModule()

        self.tool_registry = initialize_tools(calendar_config)

        self.conversation_history = []
        logger.info("ChatbotApp initialized successfully with custom configuration.")

    def process_turn(self, user_input: str) -> str:
        """
        Processes a single turn of the conversation from user input to bot response.
        """
        nlu_output = self.nlu_processor.process(user_input)
        logger.info(f"NLU Output: {json.dumps(nlu_output, indent=2)}")

        action = self.dialogue_manager.get_next_action(nlu_output)
        logger.info(f"DM Action: {json.dumps(action, indent=2)}")

        tool_name = action.get("action")

        if tool_name in self.tool_registry:
            try:
                tool_function = self.tool_registry[tool_name]
                tool_result = tool_function(**action.get("details", {}))

                if tool_result.get("success"):
                    # For successful tool calls, use a specific response action
                    response_action = {
                        "action": f"respond_{tool_name}",
                        "details": {"result": tool_result.get("message")},
                    }
                else:
                    # Handle failures and suggestions
                    if tool_result.get("suggestions"):
                        suggestions_str = ", ".join(
                            [s.strftime("%I:%M %p") for s in tool_result["suggestions"]]
                        )
                        response_action = {
                            "action": "suggest_slots",
                            "details": {
                                "reason": tool_result.get("message"),
                                "suggestions": suggestions_str,
                            },
                        }
                    else:
                        response_action = {
                            "action": "inform_failure",
                            "details": tool_result,
                        }

                bot_response = self.nlg_module.generate_response(response_action)

            except Exception as e:
                logger.error(f"Error calling tool '{tool_name}': {e}")
                bot_response = self.nlg_module.generate_response({"action": "fallback"})
        else:
            # If it's not a tool, it's a direct NLG action (like greet, confirm, etc.)
            bot_response = self.nlg_module.generate_response(action)

        logger.info(f"NLG Response: {bot_response}")
        return bot_response
