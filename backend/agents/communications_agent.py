import json
from pathlib import Path

ANNOUNCEMENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "announcements.json"
APPOINTMENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "appointments.json"


class CommunicationAgent:

    # =============================
    # Data Loaders
    # =============================

    def get_announcements(self):
        try:
            with open(ANNOUNCEMENTS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    # =============================
    # 1. Draft Emails
    # =============================

    def draft_email(self, recipient: str, subject: str, purpose: str):
        body = f"Dear {recipient},\n\nThis is regarding {purpose}.\n\nPlease let us know if you have any questions.\n\nBest regards,\nSmart Campus Administration"
        return {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "Draft Generated"
        }

    # =============================
    # 2. Send Notifications
    # =============================

    def send_notification(self, title: str, message: str, target_audience: str = "All Students"):
        notification_entry = {
            "id": f"NOTIF_{len(self.get_announcements()) + 1:03d}",
            "title": title,
            "message": message,
            "audience": target_audience,
            "status": "Sent"
        }
        return {
            "success": True,
            "message": f"Notification '{title}' broadcasted to {target_audience}.",
            "notification": notification_entry
        }

    # =============================
    # 3. Generate Announcements
    # =============================

    def create_announcement(self, title: str, content: str, category: str = "General"):
        try:
            with open(ANNOUNCEMENTS_PATH, "r", encoding="utf-8") as f:
                announcements = json.load(f)
        except FileNotFoundError:
            announcements = []

        new_announcement = {
            "id": f"ANN_{len(announcements) + 1:03d}",
            "title": title,
            "content": content,
            "category": category,
            "date": "2026-08-08"
        }
        announcements.insert(0, new_announcement)

        with open(ANNOUNCEMENTS_PATH, "w", encoding="utf-8") as f:
            json.dump(announcements, f, indent=4)

        return {
            "success": True,
            "message": "Announcement published successfully!",
            "announcement": new_announcement
        }

    # =============================
    # 4. Appointment Scheduling
    # =============================

    def schedule_appointment(self, student_id: str, officer: str, date: str, time_slot: str, reason: str):
        try:
            with open(APPOINTMENTS_PATH, "r", encoding="utf-8") as f:
                appointments = json.load(f)
        except FileNotFoundError:
            appointments = []

        new_appointment = {
            "id": f"APT_{len(appointments) + 1:03d}",
            "student_id": student_id,
            "officer": officer,
            "date": date,
            "time_slot": time_slot,
            "reason": reason,
            "status": "Confirmed"
        }
        appointments.append(new_appointment)

        with open(APPOINTMENTS_PATH, "w", encoding="utf-8") as f:
            json.dump(appointments, f, indent=4)

        return {
            "success": True,
            "message": f"Appointment booked with {officer} on {date} at {time_slot}.",
            "appointment": new_appointment
        }
    