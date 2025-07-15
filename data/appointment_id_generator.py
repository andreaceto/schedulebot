import pandas as pd
import random
import string
import os


def generate_appointment_id():
    """
    Generates a random appointment ID in the format #123456.
    """
    numbers = "".join(random.choices(string.digits, k=6))
    return f"#{numbers}"


def create_id_file(num_to_generate, output_path):
    """
    Generates a specified number of IDs and saves them to a CSV file.
    """
    print(f"Generating {num_to_generate} appointment IDs...")

    # Create a list of dictionaries
    id_log = [
        {"text": generate_appointment_id(), "entity": "appointment_id"}
        for _ in range(num_to_generate)
    ]

    # Convert to DataFrame
    ids_df = pd.DataFrame(id_log)

    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # Save to CSV
    ids_df.to_csv(output_path, index=False)
    print(f"✅ Successfully saved IDs to '{output_path}'")


# This part runs when you execute the script directly
if __name__ == "__main__":
    # --- Configuration ---
    NUM_IDS_TO_GENERATE = 1500
    OUTPUT_FILE = os.path.join("data", "raw", "entities", "appointment_id.csv")

    create_id_file(NUM_IDS_TO_GENERATE, OUTPUT_FILE)
