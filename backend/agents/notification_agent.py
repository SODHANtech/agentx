import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.database import models

class NotificationAgent:

    def remind(self, query: str, student_id: int = 2, db: Session = None):
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
            new_notif = models.Notification(
                student_id=parsed_student_id,
                query=query,
                status="Pending",
                created_at=datetime.utcnow()
            )
            db.add(new_notif)
            db.commit()
            db.refresh(new_notif)

            return {
                "message": "Reminder created successfully.",
                "reminder": {
                    "id": new_notif.id,
                    "student_id": new_notif.student_id,
                    "query": new_notif.query,
                    "status": new_notif.status,
                    "created_at": new_notif.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(new_notif.created_at, datetime) else str(new_notif.created_at)
                }
            }
        finally:
            if local_session:
                db.close()

    def get_reminders(self, student_id: int = 2, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            notifications = db.query(models.Notification).filter(
                models.Notification.student_id == student_id
            ).all()
            
            results = []
            for n in notifications:
                results.append({
                    "id": n.id,
                    "student_id": n.student_id,
                    "query": n.query,
                    "status": n.status,
                    "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(n.created_at, datetime) else str(n.created_at)
                })
            return results
        finally:
            if local_session:
                db.close()