import unittest
import sys
import os

# Add the 'src' directory to the Python path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schedulebot.core.dialogue_manager import DialogueManager


class TestDialogueManager(unittest.TestCase):
    def setUp(self):
        """This method is called before each test."""
        self.manager = DialogueManager()

    def test_01_handle_greeting(self):
        """Tests if the manager returns a simple 'greet' action."""
        nlu_output = {"intent": {"name": "greeting"}}
        action = self.manager.get_next_action(nlu_output)
        self.assertEqual(action["action"], "greet")

    def test_02_schedule_request_missing_info(self):
        """Tests if the manager asks for missing info when scheduling."""
        nlu_output = {
            "intent": {"name": "schedule"},
            "entities": [{"entity": "practitioner_name", "value": "Dr. Smith"}],
        }
        action = self.manager.get_next_action(nlu_output)
        self.assertEqual(action["action"], "request_information")
        # The DM should identify that 'time' and 'appointment_type' are missing
        self.assertIn("time", action["missing_slots"])
        self.assertIn("appointment_type", action["missing_slots"])

    def test_03_schedule_request_all_info_present(self):
        """Tests if the manager moves to confirmation when all info is provided."""
        nlu_output = {
            "intent": {"name": "schedule"},
            "entities": [
                {"entity": "practitioner_name", "value": "Dr. Smith"},
                {"entity": "time", "value": "2025-08-01T14:00:00-07:00"},
                {"entity": "appointment_type", "value": "check-up"},
            ],
        }
        action = self.manager.get_next_action(nlu_output)
        self.assertEqual(action["action"], "confirm_booking")
        self.assertEqual(self.manager.state["pending_action"], "confirm_booking")
        self.assertIn("Dr. Smith", self.manager.state["pending_details"].values())

    def test_04_user_confirms_pending_action(self):
        """Tests if the manager executes the action after a positive reply."""
        # First, set up a pending action
        self.manager.state["pending_action"] = "confirm_booking"
        self.manager.state["pending_details"] = {"practitioner_name": "Dr. Smith"}

        # Now, simulate the user saying "yes"
        nlu_output = {"intent": {"name": "positive_reply"}}
        action = self.manager.get_next_action(nlu_output)

        self.assertEqual(action["action"], "execute_booking")
        self.assertEqual(action["details"]["practitioner_name"], "Dr. Smith")
        # Ensure the state was reset after the action
        self.assertIsNone(self.manager.state["pending_action"])

    def test_05_user_cancels_pending_action(self):
        """Tests if the manager cancels the action after a negative reply."""
        # Set up a pending action
        self.manager.state["pending_action"] = "confirm_cancellation"

        # Simulate the user saying "no"
        nlu_output = {"intent": {"name": "negative_reply"}}
        action = self.manager.get_next_action(nlu_output)

        self.assertEqual(action["action"], "cancel_action")
        # Ensure the state was reset
        self.assertIsNone(self.manager.state["pending_action"])

    def test_06_handle_multi_turn_request(self):
        """Tests the full flow of asking for and receiving missing info."""
        # Turn 1: User asks to cancel, but gives no ID
        nlu_turn1 = {"intent": {"name": "cancel"}}
        action1 = self.manager.get_next_action(nlu_turn1)

        self.assertEqual(action1["action"], "request_information")
        self.assertEqual(action1["missing_slots"], ["appointment_id"])
        # Check that the manager is now waiting for an appointment_id
        self.assertEqual(self.manager.state["awaiting_slot"], "appointment_id")
        self.assertEqual(self.manager.state["pending_action"], "cancel")

        # Turn 2: User provides the missing appointment ID
        nlu_turn2 = {
            "intent": {"name": "inform"},
            "entities": [{"entity": "appointment_id", "value": "#12345"}],
        }
        action2 = self.manager.get_next_action(nlu_turn2)

        # The manager should now have all info and move to confirmation
        self.assertEqual(action2["action"], "confirm_cancellation")
        self.assertEqual(action2["details"]["appointment_id"], "#12345")
        # Ensure the await state is cleared
        self.assertIsNone(self.manager.state["awaiting_slot"])


if __name__ == "__main__":
    unittest.main()
