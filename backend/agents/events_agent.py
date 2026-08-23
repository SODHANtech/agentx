import json
from pathlib import Path
from datetime import datetime

EVENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "events.json"
REGISTRATION_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "event_registrations.json"
)


class EventsAgent:

    # =============================
    # Load Data
    # =============================

    def get_events(self):
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_registrations(self):
        try:
            with open(REGISTRATION_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_registrations(self, registrations):
        with open(REGISTRATION_PATH, "w", encoding="utf-8") as f:
            json.dump(registrations, f, indent=4)

    # =============================
    # Main Handler
    # =============================

    def handle(self, query: str):

        query = query.lower().strip()

        # Register
        if "register" in query:
            return self.register_event(query)

        # Cancel
        if "cancel" in query:
            return self.cancel_registration(query)

        # My Registered Events
        if (
            "my events" in query
            or "registered events" in query
            or "my registrations" in query
        ):
            return self.get_registered_events()

        # Show All Events
        if any(word in query for word in [
            "show events",
            "all events",
            "upcoming",
            "events"
        ]):
            return {
                "events": self.get_upcoming_events()
            }

        # Search by Month
        result = self.search_by_month(query)
        if result:
            return {"events": result}

        # Search by Date
        result = self.search_by_date(query)
        if result:
            return {"events": result}

        # Search by Venue
        result = self.search_by_venue(query)
        if result:
            return {"events": result}

        # Smart Search
        return {
            "events": self.search_event(query)
        }

    # =============================
    # Upcoming Events
    # =============================

    def get_upcoming_events(self):
        events = self.get_events()
        return sorted(events, key=lambda x: x["date"])

    # =============================
    # Registered Events
    # =============================

    def get_registered_events(self, student_id: str = "S001"):
        registrations = self.get_registrations()
        my_events = [
            reg
            for reg in registrations
            if reg.get("student_id") == student_id
        ]
        return {
            "registered_events": my_events
        }

    # =============================
    # Search by Month
    # =============================

    def search_by_month(self, query):

        months = [
            "january", "february", "march",
            "april", "may", "june",
            "july", "august", "september",
            "october", "november", "december"
        ]

        events = self.get_events()

        for month in months:

            if month in query:

                return [
                    event
                    for event in events
                    if datetime.strptime(
                        event["date"],
                        "%Y-%m-%d"
                    ).strftime("%B").lower() == month
                ]

        return []

    # =============================
    # Search by Date
    # =============================

    def search_by_date(self, query):

        events = self.get_events()

        return [
            event
            for event in events
            if event["date"] in query
        ]

    # =============================
    # Search by Venue
    # =============================

    def search_by_venue(self, query):

        events = self.get_events()

        return [
            event
            for event in events
            if event["venue"].lower() in query
        ]

    # =============================
    # Smart Search
    # =============================

    def search_event(self, query):

        events = self.get_events()

        keywords = [
            word
            for word in query.lower().split()
            if len(word) > 2
        ]

        results = []

        for event in events:

            searchable = (
                event.get("title", "")
                + " "
                + event.get("venue", "")
                + " "
                + event.get("description", "")
                + " "
                + event.get("type", "")
            ).lower()

            score = 0

            for keyword in keywords:
                if keyword in searchable:
                    score += 1

            if score > 0:
                results.append((score, event))

        results.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [
            item[1]
            for item in results
        ]

    # =============================
    # Cancel Registration
    # =============================

    def cancel_registration(self, query):

        registrations = self.get_registrations()

        updated = []
        removed = False

        for reg in registrations:

            if (
                reg.get("student_id") == "S001"
                and reg.get("event", "").lower() in query.lower()
            ):
                removed = True
                continue

            updated.append(reg)

        self.save_registrations(updated)

        if removed:
            return {
                "success": True,
                "message": "Registration cancelled successfully."
            }

        return {
            "success": False,
            "message": "No registration found."
        }

    # =============================
    # Register Event
    # =============================

    def register_event(self, query):

        events = self.get_events()
        registrations = self.get_registrations()

        for event in events:

            if event["title"].lower() in query.lower() or query.lower() in event["title"].lower():

                for reg in registrations:

                    if (
                        reg.get("student_id") == "S001"
                        and reg.get("event") == event["title"]
                    ):
                        return {
                            "success": False,
                            "message": f"You are already registered for {event['title']}."
                        }

                registrations.append({
                    "student_id": "S001",
                    "event": event["title"],
                    "registered": True,
                    "date": event.get("date", ""),
                    "venue": event.get("venue", "")
                })

                self.save_registrations(registrations)

                return {
                    "success": True,
                    "message": f"Successfully registered for {event['title']}."
                }

        return {
            "success": False,
            "message": "Event not found."
        }

    # =============================
    # Calendar Export (.ics)
    # =============================

    def generate_ics(self, event_title: str) -> str:
        events = self.get_events()
        event = next((e for e in events if e["title"].lower() == event_title.lower()), None)

        if not event:
            return None

        clean_date = event.get("date", "").replace("-", "")

        ics_content = (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//Smart Campus AI//EN\n"
            "BEGIN:VEVENT\n"
            f"SUMMARY:{event.get('title')}\n"
            f"DESCRIPTION:{event.get('description', 'Campus Event')}\n"
            f"LOCATION:{event.get('venue', 'Campus')}\n"
            f"DTSTART:{clean_date}T090000Z\n"
            f"DTEND:{clean_date}T170000Z\n"
            f"STATUS:CONFIRMED\n"
            "END:VEVENT\n"
            "END:VCALENDAR"
        )
        return ics_content

    # =============================
    # Event Reminders
    # =============================

    def get_event_reminders(self, student_id: str = "S001"):
        registrations = self.get_registrations()
        my_events = [r["event"] for r in registrations if r.get("student_id") == student_id]
        events = self.get_events()

        reminders = []
        for evt in events:
            if evt["title"] in my_events:
                reminders.append({
                    "id": f"rem_{evt['title']}",
                    "title": f"Upcoming Event: {evt['title']}",
                    "message": f"You are registered for {evt['title']} on {evt['date']} at {evt['venue']}.",
                    "type": "event_reminder",
                    "date": evt.get("date", "")
                })
        return reminders