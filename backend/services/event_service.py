import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.database import models

class EventService:
    @staticmethod
    def get_event_by_id(db: Session, event_id: int) -> Optional[models.Event]:
        return db.query(models.Event).filter(models.Event.id == event_id).first()

    @staticmethod
    def get_published_events(db: Session, category: Optional[str] = None) -> List[models.Event]:
        query = db.query(models.Event).filter(models.Event.published == True)
        if category:
            query = query.filter(models.Event.category.ilike(category))
        return query.order_by(models.Event.start_datetime.asc()).all()

    @staticmethod
    def get_admin_events(db: Session, category: Optional[str] = None) -> List[models.Event]:
        query = db.query(models.Event)
        if category:
            query = query.filter(models.Event.category.ilike(category))
        return query.order_by(models.Event.created_at.desc()).all()

    @staticmethod
    def create_event(db: Session, payload, admin_id: int) -> models.Event:
        new_event = models.Event(
            title=payload.title,
            category=payload.category,
            description=payload.description,
            venue=payload.venue,
            start_datetime=payload.start_datetime,
            end_datetime=payload.end_datetime,
            registration_link=payload.registration_link,
            max_participants=payload.max_participants,
            published=payload.published,
            created_by=admin_id,
            organizer=payload.organizer,
            department=payload.department,
            banner_poster=payload.banner_poster,
            eligibility=payload.eligibility,
            team_size=payload.team_size,
            prize_pool=payload.prize_pool,
            speaker=payload.speaker
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        # 1. Create Audit Log
        audit = models.AuditLog(
            admin_id=admin_id,
            action=f"Created Event #{new_event.id}",
            module="Events",
            target_type="Event",
            target_id=new_event.id,
            new_value=json.dumps(payload.dict(), default=str)
        )
        db.add(audit)

        # 2. Notify students if published on creation
        if new_event.published:
            students = db.query(models.User).filter(models.User.role == "Student").all()
            for stud in students:
                notif = models.Notification(
                    recipient_id=stud.id,
                    title=f"New {new_event.category} Published",
                    message=f"{new_event.title} is now available.",
                    type="NewEvent",
                    related_type="Event",
                    related_id=new_event.id,
                    student_id=stud.id,
                    query=f"New event: {new_event.title}",
                    status="Pending"
                )
                db.add(notif)
        db.commit()
        return new_event

    @staticmethod
    def update_event(db: Session, event_id: int, payload, admin_id: int) -> Tuple[Optional[models.Event], bool, bool, bool]:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        if not event:
            return None, False, False, False

        prev_val = json.dumps({
            "title": event.title,
            "venue": event.venue,
            "start_datetime": event.start_datetime.isoformat() if event.start_datetime else None,
            "published": event.published
        }, default=str)

        venue_changed = payload.venue is not None and payload.venue != event.venue
        date_changed = payload.start_datetime is not None and payload.start_datetime != event.start_datetime
        now_published = payload.published is not None and payload.published and not event.published

        for field, value in payload.dict(exclude_unset=True).items():
            setattr(event, field, value)

        # Update Audit Log
        audit = models.AuditLog(
            admin_id=admin_id,
            action=f"Updated Event #{event.id}",
            module="Events",
            target_type="Event",
            target_id=event.id,
            previous_value=prev_val,
            new_value=json.dumps(payload.dict(exclude_unset=True), default=str)
        )
        db.add(audit)
        db.commit()
        return event, venue_changed, date_changed, now_published

    @staticmethod
    def delete_event(db: Session, event_id: int, admin_id: int) -> Optional[models.Event]:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        if not event:
            return None

        # Create Audit Log
        audit = models.AuditLog(
            admin_id=admin_id,
            action=f"Deleted Event #{event.id} ({event.title})",
            module="Events",
            target_type="Event",
            target_id=event.id,
            previous_value=json.dumps({"title": event.title, "category": event.category})
        )
        db.add(audit)
        db.delete(event)
        db.commit()
        return event
