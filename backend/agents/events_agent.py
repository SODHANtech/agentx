import json
import re
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.database import models

EVENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "events.json"


class EventsAgent:

    # =============================
    # Load Data
    # =============================

    def get_events(self):
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # =============================
    # Main Handler
    # =============================

    def handle(self, query: str, student_id: int = 2, db: Session = None):
        query = query.lower().strip()

        # Register
        if "register" in query:
            return self.register_event(query, student_id, db)

        # Cancel
        if "cancel" in query:
            return self.cancel_registration(query, student_id, db)

        # My Registered Events
        if (
            "my events" in query
            or "registered events" in query
            or "my registrations" in query
        ):
            return self.get_registered_events(student_id, db)

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

    def get_registered_events(self, student_id: int = 2, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            registrations = db.query(models.EventRegistration).filter(
                models.EventRegistration.student_id == student_id,
                models.EventRegistration.registered == True
            ).all()
            my_events = []
            for reg in registrations:
                my_events.append({
                    "student_id": f"STUDENT_{reg.student_id}",
                    "event": reg.event_title,
                    "registered": reg.registered,
                    "date": reg.date,
                    "venue": reg.venue
                })
            return {
                "registered_events": my_events
            }
        finally:
            if local_session:
                db.close()

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

    def cancel_registration(self, query: str, student_id: int = 2, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            # Look for active registrations
            regs = db.query(models.EventRegistration).filter(
                models.EventRegistration.student_id == student_id,
                models.EventRegistration.registered == True
            ).all()

            for reg in regs:
                if reg.event_title.lower() in query.lower() or query.lower() in reg.event_title.lower():
                    reg.registered = False
                    db.commit()
                    return {
                        "success": True,
                        "message": "Registration cancelled successfully."
                    }

            return {
                "success": False,
                "message": "No registration found."
            }
        finally:
            if local_session:
                db.close()

    # =============================
    # Register Event
    # =============================

    def register_event(self, query: str, student_id: int = 2, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            events = self.get_events()
            for event in events:
                if event["title"].lower() in query.lower() or query.lower() in event["title"].lower():
                    # Check if already registered
                    existing = db.query(models.EventRegistration).filter(
                        models.EventRegistration.student_id == student_id,
                        models.EventRegistration.event_title == event["title"]
                    ).first()

                    if existing:
                        if existing.registered:
                            return {
                                "success": False,
                                "message": f"You are already registered for {event['title']}."
                            }
                        else:
                            # Re-register
                            existing.registered = True
                            db.commit()
                            return {
                                "success": True,
                                "message": f"Successfully registered for {event['title']}."
                            }

                    # Create new registration record
                    new_reg = models.EventRegistration(
                        student_id=student_id,
                        event_title=event["title"],
                        registered=True,
                        date=event.get("date", ""),
                        venue=event.get("venue", "")
                    )
                    db.add(new_reg)
                    db.commit()

                    return {
                        "success": True,
                        "message": f"Successfully registered for {event['title']}."
                    }

            return {
                "success": False,
                "message": "Event not found."
            }
        finally:
            if local_session:
                db.close()

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

    def get_event_reminders(self, student_id, db: Session = None):
        parsed_student_id = 2
        if isinstance(student_id, int):
            parsed_student_id = student_id
        elif isinstance(student_id, str):
            match = re.search(r'\d+', student_id)
            if match:
                parsed_student_id = int(match.group())
                if parsed_student_id == 1:
                    parsed_student_id = 2

        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            registrations = db.query(models.EventRegistration).filter(
                models.EventRegistration.student_id == parsed_student_id,
                models.EventRegistration.registered == True
            ).all()
            my_events = [r.event_title for r in registrations]
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
        finally:
            if local_session:
                db.close()