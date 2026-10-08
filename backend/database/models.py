from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="Student")  # "Student" | "Admin"
    status = Column(String, default="Active")  # "Active" | "Suspended"
    cgpa = Column(Float, default=0.0)
    backlogs = Column(Integer, default=0)
    roll_number = Column(String, nullable=True)  # New for Phase 2
    department = Column(String, nullable=True)   # New for Phase 2
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="student")
    requests = relationship("Request", back_populates="student")
    registrations = relationship("EventRegistration", back_populates="student", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="recipient", foreign_keys="[Notification.recipient_id]", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="admin", cascade="all, delete-orphan")

class ComplaintCluster(Base):
    __tablename__ = "complaint_clusters"

    id = Column(Integer, primary_key=True, index=True)
    ai_title = Column(String, nullable=False)
    ai_brief = Column(String, nullable=False)
    status = Column(String, default="Active")  # "Active" | "Broadcasted"
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="cluster")

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="Pending")  # "Pending" | "Clustered" | "Resolved"
    cluster_id = Column(Integer, ForeignKey("complaint_clusters.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="complaints")
    cluster = relationship("ComplaintCluster", back_populates="complaints")

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(String, nullable=False)  # "Bonafide" | "Leave" | "Doubt"
    details = Column(String, nullable=False)
    status = Column(String, default="Pending")  # "Pending" | "Under Review" | "Approved" | "Rejected" | "Completed"
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="requests")
    history = relationship("RequestHistory", back_populates="request", cascade="all, delete-orphan")

class RequestHistory(Base):
    __tablename__ = "request_histories"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), index=True, nullable=False)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    request = relationship("Request", back_populates="history")
    changer = relationship("User")

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, default="General")  # "General" | "Academic" | "Placement"
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)  # "Event" | "Hackathon" | "Seminar" | "Workshop" | "Competition" | "Guest Lecture"
    description = Column(String, nullable=False)
    venue = Column(String, nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    registration_link = Column(String, nullable=True)
    max_participants = Column(Integer, default=0)
    published = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional / Category-specific fields
    organizer = Column(String, nullable=True)
    department = Column(String, nullable=True)
    banner_poster = Column(String, nullable=True)
    eligibility = Column(String, nullable=True)
    team_size = Column(Integer, nullable=True)
    prize_pool = Column(String, nullable=True)
    speaker = Column(String, nullable=True)

    creator = relationship("User")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")

class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Registered")  # "Registered" | "Cancelled"

    __table_args__ = (
        UniqueConstraint("event_id", "student_id", name="uq_event_registration"),
    )

    student = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    officer = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time_slot = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="Confirmed")
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "RequestStatus" | "NewEvent" | "EventUpdate" | "RegistrationClosing" | "Reminder"
    related_type = Column(String, nullable=True)  # "Request" | "Event"
    related_id = Column(Integer, nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Legacy fields kept for backward compatibility (reminders, etc.)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(String, nullable=True)
    status = Column(String, default="Pending")

    recipient = relationship("User", back_populates="notifications", foreign_keys=[recipient_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    action = Column(String, nullable=False)
    module = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(Integer, nullable=False)
    previous_value = Column(String, nullable=True)  # JSON or text
    new_value = Column(String, nullable=True)       # JSON or text
    timestamp = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User", back_populates="audit_logs")
