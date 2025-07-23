import sqlite3
import datetime
import logging

# Get the logger instance that is configured in your main app.py
# This ensures all log messages go to the same place (chatbot.log)
logger = logging.getLogger(__name__)


class CalendarClient:
    """
    A client to interact with a local SQLite database for appointments,
    enforcing business rules from a configuration.
    """

    def __init__(self, config, db_path="calendar.db"):
        """Initializes the database connection and stores the config."""
        self.config = config
        self.db_path = db_path
        try:
            # Allow the connection to be used across different threads (for Gradio)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._create_table()
            logger.info(f"Successfully connected to database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            self.conn = None

    def _create_table(self):
        """Creates the appointments table if it's not already present."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    summary TEXT NOT NULL,
                    practitioner_name TEXT,
                    appointment_type TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL
                );
            """
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating appointments table: {e}")

    def _is_slot_booked(self, start_time, end_time):
        """Checks if a specific time range overlaps with any existing appointment."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM appointments
            WHERE (start_time < ? AND end_time > ?)
        """,
            (end_time.isoformat(), start_time.isoformat()),
        )
        return cursor.fetchone()[0] > 0

    def _respects_minimum_gap(self, start_time, end_time):
        """Checks if the slot respects the minimum gap between appointments."""
        gap_minutes = self.config["min_gap_minutes"]
        time_before = start_time - datetime.timedelta(minutes=gap_minutes)
        time_after = end_time + datetime.timedelta(minutes=gap_minutes)
        return not self._is_slot_booked(time_before, time_after)

    def _is_within_working_hours(self, start_time, end_time):
        """Checks if the slot is within the defined working hours."""
        working_start = datetime.datetime.strptime(
            self.config["working_hours"]["start"], "%H:%M"
        ).time()
        working_end = datetime.datetime.strptime(
            self.config["working_hours"]["end"], "%H:%M"
        ).time()
        return working_start <= start_time.time() and end_time.time() <= working_end

    def _is_during_lunch_break(self, start_time, end_time):
        """Checks if the slot falls within the lunch break."""
        lunch_start = datetime.datetime.strptime(
            self.config["lunch_break"]["start"], "%H:%M"
        ).time()
        lunch_end = datetime.datetime.strptime(
            self.config["lunch_break"]["end"], "%H:%M"
        ).time()
        return not (end_time.time() <= lunch_start or start_time.time() >= lunch_end)

    def _is_on_working_day(self, start_time):
        """Checks if the date is a working day."""
        return start_time.strftime("%A") not in self.config["non_working_days"]

    def _is_daily_limit_reached(self, start_time):
        """Checks if the maximum number of daily appointments has been reached."""
        cursor = self.conn.cursor()
        day_start = start_time.strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM appointments WHERE date(start_time) = ?", (day_start,)
        )
        return cursor.fetchone()[0] >= self.config["max_appointments_per_day"]

    def check_availability(self, start_time: datetime.datetime):
        """
        Checks if a given start time is valid for a new appointment
        based on all business rules.
        """
        end_time = start_time + datetime.timedelta(
            minutes=self.config["slot_duration_minutes"]
        )

        if not self._is_on_working_day(start_time):
            return False, "This is a non-working day."
        if self._is_daily_limit_reached(start_time):
            return (
                False,
                "The maximum number of appointments for this day has been reached.",
            )
        if not self._is_within_working_hours(start_time, end_time):
            return False, "This time is outside of working hours."
        if self._is_during_lunch_break(start_time, end_time):
            return False, "This time falls within the lunch break."
        if self._is_slot_booked(start_time, end_time):
            return False, "This time slot is already booked."
        if not self._respects_minimum_gap(start_time, end_time):
            return False, "This time is too close to another appointment."

        return True, "This time slot is available."

    def book_appointment(
        self,
        summary: str,
        practitioner_name: str,
        appointment_type: str,
        start_time: datetime.datetime,
    ):
        """Creates an event in the database after validating availability."""
        end_time = start_time + datetime.timedelta(
            minutes=self.config["slot_duration_minutes"]
        )
        is_available, reason = self.check_availability(start_time)
        if not is_available:
            logger.warning(f"Booking failed for '{summary}' at {start_time}: {reason}")
            return None, reason

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO appointments (summary, practitioner_name, appointment_type, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
                (
                    summary,
                    practitioner_name,
                    appointment_type,
                    start_time.isoformat(),
                    end_time.isoformat(),
                ),
            )
            self.conn.commit()
            appt_id = cursor.lastrowid
            logger.info(f"Successfully booked appointment ID {appt_id}: {summary}")
            return appt_id, "Appointment booked successfully."
        except sqlite3.Error as e:
            logger.error(f"Database error during booking: {e}")
            return None, "A database error occurred."

    def find_available_slots(self, start_date: datetime.date):
        """
        Finds the first few available slots for a given day.
        """
        available_slots = []
        working_start_time = datetime.datetime.strptime(
            self.config["working_hours"]["start"], "%H:%M"
        ).time()
        working_end_time = datetime.datetime.strptime(
            self.config["working_hours"]["end"], "%H:%M"
        ).time()
        current_slot_start = datetime.datetime.combine(start_date, working_start_time)
        day_end = datetime.datetime.combine(start_date, working_end_time)
        while current_slot_start < day_end:
            is_available, reason = self.check_availability(current_slot_start)
            if is_available:
                available_slots.append(current_slot_start)
                if len(available_slots) >= 3:
                    break
            current_slot_start += datetime.timedelta(
                minutes=self.config["slot_duration_minutes"]
            )
        return available_slots

    def cancel_appointment(self, appointment_id: int) -> bool:
        """Deletes an appointment by its ID. Returns True if successful."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            self.conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Successfully cancelled appointment ID {appointment_id}")
            else:
                logger.warning(
                    f"Attempted to cancel non-existent appointment ID {appointment_id}"
                )
            return success
        except sqlite3.Error as e:
            logger.error(
                f"Database error during cancellation for ID {appointment_id}: {e}"
            )
            return False

    def reschedule_appointment(
        self, appointment_id: int, new_start_time: datetime.datetime
    ) -> bool:
        """Updates the time for an existing appointment. Returns True if successful."""
        new_end_time = new_start_time + datetime.timedelta(
            minutes=self.config["slot_duration_minutes"]
        )
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE appointments SET start_time = ?, end_time = ? WHERE id = ?",
                (new_start_time.isoformat(), new_end_time.isoformat(), appointment_id),
            )
            self.conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(
                    f"Successfully rescheduled appointment ID {appointment_id} to {new_start_time}"
                )
            else:
                logger.warning(
                    f"Attempted to reschedule non-existent appointment ID {appointment_id}"
                )
            return success
        except sqlite3.Error as e:
            logger.error(
                f"Database error during reschedule for ID {appointment_id}: {e}"
            )
            return False

    def __del__(self):
        """Ensures the database connection is closed when the object is destroyed."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
