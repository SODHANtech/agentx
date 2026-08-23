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
