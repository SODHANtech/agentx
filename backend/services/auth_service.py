from sqlalchemy.orm import Session
from backend.database import models
from backend.core.security import hash_password, verify_password

class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> models.User:
        return db.query(models.User).filter(models.User.email == email).first()

    @staticmethod
    def register_student(db: Session, payload) -> models.User:
        new_user = models.User(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role="Student",
            cgpa=payload.cgpa,
            backlogs=payload.backlogs
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, payload) -> models.User:
        user = db.query(models.User).filter(models.User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.password_hash):
            return None
        return user
