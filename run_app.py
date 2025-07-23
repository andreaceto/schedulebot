import gradio as gr
import json
from src.schedulebot.app import ChatbotApp

# --- Global variable to hold our chatbot instance ---
chatbot_instance = None


def save_config(
    duration,
    gap,
    max_daily,
    work_start,
    work_end,
    lunch_start,
    lunch_end,
    non_working_days,
):
    """Saves the user's configuration to config.json and initializes the chatbot."""
    global chatbot_instance

    config = {
        "slot_duration_minutes": int(duration),
        "min_gap_minutes": int(gap),
        "max_appointments_per_day": int(max_daily),
        "working_hours": {"start": work_start, "end": work_end},
        "lunch_break": {"start": lunch_start, "end": lunch_end},
        "non_working_days": non_working_days,
    }

    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)

    print("--- Configuration Saved. Initializing Chatbot... ---")
    # Initialize the main app class with the new config
    chatbot_instance = ChatbotApp(
        nlu_model_repo="andreaceto/schedulebot-nlu-engine", calendar_config=config
    )
    print("--- Chatbot Ready ---")

    # Return updates to the Gradio UI to hide the setup and show the chat
    return {
        # --- NEW: Hide the main title ---
        main_title: gr.update(visible=False),
        setup_group: gr.update(visible=False),
        chat_group: gr.update(visible=True),
    }


def chat_interface(message, history):
    """The function that Gradio will call for each user message."""
    if chatbot_instance:
        response = chatbot_instance.process_turn(message)
        return response
    return "Error: Chatbot not initialized. Please set the configuration first."


# --- Build the Gradio UI using Blocks ---
with gr.Blocks(theme=gr.themes.Default(), title="ScheduleBOT+") as demo:
    # --- NEW: Create a separate component for the title ---
    main_title = gr.Markdown("# ScheduleBOT+ Configuration")

    # --- Setup Screen (Visible by default) ---
    with gr.Group(visible=True) as setup_group:
        gr.Markdown("## Calendar Settings")
        with gr.Row():
            slot_duration = gr.Number(label="Slot Duration (minutes)", value=30)
            min_gap = gr.Number(label="Min Gap Between (minutes)", value=15)
            max_appointments = gr.Number(label="Max Appointments per Day", value=10)
        gr.Markdown("### Working Hours")
        with gr.Row():
            working_start = gr.Textbox(label="Start (HH:MM)", value="09:00")
            working_end = gr.Textbox(label="End (HH:MM)", value="17:00")
        gr.Markdown("### Lunch Break")
        with gr.Row():
            lunch_start = gr.Textbox(label="Start (HH:MM)", value="13:00")
            lunch_end = gr.Textbox(label="End (HH:MM)", value="14:00")

        non_working = gr.CheckboxGroup(
            label="Non-Working Days",
            choices=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            value=["Saturday", "Sunday"],
        )

        save_button = gr.Button(
            "Save Configuration and Start Chatbot", variant="primary"
        )

    # --- Chat Screen (Hidden by default) ---
    with gr.Group(visible=False) as chat_group:
        gr.ChatInterface(
            fn=chat_interface,
            title="ScheduleBOT+",
            description="An intelligent agent for appointment management.",
            examples=[
                ["Hi there!"],
                ["Is 2 PM tomorrow available for a dental cleaning?"],
                ["I'd like to book a check-up with Dr. Smith."],
            ],
        )

    # --- UI Logic ---
    save_button.click(
        fn=save_config,
        inputs=[
            slot_duration,
            min_gap,
            max_appointments,
            working_start,
            working_end,
            lunch_start,
            lunch_end,
            non_working,
        ],
        # --- NEW: Add the title to the outputs ---
        outputs=[main_title, setup_group, chat_group],
    )


if __name__ == "__main__":
    demo.launch()
