import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "timetable.json")


class AcademicAgent:

    def get_today_classes(self, day: str):

        with open(DATA_PATH, "r") as file:
            timetable = json.load(file)

        classes = [
            item for item in timetable
            if item["day"].lower() == day.lower()
        ]

        if not classes:
            return {
                "message": f"No classes found for {day}"
            }

        return classes