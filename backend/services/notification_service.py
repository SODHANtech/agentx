from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database import models

class NotificationService:
    @staticmethod
    def get_user_notifications(db: Session, user_id: int) -> List[models.Notification]:
        return db.query(models.Notification).filter(
            models.Notification.recipient_id == user_id
        ).order_by(models.Notification.created_at.desc()).all()

    @staticmethod
    def create_notification(
        db: Session, 
        recipient_id: int, 
        title: str, 
        message: str, 
        type_: str, 
        related_type: Optional[str] = None, 
        related_id: Optional[int] = None
    ) -> models.Notification:
        notif = models.Notification(
            recipient_id=recipient_id,
            title=title,
            message=message,
            type=type_,
            related_type=related_type,
            related_id=related_id,
            # Legacy compatibility fields
            student_id=recipient_id,
            query=message,
            status="Pending"
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[models.Notification]:
        notif = db.query(models.Notification).filter(
            models.Notification.id == notification_id,
            models.Notification.recipient_id == user_id
        ).first()
        if notif:
            notif.read = True
            db.commit()
        return notif

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int):
        unreads = db.query(models.Notification).filter(
            models.Notification.recipient_id == user_id,
            models.Notification.read == False
        ).all()
        for n in unreads:
            n.read = True
        db.commit()
        return len(unreads)
