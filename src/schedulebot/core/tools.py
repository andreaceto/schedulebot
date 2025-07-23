import datetime
import logging
from .calendar_client import CalendarClient

# Get the logger instance that is configured in your main app.py
logger = logging.getLogger(__name__)


def check_availability(
    calendar: CalendarClient, practitioner_name: str = None, time: str = None
) -> dict:
    """Checks availability and returns a structured result."""
    logger.info(
        f"Executing tool: check_availability with params: practitioner='{practitioner_name}', time='{time}'"
    )
    if not time:
        logger.warning("check_availability called without a time parameter.")
        return {
            "success": False,
            "message": "A specific date and time are required to check availability.",
        }
    try:
        start_time = datetime.datetime.fromisoformat(time)
        is_available, reason = calendar.check_availability(start_time)

        if is_available:
            return {"success": True, "message": reason}
        else:
            suggestions = calendar.find_available_slots(start_time.date())
            return {"success": False, "message": reason, "suggestions": suggestions}
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid time format in check_availability: '{time}'. Error: {e}")
        return {
            "success": False,
            "message": "That doesn't seem to be a valid date and time format.",
        }


def book_appointment(
    calendar: CalendarClient, practitioner_name: str, appointment_type: str, time: str
) -> dict:
    """Books an appointment and returns a structured result."""
    logger.info(
        f"Executing tool: book_appointment with params: practitioner='{practitioner_name}', type='{appointment_type}', time='{time}'"
    )
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
            return {"success": True, "message": reason, "appointment_id": appt_id}
        else:
            suggestions = calendar.find_available_slots(start_time.date())
            return {"success": False, "message": reason, "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Unhandled error in book_appointment: {e}")
        return {
            "success": False,
            "message": "I encountered an internal error while booking.",
        }


def cancel_appointment(calendar: CalendarClient, appointment_id: str) -> dict:
    """Cancels an appointment and returns a structured result."""
    logger.info(f"Executing tool: cancel_appointment with ID: {appointment_id}")
    try:
        clean_id = int(str(appointment_id).strip().replace("#", ""))
        if calendar.cancel_appointment(clean_id):
            return {
                "success": True,
                "message": f"Appointment #{clean_id} has been cancelled.",
            }
        else:
            return {
                "success": False,
                "message": f"I couldn't find an appointment with the ID #{clean_id}.",
            }
    except (ValueError, TypeError) as e:
        logger.error(
            f"Invalid appointment_id format in cancel_appointment: '{appointment_id}'. Error: {e}"
        )
        return {
            "success": False,
            "message": "That doesn't seem to be a valid appointment ID.",
        }


def reschedule_appointment(
    calendar: CalendarClient, appointment_id: str, time: str
) -> dict:
    """Reschedules an appointment and returns a structured result."""
    logger.info(
        f"Executing tool: reschedule_appointment with ID: {appointment_id}, new time: {time}"
    )
    try:
        clean_id = int(str(appointment_id).strip().replace("#", ""))
        new_start_time = datetime.datetime.fromisoformat(time)

        is_available, reason = calendar.check_availability(new_start_time)
        if not is_available:
            return {
                "success": False,
                "message": f"I can't reschedule to that time. Reason: {reason}",
            }

        if calendar.reschedule_appointment(clean_id, new_start_time):
            return {
                "success": True,
                "message": f"Appointment #{clean_id} has been rescheduled.",
            }
        else:
            return {
                "success": False,
                "message": f"I couldn't find appointment #{clean_id} to reschedule.",
            }
    except Exception as e:
        logger.error(f"Unhandled error in reschedule_appointment: {e}")
        return {
            "success": False,
            "message": "I encountered an error. Please provide a valid ID and a full date and time.",
        }


def initialize_tools(config: dict):
    """
    Initializes the CalendarClient and returns a registry of tool functions.
    """
    calendar = CalendarClient(config=config)

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
