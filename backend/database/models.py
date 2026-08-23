from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
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
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="student")
    requests = relationship("Request", back_populates="student")

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
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # "Bonafide" | "Leave" | "Doubt"
    details = Column(String, nullable=False)
    status = Column(String, default="Pending")  # "Pending" | "Approved" | "Rejected"
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="requests")

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, default="General")  # "General" | "Academic" | "Placement"
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_title = Column(String, nullable=False, index=True)
    registered = Column(Boolean, default=True)
    date = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(String, nullable=False)
    status = Column(String, default="Pending")  # "Pending" | "Read"
    created_at = Column(DateTime, default=datetime.utcnow)

