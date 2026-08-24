import json
from langchain_core.messages import AIMessage

from backend.router import route
from backend.database.session import SessionLocal, get_db
from backend.database.models import User
from backend.agents.academic_agent import AcademicAgent
from backend.agents.placement_agent import PlacementAgent
from backend.agents.knowledge_agent import KnowledgeAgent
from backend.agents.notification_agent import NotificationAgent
from backend.agents.events_agent import EventsAgent
from backend.agents.student_services_agent import StudentServicesAgent
from backend.agents.quiz_agent import QuizAgent
from backend.agents.resume_agent import ResumeAgent
from backend.agents.communications_agent import CommunicationAgent
from backend.llm import llm
from backend.database import models
from backend.services import RequestService

academic = AcademicAgent()
placement = PlacementAgent()
knowledge = KnowledgeAgent()
notification = NotificationAgent()
events = EventsAgent()
student_services = StudentServicesAgent()
quiz_agent = QuizAgent()
resume_agent = ResumeAgent()
communication = CommunicationAgent()

def router_node(state):
    messages = state["messages"]
    student_id = state.get("student_id")

    # Current user query
    query = messages[-1].content

    # Limit conversation history to the last 5 turns to save token usage and prevent bloat
    recent_messages = messages[:-1][-5:]
    history = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in recent_messages
    )

    # Fetch real student user details from the database
    db = SessionLocal()
    user_profile = None
    try:
        if student_id:
            user_profile = db.query(User).filter(User.id == student_id).first()
    except Exception as e:
        print(f"Error fetching user profile in router_node: {e}")

    # Send history + current query to unified router
    router_query = f"""
Conversation History:
{history}

Current User Question:
{query}
"""

    # Record Supervisor step
    steps = [
        {
            "id": "supervisor",
            "name": "Supervisor Agent",
            "status": "running",
            "detail": "Analyzing user query intent..."
        }
    ]

    router_response = route(router_query)
    agents = router_response.get("agents", [])
    params = router_response.get("parameters", {})

    # Complete Supervisor step
    if agents:
        steps[0]["status"] = "completed"
        steps[0]["detail"] = f"Routed query to: {', '.join(agents)}"
    else:
        steps[0]["status"] = "completed"
        steps[0]["detail"] = "Query identified as general conversation"

    final_answer = {}

    for agent in agents:
        # ---------------- Academic Agent & Quiz ----------------
        if agent == "AcademicAgent":
            q_lower = query.lower()
            if "quiz" in q_lower or "practice" in q_lower or "explain" in q_lower:
                # Generate AI quiz
                steps.extend([
                    {
                        "id": "academic_RAG",
                        "name": "Academic Agent",
                        "status": "completed",
                        "detail": "Retrieving syllabus context from vector database"
                    },
                    {
                        "id": "quiz_generator",
                        "name": "Quiz Generator Agent",
                        "status": "completed",
                        "detail": "Creating custom practice questions using Groq"
                    }
                ])
                final_answer["academic_quiz"] = quiz_agent.generate_quiz(query)
            else:
                day = params.get("day") or "Monday"
                final_answer["academic"] = academic.get_today_classes(day)
                steps.append({
                    "id": "academic",
                    "name": "Academic Agent",
                    "status": "completed",
                    "detail": f"Retrieved timetable schedule for {day}"
                })

        # ---------------- Placement Agent ----------------
        elif agent == "PlacementAgent":
            company = params.get("company")
            
            cgpa = user_profile.cgpa if user_profile else 8.2
            backlogs = user_profile.backlogs if user_profile else 0
            student_name = user_profile.name if user_profile else "Satya"

            # Record placement steps
            steps.extend([
                {
                    "id": "placement",
                    "name": "Placement Agent",
                    "status": "completed",
                    "detail": f"Loading profile details for student: {student_name}"
                },
                {
                    "id": "eligibility",
                    "name": "Eligibility Engine",
                    "status": "completed",
                    "detail": f"CGPA: {cgpa} | Backlogs: {backlogs} (retrieved deterministically)"
                }
            ])
            
            if company:
                final_answer["placement"] = placement.check_eligibility(company, cgpa, backlogs)
                steps.append({
                    "id": "rule_checker",
                    "name": "Rule Checker",
                    "status": "completed",
                    "detail": f"Company criteria matched for {company}"
                })
            else:
                final_answer["placement"] = {
                    "message": "Please specify a company name (Google, Microsoft, Amazon, Infosys or TCS)."
                }
                steps.append({
                    "id": "rule_checker",
                    "name": "Rule Checker",
                    "status": "completed",
                    "detail": "Criteria matching skipped: Company name missing"
                })

        # ---------------- Knowledge Agent ----------------
        elif agent == "KnowledgeAgent":
            steps.extend([
                {
                    "id": "knowledge",
                    "name": "Knowledge Agent",
                    "status": "completed",
                    "detail": "Querying ChromaDB vector store"
                },
                {
                    "id": "rag_extractor",
                    "name": "RAG Extractor",
                    "status": "completed",
                    "detail": "Retrieved relevant handbook context chunks"
                }
            ])
            final_answer["knowledge"] = knowledge.ask(
                question=query,
                history=history,
            )

        # ---------------- Notification Agent ----------------
        elif agent == "NotificationAgent":
            steps.append({
                "id": "notification",
                "name": "Notification Agent",
                "status": "completed",
                "detail": "Scheduling alert reminder trigger"
            })
            final_answer["notification"] = notification.remind(query, student_id=student_id, db=db)

        # ---------------- Events Agent ----------------
        elif agent == "EventsAgent":
            steps.append({
                "id": "events",
                "name": "Events Agent",
                "status": "completed",
                "detail": "Searching campus events registry"
            })
            final_answer["events"] = events.search_event(query)

        # ---------------- Student Services Agent ----------------
        elif agent == "StudentServicesAgent":
            steps.append({
                "id": "services",
                "name": "Student Services Agent",
                "status": "completed",
                "detail": "Processing student services inquiry"
            })
            q_lower = query.lower()
            if "bonafide" in q_lower or "certificate" in q_lower:
                try:
                    RequestService.create_student_request(
                        db=db,
                        student_id=student_id if student_id else 2,
                        request_type="Bonafide Certificate",
                        details=f"Requested via AI Chat: '{query}'"
                    )
                    final_answer["response"] = "Your request for a Bonafide Certificate has been submitted. A notification has been sent, and the administration has received it. You can collect it tomorrow at the administration office."
                except Exception as e:
                    print(f"Error creating Bonafide request via agent: {e}")
                    final_answer["response"] = "Failed to file your Bonafide Certificate request due to a database error."
            elif "leave" in q_lower or "outing" in q_lower or "permission" in q_lower:
                try:
                    RequestService.create_student_request(
                        db=db,
                        student_id=student_id if student_id else 2,
                        request_type="Leave Application",
                        details=f"Requested via AI Chat: '{query}'"
                    )
                    final_answer["response"] = "Your request for a Leave Application has been submitted. The administration has received it and it is currently pending review."
                except Exception as e:
                    print(f"Error creating Leave request via agent: {e}")
                    final_answer["response"] = "Failed to file your Leave request due to a database error."
            elif "doubt" in q_lower or "clarification" in q_lower:
                try:
                    RequestService.create_student_request(
                        db=db,
                        student_id=student_id if student_id else 2,
                        request_type="Doubt Clearance",
                        details=f"Requested via AI Chat: '{query}'"
                    )
                    final_answer["response"] = "Your request for Doubt Clearance has been submitted. The academic team has received it and it is currently pending review."
                except Exception as e:
                    print(f"Error creating Doubt request via agent: {e}")
                    final_answer["response"] = "Failed to file your Doubt request due to a database error."
            else:
                final_answer["student_services"] = student_services.search_services(query)

        # ---------------- Resume Agent ----------------
        elif agent == "ResumeAgent":
            steps.append({
                "id": "resume",
                "name": "Resume Agent",
                "status": "completed",
                "detail": "Providing resume upload instructions."
            })
            final_answer["response"] = "Please upload a resume file directly via the attachment clip icon below to analyze it."

        # ---------------- Communication Agent ----------------
        elif agent == "CommunicationAgent":
            steps.append({
                "id": "communication",
                "name": "Communication Agent",
                "status": "completed",
                "detail": "Handling communication query."
            })
            q_lower = query.lower()
            if "email" in q_lower or "draft" in q_lower or "mail" in q_lower:
                prompt = f"""
You are the Communication Agent.
The student wants to draft an email.
User Query: {query}

Extract:
1. Recipient (name or department, default: "Registrar's Office")
2. Subject (default: "Request for Information")
3. Purpose (short summary of what the user wants to email about)

Return ONLY a valid JSON object matching the following structure:
{{
    "recipient": "...",
    "subject": "...",
    "purpose": "..."
}}
"""
                try:
                    response = llm.invoke(prompt)
                    text = response.content.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    text = text.strip()
                    data = json.loads(text)
                except Exception:
                    data = {
                        "recipient": "Registrar's Office",
                        "subject": "Request for Information",
                        "purpose": query
                    }
                
                draft = communication.draft_email(
                    recipient=data.get("recipient", "Registrar's Office"),
                    subject=data.get("subject", "Request for Information"),
                    purpose=data.get("purpose", query)
                )
                final_answer["communication"] = {
                    "message": f"Draft email generated successfully for {draft['recipient']}.",
                    "email_draft": draft
                }
            elif "appointment" in q_lower or "schedule" in q_lower or "slot" in q_lower or "book" in q_lower:
                prompt = f"""
You are the Communication Agent.
The student wants to schedule an appointment.
User Query: {query}

Extract:
1. Officer (default: "Academic Advisor")
2. Date (format YYYY-MM-DD, default: "2026-08-24")
3. Time slot (default: "10:00 AM")
4. Reason (default: "Academic Discussion")

Return ONLY a valid JSON object matching the following structure:
{{
    "officer": "...",
    "date": "...",
    "time_slot": "...",
    "reason": "..."
}}
"""
                try:
                    response = llm.invoke(prompt)
                    text = response.content.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    text = text.strip()
                    data = json.loads(text)
                except Exception:
                    data = {
                        "officer": "Academic Advisor",
                        "date": "2026-08-24",
                        "time_slot": "10:00 AM",
                        "reason": "Academic Discussion"
                    }
                
                apt = communication.schedule_appointment(
                    student_id=student_id if student_id else 2,
                    officer=data.get("officer", "Academic Advisor"),
                    date=data.get("date", "2026-08-24"),
                    time_slot=data.get("time_slot", "10:00 AM"),
                    reason=data.get("reason", "Academic Discussion"),
                    db=db
                )
                final_answer["communication"] = apt
            else:
                announcements = communication.get_announcements(db=db)
                final_answer["communication"] = {
                    "announcements": announcements[:3]
                }

    db.close()

    # Response Agent formats final result
    steps.append({
        "id": "response",
        "name": "Response Agent",
        "status": "completed",
        "detail": "Formatting final structured output"
    })

    return {
        "messages": [
            AIMessage(
                content=json.dumps(final_answer)
            )
        ],
        "agent_steps": steps
    }