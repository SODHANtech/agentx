from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from typing import Optional, List
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
    ScheduleAppointmentSchema,
    StudentRequestCreateSchema,
    AdminRequestUpdateSchema,
    AdminEventCreateSchema,
    AdminEventUpdateSchema
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
def get_user_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = db.query(models.Notification).filter(
        models.Notification.recipient_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).all()
    
    results = []
    for n in notifications:
        results.append({
            "id": n.id,
            "title": n.title or "Reminder Alert",
            "message": n.message or n.query,
            "type": n.type or "Reminder",
            "related_type": n.related_type,
            "related_id": n.related_id,
            "read": n.read,
            "created_at": n.created_at.isoformat()
        })
    return results





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
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # RBAC restriction: Only Admin can send notifications
    title = payload.title
    message = payload.message
    audience = payload.audience
    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and Message are required.")
    return communication_agent.send_notification(title, message, audience, db=db)


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
    # Validate MIME type and file extension
    if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Read content to check file size (5MB limit)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the maximum limit of 5MB."
        )

    upload_dir = "backend/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        return resume_agent.analyze_resume(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse or analyze PDF file: {str(e)}"
        )


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


# ==========================================
# System Health & Stats Endpoints
# ==========================================

@router.get("/health")
def health_check(request: Request, db: Session = Depends(get_db)):
    # Check database connection (SQLite)
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Database health check failed: {e}")
        db_status = "disconnected"

    # Compute server uptime
    start_time = getattr(request.app.state, "start_time", time.time())
    uptime = int(time.time() - start_time)

    # Count actual users in the SQLite database
    try:
        total_users = db.query(models.User).count()
        students = db.query(models.User).filter(models.User.role == "Student").count()
        admins = db.query(models.User).filter(models.User.role == "Admin").count()
    except Exception as e:
        print(f"Error querying user counts: {e}")
        total_users, students, admins = 0, 0, 0

    return {
        "backend": "online",
        "database": db_status,
        "uptime": uptime,
        "totalUsers": total_users,
        "students": students,
        "admins": admins
    }


# ==========================================
# Requests Endpoints
# ==========================================

@router.get("/admin/requests")
def get_admin_requests(admin_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    requests = db.query(models.Request).order_by(models.Request.created_at.desc()).all()
    results = []
    for r in requests:
        results.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": r.student.name if r.student else "Unknown",
            "roll_number": r.student.roll_number if r.student else "",
            "department": r.student.department if r.student else "",
            "type": r.type,
            "details": r.details,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        })
    return results

@router.get("/admin/requests/{request_id}")
def get_admin_request_by_id(request_id: int, admin_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Request not found.")
    
    history_logs = []
    for h in r.history:
        history_logs.append({
            "id": h.id,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "changed_by_name": h.changer.name if h.changer else "System",
            "note": h.note,
            "timestamp": h.timestamp.isoformat()
        })

    return {
        "id": r.id,
        "student_id": r.student_id,
        "student_name": r.student.name if r.student else "Unknown",
        "roll_number": r.student.roll_number if r.student else "",
        "department": r.student.department if r.student else "",
        "type": r.type,
        "details": r.details,
        "status": r.status,
        "created_at": r.created_at.isoformat(),
        "history": history_logs
    }

@router.put("/admin/requests/{request_id}")
def update_admin_request(
    request_id: int, 
    payload: AdminRequestUpdateSchema,
    admin_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Request not found.")
    
    prev_status = r.status
    new_status = payload.status
    
    # 1. Update request status
    r.status = new_status
    
    # 2. Append to RequestHistory
    history = models.RequestHistory(
        request_id=r.id,
        previous_status=prev_status,
        new_status=new_status,
        changed_by=admin_user.id,
        note=payload.note
    )
    db.add(history)
    
    # 3. Create Notification for the student recipient
    notif = models.Notification(
        recipient_id=r.student_id,
        title=f"Your {r.type} request has been {new_status.lower()}.",
        message=f"Status update: {new_status}. Note: {payload.note or 'No notes provided by admin.'}",
        type="RequestStatus",
        related_type="Request",
        related_id=r.id,
        # Legacy fields
        student_id=r.student_id,
        query=f"Status update: {new_status}",
        status="Pending"
    )
    db.add(notif)
    
    # 4. Create Admin Audit Log
    prev_val = json.dumps({"status": prev_status})
    new_val = json.dumps({"status": new_status, "note": payload.note})
    
    audit = models.AuditLog(
        admin_id=admin_user.id,
        action=f"{new_status} Request #{r.id}" if new_status in ["Approved", "Rejected"] else f"Updated Request #{r.id} to {new_status}",
        module="Requests",
        target_type="Request",
        target_id=r.id,
        previous_value=prev_val,
        new_value=new_val
    )
    db.add(audit)
    
    db.commit()
    return {"status": "success", "message": f"Request status updated to {new_status}"}

@router.get("/student/requests")
def get_student_requests(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = db.query(models.Request).filter(models.Request.student_id == current_user.id).order_by(models.Request.created_at.desc()).all()
    results = []
    for r in requests:
        results.append({
            "id": r.id,
            "type": r.type,
            "details": r.details,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        })
    return results

@router.post("/student/requests")
def create_student_request(
    payload: StudentRequestCreateSchema,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if current_user.role != "Student":
        raise HTTPException(status_code=403, detail="Operation forbidden: Only students can submit requests.")

    new_req = models.Request(
        student_id=current_user.id,
        type=payload.type,
        details=payload.details,
        status="Pending"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    
    # Add initial RequestHistory
    history = models.RequestHistory(
        request_id=new_req.id,
        previous_status=None,
        new_status="Pending",
        changed_by=current_user.id,
        note="Submitted by Student"
    )
    db.add(history)
    db.commit()

    # Trigger custom notification for all requests
    if "bonafide" in payload.type.lower():
        notif_msg = "ur request to get bonafied is recieved please wait until tommorow for ur request and collect it in administatation office"
    else:
        notif_msg = f"ur request for {payload.type} is recieved please wait until tommorow for ur request"

    notif = models.Notification(
        recipient_id=current_user.id,
        title="Request Received",
        message=notif_msg,
        type="RequestStatus",
        related_type="Request",
        related_id=new_req.id,
        # Legacy fields
        student_id=current_user.id,
        query=notif_msg,
        status="Pending"
    )
    db.add(notif)
    db.commit()
    
    return {
        "id": new_req.id,
        "type": new_req.type,
        "details": new_req.details,
        "status": new_req.status,
        "created_at": new_req.created_at.isoformat()
    }

@router.get("/student/requests/{request_id}/history")
def get_student_request_history(
    request_id: int, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    r = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Request not found.")
    
    if r.student_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Operation forbidden: Access denied to this request's records.")
        
    history_logs = []
    for h in r.history:
        history_logs.append({
            "id": h.id,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "changed_by_name": h.changer.name if h.changer else "System",
            "note": h.note,
            "timestamp": h.timestamp.isoformat()
        })
    return history_logs

# ==========================================
# Unified Events Endpoints
# ==========================================

def serialize_event(e: models.Event):
    return {
        "id": e.id,
        "title": e.title,
        "category": e.category,
        "description": e.description,
        "venue": e.venue,
        "start_datetime": e.start_datetime.isoformat() if e.start_datetime else None,
        "end_datetime": e.end_datetime.isoformat() if e.end_datetime else None,
        "registration_link": e.registration_link,
        "max_participants": e.max_participants,
        "published": e.published,
        "created_by": e.created_by,
        "organizer": e.organizer,
        "department": e.department,
        "banner_poster": e.banner_poster,
        "eligibility": e.eligibility,
        "team_size": e.team_size,
        "prize_pool": e.prize_pool,
        "speaker": e.speaker,
        "date": e.start_datetime.strftime("%Y-%m-%d") if e.start_datetime else "",
        "time": e.start_datetime.strftime("%I:%M %p") if e.start_datetime else "",
        "created_at": e.created_at.isoformat() if e.created_at else None
    }

@router.get("/events")
def get_published_events(
    category: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query_builder = db.query(models.Event).filter(models.Event.published == True)
    if category:
        query_builder = query_builder.filter(models.Event.category.ilike(category))
    
    events = query_builder.order_by(models.Event.start_datetime.asc()).all()
    return [serialize_event(e) for e in events]

@router.get("/events/{event_id}")
def get_single_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return serialize_event(event)

@router.get("/admin/events")
def get_admin_events(
    category: Optional[str] = None,
    admin_user: models.User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    query_builder = db.query(models.Event)
    if category:
        query_builder = query_builder.filter(models.Event.category.ilike(category))
        
    events = query_builder.order_by(models.Event.created_at.desc()).all()
    return [serialize_event(e) for e in events]

@router.post("/admin/events")
def create_admin_event(
    payload: AdminEventCreateSchema,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(models.Event).filter(models.Event.title.ilike(payload.title)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Event with title '{payload.title}' already exists.")
        
    new_event = models.Event(
        title=payload.title,
        category=payload.category,
        description=payload.description,
        venue=payload.venue,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        registration_link=payload.registration_link,
        max_participants=payload.max_participants,
        published=payload.published,
        created_by=admin_user.id,
        organizer=payload.organizer,
        department=payload.department,
        banner_poster=payload.banner_poster,
        eligibility=payload.eligibility,
        team_size=payload.team_size,
        prize_pool=payload.prize_pool,
        speaker=payload.speaker
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    # 1. Create Admin Audit Log
    audit = models.AuditLog(
        admin_id=admin_user.id,
        action=f"Created Event #{new_event.id}",
        module="Events",
        target_type="Event",
        target_id=new_event.id,
        new_value=json.dumps(payload.dict(), default=str)
    )
    db.add(audit)
    
    # 2. If published, notify all students
    if new_event.published:
        students = db.query(models.User).filter(models.User.role == "Student").all()
        for stud in students:
            notif = models.Notification(
                recipient_id=stud.id,
                title=f"New {new_event.category} Published",
                message=f"{new_event.title} is now available.",
                type="NewEvent",
                related_type="Event",
                related_id=new_event.id,
                student_id=stud.id,
                query=f"New event: {new_event.title}",
                status="Pending"
            )
            db.add(notif)
            
    db.commit()
    return serialize_event(new_event)

@router.put("/admin/events/{event_id}")
def update_admin_event(
    event_id: int,
    payload: AdminEventUpdateSchema,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
        
    prev_val = json.dumps({
        "title": event.title,
        "venue": event.venue,
        "start_datetime": event.start_datetime.isoformat() if event.start_datetime else None,
        "published": event.published
    }, default=str)
    
    venue_changed = payload.venue is not None and payload.venue != event.venue
    date_changed = payload.start_datetime is not None and payload.start_datetime != event.start_datetime
    now_published = payload.published is not None and payload.published and not event.published
    
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(event, field, value)
        
    db.commit()
    
    # Audit log
    audit = models.AuditLog(
        admin_id=admin_user.id,
        action=f"Edited Event #{event.id}",
        module="Events",
        target_type="Event",
        target_id=event.id,
        previous_value=prev_val,
        new_value=json.dumps(payload.dict(exclude_unset=True), default=str)
    )
    db.add(audit)
    
    # Notify registered students
    if (venue_changed or date_changed) and event.published:
        registrations = db.query(models.EventRegistration).filter(
            models.EventRegistration.event_id == event.id,
            models.EventRegistration.status == "Registered"
        ).all()
        for r in registrations:
            notif = models.Notification(
                recipient_id=r.student_id,
                title="Event Updated",
                message=f"The details for {event.title} have changed. Venue: {event.venue}.",
                type="EventUpdate",
                related_type="Event",
                related_id=event.id,
                student_id=r.student_id,
                query=f"Updated details: {event.title}",
                status="Pending"
            )
            db.add(notif)
            
    elif now_published:
        students = db.query(models.User).filter(models.User.role == "Student").all()
        for stud in students:
            notif = models.Notification(
                recipient_id=stud.id,
                title=f"New {event.category} Published",
                message=f"{event.title} is now available.",
                type="NewEvent",
                related_type="Event",
                related_id=event.id,
                student_id=stud.id,
                query=f"New event: {event.title}",
                status="Pending"
            )
            db.add(notif)
            
    db.commit()
    return serialize_event(event)

@router.delete("/admin/events/{event_id}")
def delete_admin_event(
    event_id: int,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
        
    audit = models.AuditLog(
        admin_id=admin_user.id,
        action=f"Deleted Event #{event.id}",
        module="Events",
        target_type="Event",
        target_id=event.id,
        previous_value=json.dumps({"title": event.title, "category": event.category})
    )
    db.add(audit)
    
    registrations = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event.id,
        models.EventRegistration.status == "Registered"
    ).all()
    for r in registrations:
        notif = models.Notification(
            recipient_id=r.student_id,
            title="Event Cancelled",
            message=f"The event '{event.title}' has been cancelled by the administration.",
            type="EventUpdate",
            related_type="Event",
            related_id=event.id,
            student_id=r.student_id,
            query=f"Event cancelled: {event.title}",
            status="Pending"
        )
        db.add(notif)
        
    db.delete(event)
    db.commit()
    return {"status": "success", "message": "Event deleted successfully."}

# ==========================================
# Registrations Endpoints
# ==========================================

@router.post("/events/{event_id}/register")
def student_register_event(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "Student":
        raise HTTPException(status_code=403, detail="Operation forbidden: Only students can register for events.")

    event = db.query(models.Event).filter(
        models.Event.id == event_id, 
        models.Event.published == True
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not published.")
        
    existing = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.student_id == current_user.id
    ).first()
    
    if existing:
        if existing.status == "Registered":
            raise HTTPException(status_code=400, detail="You are already registered for this event.")
        else:
            existing.status = "Registered"
            existing.registered_at = datetime.utcnow()
            db.commit()
            return {"status": "success", "message": "Successfully registered."}
            
    new_reg = models.EventRegistration(
        event_id=event_id,
        student_id=current_user.id,
        status="Registered"
    )
    db.add(new_reg)
    db.commit()
    return {"status": "success", "message": "Successfully registered."}

@router.delete("/events/{event_id}/register")
def student_cancel_event_registration(
    event_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reg = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.student_id == current_user.id,
        models.EventRegistration.status == "Registered"
    ).first()
    
    if not reg:
        raise HTTPException(status_code=404, detail="No active registration found for this event.")
        
    reg.status = "Cancelled"
    db.commit()
    return {"status": "success", "message": "Successfully cancelled registration."}

@router.get("/student/event-registrations")
def get_student_event_registrations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    regs = db.query(models.EventRegistration).filter(
        models.EventRegistration.student_id == current_user.id,
        models.EventRegistration.status == "Registered"
    ).all()
    
    results = []
    for r in regs:
        if r.event:
            results.append({
                "id": r.id,
                "event_id": r.event_id,
                "title": r.event.title,
                "category": r.event.category,
                "venue": r.event.venue,
                "date": r.event.start_datetime.strftime("%Y-%m-%d") if r.event.start_datetime else ""
            })
    return results



@router.put("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    n = db.query(models.Notification).filter(
        models.Notification.id == notif_id,
        models.Notification.recipient_id == current_user.id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")
        
    n.read = True
    n.status = "Read"
    db.commit()
    return {"status": "success", "message": "Notification marked as read."}

@router.put("/notifications/read-all")
def mark_all_notifications_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs = db.query(models.Notification).filter(
        models.Notification.recipient_id == current_user.id,
        models.Notification.read == False
    ).all()
    for n in notifs:
        n.read = True
        n.status = "Read"
    db.commit()
    return {"status": "success", "message": "All notifications marked as read."}

# ==========================================
# Audit Logs Endpoints
# ==========================================

@router.get("/admin/audit-logs")
def get_admin_audit_logs(
    admin_id: Optional[int] = None,
    module: Optional[str] = None,
    action: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    admin_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query_builder = db.query(models.AuditLog)
    if admin_id:
        query_builder = query_builder.filter(models.AuditLog.admin_id == admin_id)
    if module:
        query_builder = query_builder.filter(models.AuditLog.module.ilike(module))
    if action:
        query_builder = query_builder.filter(models.AuditLog.action.ilike(f"%{action}%"))
        
    total_count = query_builder.count()
    offset = (page - 1) * limit
    logs = query_builder.order_by(models.AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "admin_id": l.admin_id,
            "admin_name": l.admin.name if l.admin else "Unknown",
            "action": l.action,
            "module": l.module,
            "target_type": l.target_type,
            "target_id": l.target_id,
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "timestamp": l.timestamp.isoformat()
        })
        
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "logs": results
    }

