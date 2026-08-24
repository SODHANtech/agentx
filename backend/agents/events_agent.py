import json
import re
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.database import models

class EventsAgent:

    # =============================
    # Load Data (Dynamic SQLite Query)
    # =============================

    def get_events(self, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            # Fetch published events
            db_events = db.query(models.Event).filter(models.Event.published == True).all()
            results = []
            for e in db_events:
                # Convert to legacy JSON format for compatibility
                results.append({
                    "id": e.id,
                    "title": e.title,
                    "category": e.category,
                    "description": e.description,
                    "date": e.start_datetime.strftime("%Y-%m-%d") if e.start_datetime else "",
                    "time": e.start_datetime.strftime("%I:%M %p") if e.start_datetime else "",
                    "venue": e.venue,
                    "registration_link": e.registration_link,
                    "max_participants": e.max_participants,
                    "organizer": e.organizer,
                    "department": e.department,
                    "banner_poster": e.banner_poster,
                    "eligibility": e.eligibility,
                    "team_size": e.team_size,
                    "prize_pool": e.prize_pool,
                    "speaker": e.speaker
                })
            return results
        finally:
            if local_session:
                db.close()

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
                models.EventRegistration.status == "Registered"
            ).all()
            my_events = []
            for reg in registrations:
                if reg.event:
                    my_events.append({
                        "student_id": f"STUDENT_{reg.student_id}",
                        "event": reg.event.title,
                        "registered": True,
                        "date": reg.event.start_datetime.strftime("%Y-%m-%d") if reg.event.start_datetime else "",
                        "venue": reg.event.venue
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
                + event.get("category", "")
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
    # Register Event
    # =============================

    def register_event(self, query: str, student_id: int = 2, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            # Query active events directly from DB to find match
            db_events = db.query(models.Event).filter(models.Event.published == True).all()
            for event in db_events:
                if event.title.lower() in query.lower() or query.lower() in event.title.lower():
                    # Check if already registered
                    existing = db.query(models.EventRegistration).filter(
                        models.EventRegistration.student_id == student_id,
                        models.EventRegistration.event_id == event.id
                    ).first()

                    if existing:
                        if existing.status == "Registered":
                            return {
                                "success": False,
                                "message": f"You are already registered for {event.title}."
                            }
                        else:
                            # Re-register
                            existing.status = "Registered"
                            existing.registered_at = datetime.utcnow()
                            db.commit()
                            return {
                                "success": True,
                                "message": f"Successfully registered for {event.title}."
                            }

                    # Create new registration record (no duplicated event columns!)
                    new_reg = models.EventRegistration(
                        student_id=student_id,
                        event_id=event.id,
                        status="Registered",
                        registered_at=datetime.utcnow()
                    )
                    db.add(new_reg)
                    db.commit()

                    return {
                        "success": True,
                        "message": f"Successfully registered for {event.title}."
                    }

            return {
                "success": False,
                "message": "Event not found."
            }
        finally:
            if local_session:
                db.close()

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
                models.EventRegistration.status == "Registered"
            ).all()

            for reg in regs:
                if reg.event and (reg.event.title.lower() in query.lower() or query.lower() in reg.event.title.lower()):
                    reg.status = "Cancelled"
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
                models.EventRegistration.status == "Registered"
            ).all()

            reminders = []
            for r in registrations:
                if r.event:
                    evt_date = r.event.start_datetime.strftime("%Y-%m-%d") if r.event.start_datetime else ""
                    reminders.append({
                        "id": f"rem_{r.event.title}",
                        "title": f"Upcoming Event: {r.event.title}",
                        "message": f"You are registered for {r.event.title} on {evt_date} at {r.event.venue}.",
                        "type": "event_reminder",
                        "date": evt_date
                    })
            return reminders
        finally:
            if local_session:
                db.close()