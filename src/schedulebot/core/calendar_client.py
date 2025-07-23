import sqlite3
import datetime


class CalendarClient:
    """
    A client to interact with a local SQLite database for appointments,
    enforcing business rules from a configuration.
    """

    def __init__(self, config, db_path="calendar.db"):
        """Initializes the database connection and stores the config."""
        self.config = config
        self.db_path = db_path
        # Allow the connection to be used across different threads (for Gradio)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        """Creates the appointments table if it's not already present."""
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
            return None, reason

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO appointments (summary, practitioner_name, appointment_type, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                summary,
                practitioner_name,
                appointment_type,
                start_time.isoformat(),
                end_time.isoformat(),
            ),
        )
        self.conn.commit()
        return cursor.lastrowid, "Appointment booked successfully."

    def cancel_appointment(self, appointment_id: int) -> bool:
        """Deletes an appointment by its ID. Returns True if successful."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def reschedule_appointment(
        self, appointment_id: int, new_start_time: datetime.datetime
    ) -> bool:
        """Updates the time for an existing appointment. Returns True if successful."""
        new_end_time = new_start_time + datetime.timedelta(
            minutes=self.config["slot_duration_minutes"]
        )
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE appointments
            SET start_time = ?, end_time = ?
            WHERE id = ?
        """,
            (new_start_time.isoformat(), new_end_time.isoformat(), appointment_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def __del__(self):
        """Ensures the database connection is closed when the object is destroyed."""
        self.conn.close()
