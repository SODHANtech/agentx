from pydantic import BaseModel, Field
from typing import Optional

# ==========================================
# Authentication Schemas
# ==========================================

class UserRegisterSchema(BaseModel):
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    role: Optional[str] = Field("Student", description="User role (Student | Admin)")
    cgpa: Optional[float] = Field(0.0, description="Cumulative GPA (for Students)")
    backlogs: Optional[int] = Field(0, description="Active backlog count (for Students)")

class UserLoginSchema(BaseModel):
    email: str = Field(..., description="User's registered email")
    password: str = Field(..., description="Account password")

# ==========================================
# Agent & Request Schemas
# ==========================================

class EventRegisterSchema(BaseModel):
    event: str = Field(..., description="The name/title of the event to register for")

class EventCancelSchema(BaseModel):
    event: str = Field(..., description="The name/title of the event to cancel registration for")

class GrievanceSchema(BaseModel):
    category: str = Field("General", description="Grievance category (e.g. Hostel, Library, Transport)")
    description: str = Field(..., description="Detailed description of the grievance")

class DraftEmailSchema(BaseModel):
    recipient: str = Field("Student", description="Email recipient name or category")
    subject: str = Field("Campus Update", description="Subject line of the email draft")
    purpose: str = Field("General Query", description="Detailed purpose of the email")

class SendNotificationSchema(BaseModel):
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Detailed notification message content")
    audience: str = Field("All Students", description="Target audience group for the notification")

class CreateAnnouncementSchema(BaseModel):
    title: str = Field(..., description="Announcement title")
    content: str = Field(..., description="Detailed content of the announcement")
    category: str = Field("General", description="Announcement category (e.g., Academic, Placement, General)")

class ScheduleAppointmentSchema(BaseModel):
    officer: str = Field("Academic Advisor", description="The campus officer to meet with")
    date: str = Field(..., description="Target date of the appointment (YYYY-MM-DD)")
    time_slot: str = Field("10:00 AM", description="Target time slot of the appointment")
    reason: str = Field("Academic Discussion", description="The reason for scheduling the meeting")

# ==========================================
# Phase 2 Request & Unified Event Schemas
# ==========================================
from datetime import datetime

class StudentRequestCreateSchema(BaseModel):
    type: str = Field(..., description="Type of request, e.g. Bonafide Certificate, Leave Request")
    details: str = Field(..., description="Description / context details for the request")

class AdminRequestUpdateSchema(BaseModel):
    status: str = Field(..., description="New status: Pending | Under Review | Approved | Rejected | Completed")
    note: Optional[str] = Field(None, description="Explanation or rejection reason")

class AdminEventCreateSchema(BaseModel):
    title: str = Field(..., description="Event title")
    category: str = Field(..., description="Category, e.g. Event, Hackathon, Seminar, Workshop, Competition")
    description: str = Field(..., description="Event description")
    venue: str = Field(..., description="Venue location")
    start_datetime: datetime = Field(..., description="Start date & time")
    end_datetime: datetime = Field(..., description="End date & time")
    registration_link: Optional[str] = Field(None)
    max_participants: Optional[int] = Field(0)
    published: Optional[bool] = Field(False)
    organizer: Optional[str] = Field(None)
    department: Optional[str] = Field(None)
    banner_poster: Optional[str] = Field(None)
    eligibility: Optional[str] = Field(None)
    team_size: Optional[int] = Field(None)
    prize_pool: Optional[str] = Field(None)
    speaker: Optional[str] = Field(None)

class AdminEventUpdateSchema(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    venue: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    registration_link: Optional[str] = None
    max_participants: Optional[int] = None
    published: Optional[bool] = None
    organizer: Optional[str] = None
    department: Optional[str] = None
    banner_poster: Optional[str] = None
    eligibility: Optional[str] = None
    team_size: Optional[int] = None
    prize_pool: Optional[str] = None
    speaker: Optional[str] = None

