import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.database import models

class CommunicationAgent:

    # =============================
    # Data Loaders / Announcements
    # =============================

    def get_announcements(self, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            announcements = db.query(models.Announcement).order_by(models.Announcement.created_at.desc()).all()
            results = []
            for ann in announcements:
                results.append({
                    "id": f"ANN_{ann.id:03d}",
                    "title": ann.title,
                    "content": ann.description,
                    "category": ann.category,
                    "date": ann.created_at.strftime("%Y-%m-%d") if ann.created_at else "2026-08-23"
                })
            return results
        finally:
            if local_session:
                db.close()

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

    def send_notification(self, title: str, message: str, target_audience: str = "All Students", db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            # Create a notification for each student
            students = db.query(models.User).filter(models.User.role == "Student").all()
            for student in students:
                new_notif = models.Notification(
                    student_id=student.id,
                    query=f"Broadcast: {title} - {message}",
                    status="Pending"
                )
                db.add(new_notif)
            db.commit()
            
            notification_entry = {
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
        finally:
            if local_session:
                db.close()

    # =============================
    # 3. Generate Announcements
    # =============================

    def create_announcement(self, title: str, content: str, category: str = "General", author_id: int = 1, db: Session = None):
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            new_ann = models.Announcement(
                title=title,
                description=content,
                category=category,
                author_id=author_id
            )
            db.add(new_ann)
            db.commit()
            db.refresh(new_ann)

            return {
                "success": True,
                "message": "Announcement published successfully!",
                "announcement": {
                    "id": f"ANN_{new_ann.id:03d}",
                    "title": new_ann.title,
                    "content": new_ann.description,
                    "category": new_ann.category,
                    "date": new_ann.created_at.strftime("%Y-%m-%d") if new_ann.created_at else "2026-08-23"
                }
            }
        finally:
            if local_session:
                db.close()

    # =============================
    # 4. Appointment Scheduling
    # =============================

    def schedule_appointment(self, student_id, officer: str, date: str, time_slot: str, reason: str, db: Session = None):
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
            new_appointment = models.Appointment(
                student_id=parsed_student_id,
                officer=officer,
                date=date,
                time_slot=time_slot,
                reason=reason,
                status="Confirmed"
            )
            db.add(new_appointment)
            db.commit()
            db.refresh(new_appointment)

            return {
                "success": True,
                "message": f"Appointment booked with {officer} on {date} at {time_slot}.",
                "appointment": {
                    "id": f"APT_{new_appointment.id:03d}",
                    "student_id": f"STUDENT_{new_appointment.student_id}",
                    "officer": new_appointment.officer,
                    "date": new_appointment.date,
                    "time_slot": new_appointment.time_slot,
                    "reason": new_appointment.reason,
                    "status": new_appointment.status
                }
            }
        finally:
            if local_session:
                db.close()