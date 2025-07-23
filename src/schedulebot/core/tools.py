import datetime
from .calendar_client import CalendarClient


def check_availability(
    calendar: CalendarClient, practitioner_name: str = None, time: str = None
) -> str:
    """Checks if a specific time slot is available using the provided calendar client."""
    try:
        start_time = datetime.datetime.fromisoformat(time)
        is_available, reason = calendar.check_availability(start_time)
        return reason
    except (TypeError, ValueError):
        return "I can check availability, but I'll need a specific date and time."


def book_appointment(
    calendar: CalendarClient, practitioner_name: str, appointment_type: str, time: str
) -> str:
    """Books an appointment in the database using the provided calendar client."""
    try:
        start_time = datetime.datetime.fromisoformat(time)
        summary = f"{appointment_type} with {practitioner_name}"

        appt_id, reason = calendar.book_appointment(
            summary=summary,
            practitioner_name=practitioner_name,
            appointment_type=appointment_type,
            start_time=start_time,
        )

        if appt_id:
            return f"Success! Your appointment is booked. The ID is #{appt_id}."
        else:
            return f"I'm sorry, I couldn't book that. Reason: {reason}"
    except Exception as e:
        print(f"Error booking appointment: {e}")
        return "I'm sorry, I encountered an error while trying to book the appointment."


def cancel_appointment(calendar: CalendarClient, appointment_id: str) -> str:
    """Cancels an appointment in the database."""
    try:
        # Clean up the ID (e.g., remove '#')
        clean_id = int(str(appointment_id).strip().replace("#", ""))
        if calendar.cancel_appointment(clean_id):
            return f"Success! Appointment #{clean_id} has been cancelled."
        else:
            return f"I'm sorry, I couldn't find an appointment with the ID #{clean_id}."
    except (ValueError, TypeError):
        return "I can cancel an appointment, but I need a valid appointment ID."


def reschedule_appointment(
    calendar: CalendarClient, appointment_id: str, time: str
) -> str:
    """Reschedules an appointment in the database."""
    try:
        clean_id = int(str(appointment_id).strip().replace("#", ""))
        new_start_time = datetime.datetime.fromisoformat(time)

        # Check if the new time slot is available before rescheduling
        is_available, reason = calendar.check_availability(new_start_time)
        if not is_available:
            return f"I'm sorry, I can't reschedule to that time. Reason: {reason}"

        if calendar.reschedule_appointment(clean_id, new_start_time):
            return f"Success! Appointment #{clean_id} has been rescheduled to {new_start_time.strftime('%I:%M %p on %B %d')}."
        else:
            return f"I'm sorry, I couldn't find an appointment with the ID #{clean_id} to reschedule."
    except Exception as e:
        print(f"Error rescheduling: {e}")
        return "I'm sorry, I encountered an error. Please provide a valid appointment ID and a full date and time."


def initialize_tools(config: dict):
    """
    Initializes the CalendarClient with the given config and returns a
    registry of tool functions bound to that client.
    """
    calendar = CalendarClient(config=config)

    # Use lambda functions to pre-fill the 'calendar' argument for each tool
    tool_registry = {
        "execute_query_avail": lambda **kwargs: check_availability(
            calendar=calendar, **kwargs
        ),
        "execute_booking": lambda **kwargs: book_appointment(
            calendar=calendar, **kwargs
        ),
        "execute_cancellation": lambda **kwargs: cancel_appointment(
            calendar=calendar, **kwargs
        ),
        "execute_reschedule": lambda **kwargs: reschedule_appointment(
            calendar=calendar, **kwargs
        ),
    }
    return tool_registry
