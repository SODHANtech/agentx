import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "timetable.json")


class AcademicAgent:

    def get_today_classes(self, day: str):
        day_lower = day.strip().lower()

        if day_lower == "sunday":
            return {
                "message": "Sunday is an official campus holiday. No classes are scheduled."
            }

        with open(DATA_PATH, "r", encoding="utf-8") as file:
            timetable = json.load(file)

        classes = [
            item for item in timetable
            if item["day"].lower() == day_lower
        ]

        if not classes:
            return {
                "message": f"No classes found for {day.strip().capitalize()}"
            }

        return classes