import requests
from datetime import datetime


class SlotFiller:
    def __init__(self, duckling_url: str = "http://localhost:8000/parse"):
        """
        Initializes the SlotFiller with the Duckling service URL.
        """
        self.duckling_url = duckling_url

    def parse_time(self, text: str) -> dict | None:
        """
        Sends text to Duckling to extract time-related information.
        Returns the first valid time entity found.
        """
        try:
            # Data to send to Duckling
            data = {"text": text, "locale": "en_US", "dims": '["time"]'}

            response = requests.post(self.duckling_url, data=data)
            response.raise_for_status()  # Raises an exception for HTTP errors

            parsed_data = response.json()

            if not parsed_data:
                return None

            # Extract the most relevant value
            # Duckling can return multiple values (e.g., "tomorrow at 5" -> tomorrow's date, hour 5)
            # We look for the 'value' type that contains complete date and time.
            for entity in parsed_data:
                if entity.get("dim") == "time" and entity["value"]["type"] == "value":
                    raw_time = entity["value"]["value"]
                    # Convert to a standard format (ISO 8601)
                    dt_object = datetime.fromisoformat(raw_time)
                    return {"text": entity["body"], "value": dt_object.isoformat()}

            return None

        except requests.exceptions.RequestException as e:
            print(
                f"ERROR: Unable to communicate with Duckling. Make sure it is running. Details: {e}"
            )
            return None


# Block to test the script directly
if __name__ == "__main__":
    filler = SlotFiller()

    test_text_1 = "I would like to book a meeting for tomorrow at 5 PM"
    time_info_1 = filler.parse_time(test_text_1)
    print(f"Text: '{test_text_1}'")
    print(f"Extracted info: {time_info_1}\n")

    test_text_2 = "Can we meet next Friday?"
    time_info_2 = filler.parse_time(test_text_2)
    print(f"Text: '{test_text_2}'")
    print(f"Extracted info: {time_info_2}\n")

    test_text_3 = "Hi, how are you?"
    time_info_3 = filler.parse_time(test_text_3)
    print(f"Text: '{test_text_3}'")
    print(f"Extracted info: {time_info_3}\n")
