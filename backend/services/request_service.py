import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.database import models

class RequestService:
    @staticmethod
    def get_request_by_id(db: Session, request_id: int) -> Optional[models.Request]:
        return db.query(models.Request).filter(models.Request.id == request_id).first()

    @staticmethod
    def get_student_requests(db: Session, student_id: int) -> List[models.Request]:
        return db.query(models.Request).filter(models.Request.student_id == student_id).order_by(models.Request.created_at.desc()).all()

    @staticmethod
    def get_all_requests(db: Session, category: Optional[str] = None) -> List[models.Request]:
        query = db.query(models.Request)
        if category:
            query = query.filter(models.Request.type.ilike(category))
        return query.order_by(models.Request.created_at.desc()).all()

    @staticmethod
    def create_student_request(db: Session, student_id: int, request_type: str, details: str) -> models.Request:
        new_request = models.Request(
            student_id=student_id,
            type=request_type,
            details=details,
            status="Pending"
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        # 1. Append history log
        history = models.RequestHistory(
            request_id=new_request.id,
            previous_status=None,
            new_status="Pending",
            changed_by=student_id,
            note="Request submitted by student"
        )
        db.add(history)

        # 2. Trigger student notification
        notif = models.Notification(
            recipient_id=student_id,
            title=f"New {request_type} request filed",
            message=f"Your request of type '{request_type}' has been successfully filed and is pending review.",
            type="RequestStatus",
            related_type="Request",
            related_id=new_request.id,
            student_id=student_id,
            query=f"Created request: {request_type}",
            status="Pending"
        )
        db.add(notif)
        db.commit()

        return new_request

    @staticmethod
    def update_request_status(
        db: Session, 
        request_id: int, 
        new_status: str, 
        note: Optional[str], 
        admin_id: int
    ) -> Tuple[models.Request, models.Notification]:
        r = db.query(models.Request).filter(models.Request.id == request_id).first()
        if not r:
            return None, None

        prev_status = r.status

        # State Machine Transition Validation
        valid_transitions = {
            "Pending": ["Under Review", "Approved", "Rejected"],
            "Under Review": ["Approved", "Rejected"],
            "Approved": ["Completed"],
            "Rejected": [],
            "Completed": []
        }

        # Validate transition if not a no-op status update
        if prev_status != new_status:
            allowed = valid_transitions.get(prev_status, [])
            if new_status not in allowed:
                raise ValueError(f"Invalid state transition from '{prev_status}' to '{new_status}'")

        # 1. Update status
        r.status = new_status

        # 2. Append history log
        history = models.RequestHistory(
            request_id=r.id,
            previous_status=prev_status,
            new_status=new_status,
            changed_by=admin_id,
            note=note
        )
        db.add(history)

        # 3. Create Notification for the student
        notif = models.Notification(
            recipient_id=r.student_id,
            title=f"Your {r.type} request has been {new_status.lower()}.",
            message=f"Status update: {new_status}. Note: {note or 'No notes provided by admin.'}",
            type="RequestStatus",
            related_type="Request",
            related_id=r.id,
            student_id=r.student_id,
            query=f"Status update: {new_status}",
            status="Pending"
        )
        db.add(notif)

        # 4. Create Audit Log
        prev_val = json.dumps({"status": prev_status})
        new_val = json.dumps({"status": new_status, "note": note})

        audit = models.AuditLog(
            admin_id=admin_id,
            action=f"{new_status} Request #{r.id}" if new_status in ["Approved", "Rejected"] else f"Updated Request #{r.id} to {new_status}",
            module="Requests",
            target_type="Request",
            target_id=r.id,
            previous_value=prev_val,
            new_value=new_val
        )
        db.add(audit)

        db.commit()
        db.refresh(notif)
        return r, notif
