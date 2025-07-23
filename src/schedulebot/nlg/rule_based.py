import random
from data.appointment_id_generator import generate_appointment_id


class NLGModule:
    """
    Handles the generation of natural language responses using a rule-based
    template system.
    """

    def __init__(self):
        """
        Initializes the NLG Module by defining the response templates.
        """
        print("Initializing Rule-Based NLG Module...")
        self.templates = {
            "greet": [
                "Hello! How can I help you with your appointments today?",
                "Hi there! What can I do for you?",
                "Welcome! How can I assist you?",
            ],
            "say_goodbye": [
                "Goodbye! Have a great day.",
                "Farewell! Let me know if you need anything else.",
                "Bye for now!",
            ],
            "confirm_booking": [
                "Okay, I have you down for a {appointment_type} with {practitioner_name} at {time}. Does that sound right?",
                "Just to confirm, you'd like to book a {appointment_type} with {practitioner_name} for {time}. Is that correct?",
            ],
            "confirm_reschedule": [
                "Got it. You'd like to move appointment {appointment_id} to {time}. Should I go ahead and make that change?",
                "To confirm, we are rescheduling appointment {appointment_id} to {time}. Is this correct?",
            ],
            "confirm_cancellation": [
                "Are you sure you want to cancel appointment #{appointment_id}?",
                "Just to double-check, you'd like to cancel your appointment with ID #{appointment_id}. Is that right?",
            ],
            "request_information": [
                "To proceed, I'll need a bit more information. Could you please provide the {missing_slots}?",
                "I can help with that! I just need you to provide the {missing_slots}.",
            ],
            "cancel_action": [
                "Okay, I've cancelled that request. Is there anything else I can help you with?",
                "No problem, that action has been cancelled. What else can I do for you?",
            ],
            # --- Templates for successful tool actions ---
            "respond_execute_booking": [
                "All set! Your appointment is booked. {result}",
                "Great, you are confirmed. {result}",
            ],
            "respond_execute_cancellation": [
                "Okay, I've processed that for you. {result}",
                "Done. {result}",
            ],
            "respond_execute_reschedule": [
                "The appointment has been updated. {result}",
                "All set. {result}",
            ],
            "respond_execute_query_avail": [
                "Here is the availability I found: {result}",
                "Let's see... {result}",
            ],
            # --- Templates for suggestions and failures ---
            "suggest_slots": [
                "I'm sorry, but that time is unavailable because: {reason}. However, here are some open slots for that day: {suggestions}.",
                "Unfortunately, that time won't work ({reason}). You could try one of these times instead: {suggestions}.",
            ],
            "inform_failure": [
                "I'm sorry, I was unable to complete your request. Reason: {message}",
                "Apologies, but I ran into an issue: {message}",
            ],
            "fallback": [
                "I'm sorry, I didn't quite understand that. Could you please rephrase?",
                "I'm not sure how to help with that. I can assist with scheduling, rescheduling, and canceling appointments.",
            ],
        }
        print("✅ Rule-Based NLG Module ready.")

    def generate_response(self, action: dict) -> str:
        """
        Takes a structured action and generates a text response from a template.
        """
        action_type = action.get("action", "fallback")
        details = action.get("details", {})

        # Get a random template for the given action type
        if action_type in self.templates:
            template = random.choice(self.templates[action_type])

            # Fill in any placeholders in the template
            if "missing_slots" in action:
                details["missing_slots"] = " and ".join(action["missing_slots"])

            # Use a dummy ID for booking confirmations
            if action_type == "execute_booking":
                details["appointment_id"] = generate_appointment_id()

            # Use .get() to avoid errors if a key is missing
            return template.format(**{k: details.get(k, f"{{{k}}}") for k in details})
        else:
            # If the action is unknown, use the fallback
            return random.choice(self.templates["fallback"])
