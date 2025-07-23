import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from data.appointment_id_generator import generate_appointment_id


class NLGModule:
    """
    Handles NLG using the more powerful Qwen2.5-0.5B-Instruct model.
    """

    def __init__(self, model_repo_id="unsloth/Qwen2.5-0.5B-Instruct-bnb-4bit"):
        print("Initializing NLG Module SLM (Qwen2.5)...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_repo_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_repo_id,
                load_in_4bit=True,  # Load the model in 4-bit
                torch_dtype=torch.bfloat16,
                device_map="auto",  # Automatically use GPU if available
            )
            print("✅ NLG SLM loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load Qwen2.5 model for NLG. Error: {e}")
            self.model = None

    def _build_prompt(self, action: dict) -> list:
        """
        Builds a prompt for the SLM using the chat template format.
        """
        details = action.get("details", {})
        action_type = action.get("action")

        # --- Convert Action to a Natural Language Instruction ---
        instruction = ""
        if action_type == "greet":
            instruction = "Greet the user warmly and ask how you can help."
        elif action_type == "say_goodbye":
            instruction = "Say a friendly goodbye."
        elif action_type == "confirm_booking":
            instruction = f"Confirm you are booking a '{details.get('appointment_type', 'session')}' with {details.get('practitioner_name', 'the practitioner')} for {details.get('time')}. Ask for confirmation."
        elif action_type == "request_information":
            missing_slots = " and ".join(
                action.get("missing_slots", ["more information"])
            )
            instruction = f"Politely ask the user for the following missing information: {missing_slots}."
        elif action_type == "execute_booking":
            appt_id = generate_appointment_id()
            instruction = f"Inform the user their appointment is booked and provide their ID: {appt_id}."
        elif action_type == "execute_cancellation":
            instruction = f"Confirm to the user that appointment '#{details.get('appointment_id')}' has been cancelled."
        else:  # Fallback for all other actions
            instruction = (
                "Politely inform the user that you didn't understand their request."
            )

        # Qwen2.5 uses a chat template format, which is more robust
        messages = [
            {
                "role": "system",
                "content": "You are a friendly and helpful chatbot assistant. Your task is to turn a structured instruction into a natural, conversational response.",
            },
            {"role": "user", "content": f"Instruction: {instruction}"},
        ]
        return messages

    def generate_response(self, action: dict) -> str:
        """
        Takes a structured action and generates a human-like text response.
        """
        if not self.model:
            return "Error: The NLG model is not loaded."

        messages = self._build_prompt(action)

        # Use the tokenizer's chat template
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs, max_new_tokens=100, temperature=0.7, do_sample=True
        )

        # Decode only the newly generated tokens
        response_text = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        )

        return response_text.strip()
