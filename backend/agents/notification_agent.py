import json
from pathlib import Path
from datetime import datetime

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "reminders.json"


class NotificationAgent:

    def remind(self, query: str):

        reminder = {
            "id": int(datetime.now().timestamp()),
            "query": query,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Pending"
        }

        reminders = []

        if DATA_PATH.exists():
            with open(DATA_PATH, "r") as f:
                try:
                    reminders = json.load(f)
                except:
                    reminders = []

        reminders.append(reminder)

        with open(DATA_PATH, "w") as f:
            json.dump(reminders, f, indent=4)

        return {
            "message": "Reminder created successfully.",
            "reminder": reminder
        }

    def get_reminders(self):

        if not DATA_PATH.exists():
            return []

        with open(DATA_PATH, "r") as f:
            return json.load(f)