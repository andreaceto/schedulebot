class DialogueManager:
    """
    A rule-based dialogue manager that tracks conversation state and determines
    the bot's next action based on the NLU output.
    """

    def __init__(self):
        """
        Initializes the conversation state.
        """
        self.state = {}
        self.reset_state()

    def reset_state(self):
        """
        Resets the conversation state to its default.
        """
        self.state = {
            "pending_action": None,  # e.g., 'confirm_booking', 'confirm_cancellation'
            "pending_details": {},  # Information related to the pending action
            "awaiting_slot": None,  # The slot the bot is waiting for the user to provide
        }

    def get_next_action(self, nlu_output: dict) -> dict:
        """
        Determines the bot's next action based on NLU output and conversation state.
        Returns a structured action dictionary for the NLG module.
        """
        intent = nlu_output.get("intent", {}).get("name")
        entities = {
            e["entity"].lower().replace("person", "practitioner_name"): e["value"]
            for e in nlu_output.get("entities", [])
        }

        # --- Handle Context-Dependent Replies First ---
        if self.state["awaiting_slot"] and self.state["awaiting_slot"] in entities:
            # The user has provided the missing information.
            # We merge it with the pending details and re-evaluate the original intent.
            self.state["pending_details"].update(entities)
            intent = self.state[
                "pending_action"
            ]  # Pretend the user repeated their original intent
            self.state["awaiting_slot"] = None  # Clear the await state

        if self.state["pending_action"] and intent in [
            "positive_reply",
            "negative_reply",
        ]:
            if intent == "positive_reply":
                action_to_execute = self.state["pending_action"].replace(
                    "confirm_", "execute_"
                )
                details = self.state["pending_details"]
                self.reset_state()
                return {"action": action_to_execute, "details": details}

            if intent == "negative_reply":
                action = {"action": "cancel_action"}
                self.reset_state()
                return action

        # --- Handle Primary Intents ---
        if intent == "greeting":
            return {"action": "greet"}

        if intent == "bye":
            return {"action": "say_goodbye"}

        if intent == "schedule":
            required = ["practitioner_name", "time", "appointment_type"]
            missing = [slot for slot in required if slot not in entities]

            if not missing:
                self.state["pending_action"] = "confirm_booking"
                self.state["pending_details"] = entities
                return {"action": "confirm_booking", "details": entities}
            else:
                self.state["pending_action"] = "schedule"
                self.state["pending_details"] = entities
                self.state["awaiting_slot"] = missing[0]
                return {"action": "request_information", "missing_slots": missing}

        if intent == "reschedule":
            required = ["appointment_id", "time"]
            missing = [slot for slot in required if slot not in entities]

            if not missing:
                self.state["pending_action"] = "confirm_reschedule"
                self.state["pending_details"] = entities
                return {"action": "confirm_reschedule", "details": entities}
            else:
                self.state["pending_action"] = "reschedule"
                self.state["pending_details"] = entities
                self.state["awaiting_slot"] = missing[0]
                return {"action": "request_information", "missing_slots": missing}

        if intent == "cancel":
            if "appointment_id" in entities:
                self.state["pending_action"] = "confirm_cancellation"
                self.state["pending_details"] = entities
                return {"action": "confirm_cancellation", "details": entities}
            else:
                self.state["pending_action"] = "cancel"
                self.state["pending_details"] = entities
                self.state["awaiting_slot"] = "appointment_id"
                return {
                    "action": "request_information",
                    "missing_slots": ["appointment_id"],
                }

        if intent == "query_avail":
            if "time" in entities:
                return {"action": "execute_query_avail", "details": entities}
            else:
                self.state["pending_action"] = "query_avail"
                self.state["awaiting_slot"] = "time"
                return {"action": "request_information", "missing_slots": ["time"]}

        return {"action": "fallback"}
