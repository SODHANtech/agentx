from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends, Header
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
import json
import os

from backend.graph import graph
from backend.database.session import get_db
from backend.database import models
from backend.core.security import hash_password, verify_password, create_jwt, verify_jwt
from backend.api.schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    EventRegisterSchema,
    EventCancelSchema,
    GrievanceSchema,
    DraftEmailSchema,
    SendNotificationSchema,
    CreateAnnouncementSchema,
    ScheduleAppointmentSchema
)

from backend.agents.academic_agent import AcademicAgent
from backend.agents.placement_agent import PlacementAgent
from backend.agents.dashboard_agent import DashboardAgent
from backend.agents.events_agent import EventsAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.communications_agent import CommunicationAgent
from backend.agents.student_services_agent import StudentServicesAgent
from backend.agents.complaint_analyst import ComplaintAnalyst

router = APIRouter()

# Instantiate agents
academic_agent = AcademicAgent()
placement_agent = PlacementAgent()
dashboard = DashboardAgent()
events_agent = EventsAgent()
resume_agent = ResumeAgent()
communication_agent = CommunicationAgent()
student_services_agent = StudentServicesAgent()
complaint_analyst = ComplaintAnalyst()

# ==========================================
# Authentication Dependencies (RBAC)
# ==========================================

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authentication token. Prefix token with 'Bearer '."
        )
    token = authorization.split(" ")[1]
    payload = verify_jwt(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=401,
            detail="Token is invalid or has expired."
        )
    user = db.query(models.User).filter(models.User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user account not found."
        )
    return user

def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Operation forbidden: Administrator role required."
        )
    return current_user

# ==========================================
# Auth Endpoints
# ==========================================

@router.post("/auth/register")
def register(payload: UserRegisterSchema, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Account with this email already exists."
        )
    
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
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role
        }
    }

@router.post("/auth/login")
def login(payload: UserLoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )
    
    token = create_jwt({
        "sub": user.id,
        "name": user.name,
        "role": user.role
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "cgpa": user.cgpa,
            "backlogs": user.backlogs
        }
    }

@router.get("/auth/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "cgpa": current_user.cgpa,
        "backlogs": current_user.backlogs,
        "status": current_user.status
    }

# -------------------- General / Ask --------------------

@router.get("/")
def home():
    return {
        "message": "Smart Campus AI Backend Running"
    }


@router.get("/ask")
def ask(
    query: str, 
    session_id: str = "default", 
    current_user: models.User = Depends(get_current_user)
):
    try:
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }

        # Invoke the LangGraph workflow with empty trace logs in state input and inject student_id
        response_state = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=query)
                ],
                "agent_steps": [],
                "student_id": current_user.id
            },
            config=config
        )

        last_message = response_state["messages"][-1].content
        agent_steps = response_state.get("agent_steps", [])

        # Format output message string based on structured sub-agent payloads
        response_text = ""
        try:
            data = json.loads(last_message)
            
            # Map specific agent outputs to readable text responses
            answers = []
            if "academic" in data:
                classes = data["academic"]
                if isinstance(classes, list):
                    class_details = "; ".join([f"{c['subject']} in {c['classroom']} ({c['time']})" for c in classes])
                    answers.append(f"Timetable Classes: {class_details}")
                else:
                    answers.append(classes.get("message", "No classes found."))
            if "academic_quiz" in data:
                quiz_data = data["academic_quiz"]
                q_text = quiz_data.get("explanation", "")
                questions = quiz_data.get("quiz", [])
                if questions:
                    q_text += "\n\nPractice Quiz:\n"
                    for i, q in enumerate(questions, 1):
                        options = "\n".join([f"  {j}. {opt}" for j, opt in enumerate(q.get("options", []), 1)])
                        q_text += f"Q{i}: {q.get('question')}\n{options}\n"
                answers.append(q_text)
            if "placement" in data:
                p_res = data["placement"]
                answers.append(f"Placement Status: Student is {p_res.get('status', 'not eligible')} for {p_res.get('company', 'selected company')}.")
            if "knowledge" in data:
                answers.append(data["knowledge"].get("answer", ""))
            if "notification" in data:
                answers.append(data["notification"].get("message", ""))
            if "events" in data:
                evts = data["events"]
                if isinstance(evts, list) and evts:
                    evt_names = ", ".join([e["title"] for e in evts])
                    answers.append(f"Upcoming Events: {evt_names}")
                else:
                    answers.append("No matching campus events found.")
            if "student_services" in data:
                srvs = data["student_services"]
                if isinstance(srvs, list) and srvs:
                    srv_names = ", ".join([s["service"] for s in srvs])
                    answers.append(f"Matching Services: {srv_names}")
                else:
                    answers.append(srvs.get("message", "No student services found."))
            
            response_text = "\n".join(answers)
            
            if not response_text:
                if "response" in data:
                    response_text = data["response"]
                else:
                    response_text = str(last_message)
            
            if response_text == "{}":
                response_text = "I received your query. However, no specialized campus agents matched the request. How else can I assist you today?"
        except Exception:
            response_text = str(last_message)

        return {
            "response": response_text,
            "agent_steps": agent_steps,
            "status": "success"
        }

    except Exception as e:
        print(f"Error in /ask route: {e}")
        return {
            "response": f"Processed query: '{query}'. Here is the information retrieved for your request.",
            "agent_steps": [
                {
                    "id": "supervisor",
                    "name": "Supervisor Agent",
                    "status": "completed",
                    "detail": "Failed to complete processing due to internal error."
                }
            ],
            "status": "error"
        }


@router.get("/dashboard")
def dashboard_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dashboard_res = dashboard.get_dashboard(student_id=current_user.id, db=db)
    dashboard_res["student"] = {
        "name": current_user.name,
        "cgpa": current_user.cgpa,
        "backlogs": current_user.backlogs
    }
    return dashboard_res


@router.get("/notifications")
def notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    base_notifications = dashboard.get_dashboard(student_id=current_user.id, db=db).get("notifications", [])
    event_reminders = events_agent.get_event_reminders(current_user.id, db=db)
    return base_notifications + event_reminders


@router.get("/events")
def get_events(current_user: models.User = Depends(get_current_user)):
    return events_agent.get_events()


@router.get("/classes/{day}")
def get_classes(day: str, current_user: models.User = Depends(get_current_user)):
    return academic_agent.get_today_classes(day)


# -------------------- Event Registration --------------------

@router.post("/events/register")
def register_event(
    payload: EventRegisterSchema, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event_name = payload.event
    if not event_name:
        raise HTTPException(
            status_code=400,
            detail="Event name is required."
        )
    return events_agent.register_event(event_name, student_id=current_user.id, db=db)


@router.post("/events/cancel")
def cancel_event(
    payload: EventCancelSchema, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event_name = payload.event
    if not event_name:
        raise HTTPException(
            status_code=400,
            detail="Event name is required."
        )
    return events_agent.cancel_registration(event_name, student_id=current_user.id, db=db)


@router.get("/events/registrations")
def registrations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return events_agent.get_registered_events(student_id=current_user.id, db=db)


# -------------------- Calendar Export --------------------

@router.get("/events/export/{event_title}")
def export_event_calendar(
    event_title: str, 
    current_user: models.User = Depends(get_current_user)
):
    ics_data = events_agent.generate_ics(event_title)
    if not ics_data:
        raise HTTPException(status_code=404, detail="Event not found.")

    return Response(
        content=ics_data,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={event_title.replace(' ', '_')}.ics"
        }
    )


# -------------------- Placement --------------------

@router.get("/placement/{company}")
def check_placement(company: str, current_user: models.User = Depends(get_current_user)):
    # Deterministic query using active database user credentials
    student_profile = {
        "cgpa": current_user.cgpa,
        "backlogs": current_user.backlogs
    }
    # Load company matching logic dynamically
    res = placement_agent.check_eligibility(company)
    # Re-evaluate eligibility based on the REAL logged-in student user data
    if res.get("status"):
        comp_obj = next((c for c in placement_agent.get_companies() if c["company"].lower() == company.lower()), None)
        if comp_obj:
            if student_profile["cgpa"] >= comp_obj["cgpa"] and student_profile["backlogs"] <= comp_obj["backlogs"]:
                return {"status": "Eligible", "company": comp_obj["company"]}
            else:
                return {"status": "Not Eligible", "company": comp_obj["company"]}
    return res


# -------------------- Student Services --------------------

@router.get("/student-services")
def get_all_services(current_user: models.User = Depends(get_current_user)):
    return student_services_agent.get_services()


@router.get("/student-services/hostel")
def get_hostels(current_user: models.User = Depends(get_current_user)):
    return student_services_agent.get_hostels()


@router.get("/student-services/library")
def get_library(current_user: models.User = Depends(get_current_user)):
    return student_services_agent.get_library()


@router.get("/student-services/scholarships")
def get_scholarships(current_user: models.User = Depends(get_current_user)):
    return student_services_agent.get_scholarships()


@router.get("/student-services/transport")
def get_transport(current_user: models.User = Depends(get_current_user)):
    return student_services_agent.get_transport()


@router.get("/student-services/search")
def search_services(query: str, current_user: models.User = Depends(get_current_user)):
    return student_services_agent.search_services(query)


@router.post("/student-services/grievance")
def post_grievance(
    payload: GrievanceSchema, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = payload.category
    description = payload.description
    if not description:
        raise HTTPException(status_code=400, detail="Description is required.")
    return student_services_agent.file_grievance(current_user.id, category, description, db=db)


# -------------------- Communication (Admin Protected) --------------------

@router.get("/communications")
def get_communications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return communication_agent.get_announcements(db=db)


@router.post("/communications/draft-email")
def draft_email(
    payload: DraftEmailSchema, 
    current_user: models.User = Depends(get_current_user)
):
    recipient = payload.recipient
    subject = payload.subject
    purpose = payload.purpose
    return communication_agent.draft_email(recipient, subject, purpose)


@router.post("/communications/notify")
def send_notification(
    payload: SendNotificationSchema, 
    admin_user: models.User = Depends(require_admin)
):
    # RBAC restriction: Only Admin can send notifications
    title = payload.title
    message = payload.message
    audience = payload.audience
    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and Message are required.")
    return communication_agent.send_notification(title, message, audience)


@router.post("/communications/announcement")
def post_announcement(
    payload: CreateAnnouncementSchema, 
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # RBAC restriction: Only Admin can post announcements
    title = payload.title
    content = payload.content
    category = payload.category
    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and Content are required.")
    return communication_agent.create_announcement(title, content, category, author_id=admin_user.id, db=db)


@router.post("/communications/schedule-appointment")
def schedule_appointment(
    payload: ScheduleAppointmentSchema, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    officer = payload.officer
    date = payload.date
    time_slot = payload.time_slot
    reason = payload.reason
    return communication_agent.schedule_appointment(current_user.id, officer, date, time_slot, reason, db=db)


# -------------------- Resume --------------------

@router.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user)
):
    upload_dir = "backend/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return resume_agent.analyze_resume(file_path)


# -------------------- Admin AI Complaint Intelligence --------------------

@router.post("/admin/complaints/cluster")
def trigger_clustering(
    admin_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    clusters = complaint_analyst.cluster_complaints(db)
    return {
        "status": "success",
        "message": f"Successfully completed semantic analysis. Grouped complaints into {len(clusters)} systemic issue clusters.",
        "clusters": [
            {
                "id": c.id,
                "title": c.ai_title,
                "brief": c.ai_brief,
                "status": c.status
            } for c in clusters
        ]
    }


@router.get("/admin/clusters")
def get_clusters(
    admin_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    clusters = db.query(models.ComplaintCluster).all()
    res = []
    for c in clusters:
        complaints = db.query(models.Complaint).filter(models.Complaint.cluster_id == c.id).all()
        res.append({
            "id": c.id,
            "title": c.ai_title,
            "brief": c.ai_brief,
            "status": c.status,
            "complaints": [
                {
                    "id": comp.id,
                    "department": comp.department,
                    "description": comp.description,
                    "status": comp.status
                } for comp in complaints
            ]
        })
    return res


@router.post("/admin/clusters/{cluster_id}/broadcast")
def broadcast_resolution(
    cluster_id: int, 
    admin_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    cluster = db.query(models.ComplaintCluster).filter(models.ComplaintCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Complaint cluster not found.")
    
    # Update cluster state
    cluster.status = "Broadcasted"
    
    # Resolve all complaints in this cluster
    complaints = db.query(models.Complaint).filter(models.Complaint.cluster_id == cluster_id).all()
    for comp in complaints:
        comp.status = "Resolved"
        
    # Write a new announcement resolution notice
    new_announcement = models.Announcement(
        title=f"CampusOS Resolution: {cluster.ai_title}",
        description=f"Administrative Action: The reported issue '{cluster.ai_title}' has been fixed. Brief: {cluster.ai_brief}",
        category="General",
        author_id=admin_user.id
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    
    return {
        "status": "success",
        "message": f"Broadcasted resolution for cluster: {cluster.ai_title}",
        "announcement_id": new_announcement.id
    }
