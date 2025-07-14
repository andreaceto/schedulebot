from src.schedulebot.nlp.intent_classifier import IntentClassifier
from src.schedulebot.nlp.slot_filler import SlotFiller


class ConversationManager:
    def __init__(self, nlu_model_repo: str):
        """
        Initializes the manager with the NLU models.
        """
        self.intent_classifier = IntentClassifier(repo_id=nlu_model_repo)
        self.slot_filler = SlotFiller()

    def get_response(self, user_text: str) -> str:
        """
        Processes the user's input and returns a text response.
        """
        # 1. Classify the intent
        intent = self.intent_classifier.predict(user_text)
        print(f"[DEBUG: Classified intent: {intent}]")
        print(f"[DEBUG: time_slot: {self.slot_filler.parse_time(user_text)}]")

        # 2. Logic based on the intent
        if intent == "greet":
            return "Hello! How can I help you with your appointments today?"

        if intent == "bye":
            return "Goodbye! Have a great day."

        if intent in ["book", "resched"]:
            # 3. Extract date and time if required by the intent
            time_slot = self.slot_filler.parse_time(user_text)

            action = "book" if intent == "book" else "reschedule"

            if time_slot:
                return f"Okay, I see you want to {action} an appointment for {time_slot['value']}. Is that correct?"
            else:
                return "Sure, but I didn't understand the date and time. Could you please specify when?"

        if intent == "cancel":
            return "Okay, I understand you want to cancel an appointment. Can you specify which one?"

        if intent == "avail":
            return "I'm checking your availability now. One moment..."

        # Fallback for unhandled intents
        return "I'm not sure I understood your request."
