import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage

from backend.router import route
from backend.database.session import SessionLocal
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
from backend.services import RequestService
from backend.state import AgentState

# Specialized agent singletons
academic = AcademicAgent()
placement = PlacementAgent()
knowledge = KnowledgeAgent()
notification = NotificationAgent()
events = EventsAgent()
student_services = StudentServicesAgent()
quiz_agent = QuizAgent()
resume_agent = ResumeAgent()
communication = CommunicationAgent()


# ==========================================
# 1. Supervisor / Router Node
# ==========================================

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    query = messages[-1].content

    # Limit history to the last 5 turns
    recent_messages = messages[:-1][-5:]
    history = "\n".join(f"{msg.type}: {msg.content}" for msg in recent_messages)

    router_query = f"""
Conversation History:
{history}

Current User Question:
{query}
"""

    router_response = route(router_query)
    agents = router_response.get("agents", [])
    params = router_response.get("parameters", {})

    steps = [
        {
            "_reset": True,
            "id": "supervisor",
            "name": "Supervisor Agent",
            "status": "completed",
            "detail": f"Routed query to: {', '.join(agents)}" if agents else "Identified query as general campus conversation"
        }
    ]

    return {
        "pending_agents": list(agents),
        "params": params,
        "agent_outputs": {"_reset": True},
        "agent_steps": steps
    }


def route_next_agent(state: AgentState) -> str:
    pending = state.get("pending_agents", [])
    if not pending:
        return "response"

    mapping = {
        "AcademicAgent": "academic",
        "PlacementAgent": "placement",
        "KnowledgeAgent": "knowledge",
        "NotificationAgent": "notification",
        "EventsAgent": "events",
        "StudentServicesAgent": "services",
        "ResumeAgent": "resume",
        "CommunicationAgent": "communication"
    }
    next_agent = pending[0]
    return mapping.get(next_agent, "response")


# ==========================================
# 2. Specialized Agent Nodes
# ==========================================

def academic_node(state: AgentState) -> Dict[str, Any]:
    query = state["messages"][-1].content
    params = state.get("params", {})
    pending = [a for a in state.get("pending_agents", []) if a != "AcademicAgent"]

    q_lower = query.lower()
    if "quiz" in q_lower or "practice" in q_lower or "explain" in q_lower:
        steps = [
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
        ]
        out = {"academic_quiz": quiz_agent.generate_quiz(query)}
    else:
        day = params.get("day") or "Monday"
        steps = [
            {
                "id": "academic",
                "name": "Academic Agent",
                "status": "completed",
                "detail": f"Retrieved timetable schedule for {day}"
            }
        ]
        out = {"academic": academic.get_today_classes(day)}

    return {
        "pending_agents": pending,
        "agent_outputs": out,
        "agent_steps": steps
    }


def placement_node(state: AgentState) -> Dict[str, Any]:
    params = state.get("params", {})
    student_id = state.get("student_id")
    pending = [a for a in state.get("pending_agents", []) if a != "PlacementAgent"]

    db = SessionLocal()
    user_profile = None
    try:
        if student_id:
            user_profile = db.query(User).filter(User.id == student_id).first()
    except Exception as e:
        print(f"Error fetching user profile in placement_node: {e}")
    finally:
        db.close()

    cgpa = user_profile.cgpa if user_profile else 8.2
    backlogs = user_profile.backlogs if user_profile else 0
    student_name = user_profile.name if user_profile else "Satya"

    steps = [
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
    ]

    company = params.get("company")
    if company:
        out = {"placement": placement.check_eligibility(company, cgpa, backlogs)}
        steps.append({
            "id": "rule_checker",
            "name": "Rule Checker",
            "status": "completed",
            "detail": f"Company criteria matched for {company}"
        })
    else:
        out = {
            "placement": {
                "message": "Please specify a company name (Google, Microsoft, Amazon, Infosys or TCS)."
            }
        }
        steps.append({
            "id": "rule_checker",
            "name": "Rule Checker",
            "status": "completed",
            "detail": "Criteria matching skipped: Company name missing"
        })

    return {
        "pending_agents": pending,
        "agent_outputs": out,
        "agent_steps": steps
    }


def knowledge_node(state: AgentState) -> Dict[str, Any]:
    query = state["messages"][-1].content
    pending = [a for a in state.get("pending_agents", []) if a != "KnowledgeAgent"]

    recent_messages = state["messages"][:-1][-5:]
    history = "\n".join(f"{msg.type}: {msg.content}" for msg in recent_messages)

    steps = [
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
    ]

    out = {
        "knowledge": knowledge.ask(
            question=query,
            history=history,
        )
    }

    return {
        "pending_agents": pending,
        "agent_outputs": out,
        "agent_steps": steps
    }


def notification_node(state: AgentState) -> Dict[str, Any]:
    query = state["messages"][-1].content
    student_id = state.get("student_id")
    pending = [a for a in state.get("pending_agents", []) if a != "NotificationAgent"]

    db = SessionLocal()
    try:
        res = notification.remind(query, student_id=student_id, db=db)
    finally:
        db.close()

    steps = [
        {
            "id": "notification",
            "name": "Notification Agent",
            "status": "completed",
            "detail": "Scheduling alert reminder trigger"
        }
    ]

    return {
        "pending_agents": pending,
        "agent_outputs": {"notification": res},
        "agent_steps": steps
    }


def events_node(state: AgentState) -> Dict[str, Any]:
    query = state["messages"][-1].content
    pending = [a for a in state.get("pending_agents", []) if a != "EventsAgent"]

    res = events.search_event(query)

    steps = [
        {
            "id": "events",
            "name": "Events Agent",
            "status": "completed",
            "detail": "Searching campus events registry"
        }
    ]

    return {
        "pending_agents": pending,
        "agent_outputs": {"events": res},
        "agent_steps": steps
    }


def services_node(state: AgentState) -> Dict[str, Any]:
    query = state["messages"][-1].content
    student_id = state.get("student_id")
    pending = [a for a in state.get("pending_agents", []) if a != "StudentServicesAgent"]

    steps = [
        {
            "id": "services",
            "name": "Student Services Agent",
            "status": "completed",
            "detail": "Processing student services inquiry"
        }
    ]

    db = SessionLocal()
    try:
        q_lower = query.lower()
        if "bonafide" in q_lower or "certificate" in q_lower:
            try:
                RequestService.create_student_request(
                    db=db,
                    student_id=student_id if student_id else 2,
                    request_type="Bonafide Certificate",
                    details=f"Requested via AI Chat: '{query}'"
                )
                out = {"response": "Your request for a Bonafide Certificate has been submitted. A notification has been sent, and the administration has received it. You can collect it tomorrow at the administration office."}
            except Exception as e:
                print(f"Error creating Bonafide request via agent: {e}")
                out = {"response": "Failed to file your Bonafide Certificate request due to a database error."}
        elif "leave" in q_lower or "outing" in q_lower or "permission" in q_lower:
            try:
                RequestService.create_student_request(
                    db=db,
                    student_id=student_id if student_id else 2,
                    request_type="Leave Application",
                    details=f"Requested via AI Chat: '{query}'"
                )
                out = {"response": "Your request for a Leave Application has been submitted. The administration has received it and it is currently pending review."}
            except Exception as e:
                print(f"Error creating Leave request via agent: {e}")
                out = {"response": "Failed to file your Leave request due to a database error."}
        elif "doubt" in q_lower or "clarification" in q_lower:
            try:
                RequestService.create_student_request(
                    db=db,
                    student_id=student_id if student_id else 2,
                    request_type="Doubt Clearance",
                    details=f"Requested via AI Chat: '{query}'"
                )
                out = {"response": "Your request for Doubt Clearance has been submitted. The academic team has received it and it is currently pending review."}
            except Exception as e:
                print(f"Error creating Doubt request via agent: {e}")
                out = {"response": "Failed to file your Doubt request due to a database error."}
        else:
            out = {"student_services": student_services.search_services(query)}
    finally:
        db.close()

    return {
        "pending_agents": pending,
        "agent_outputs": out,
        "agent_steps": steps
    }


def resume_node(state: AgentState) -> Dict[str, Any]:
    pending = [a for a in state.get("pending_agents", []) if a != "ResumeAgent"]
    steps = [
        {
            "id": "resume",
            "name": "Resume Agent",
            "status": "completed",
            "detail": "Providing resume upload instructions."
        }
    ]
    out = {"response": "Please upload a resume file directly via the attachment clip icon below to analyze it."}

    return {
        "pending_agents": pending,
        "agent_outputs": out,
        "agent_steps": steps
    }


def communication_node(state: AgentState) -> Dict[str, Any]:
    query = state["messages"][-1].content
    student_id = state.get("student_id")
    pending = [a for a in state.get("pending_agents", []) if a != "CommunicationAgent"]

    steps = [
        {
            "id": "communication",
            "name": "Communication Agent",
            "status": "completed",
            "detail": "Handling communication query."
        }
    ]

    q_lower = query.lower()
    db = SessionLocal()
    try:
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
            out = {
                "communication": {
                    "message": f"Draft email generated successfully for {draft['recipient']}.",
                    "email_draft": draft
                }
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
            out = {"communication": apt}
        else:
            announcements = communication.get_announcements(db=db)
            out = {
                "communication": {
                    "announcements": announcements[:3]
                }
            }
    finally:
        db.close()

    return {
        "pending_agents": pending,
        "agent_outputs": out,
        "agent_steps": steps
    }


def synthesize_conversational_response(outputs: dict, query: str, user_profile: Optional[User] = None) -> str:
    """Synthesizes human-like, intelligent responses from retrieved campus agent data."""
    # 1. Attempt Groq LLM synthesis if API key is active
    try:
        from backend.llm import llm
        prompt = f"""You are Smart Campus AI, a polite, intelligent university assistant.
User Query: {query}

Retrieved Campus Systems Data:
{json.dumps(outputs, indent=2)}

Please write a natural, coherent, conversational response in markdown answering the user query based on the retrieved data. Use clean formatting and bullet points where helpful. Do NOT output raw JSON."""
        res = llm.invoke(prompt)
        if res and res.content and len(res.content.strip()) > 10:
            return res.content.strip()
    except Exception:
        pass

    # 2. High-fidelity conversational synthesis fallback
    sections = []
    student_name = user_profile.name if user_profile else "Student"

    if "academic" in outputs:
        classes = outputs["academic"]
        if isinstance(classes, list) and classes:
            day = classes[0].get("day", "Today")
            class_lines = "\n".join([f"  • **{c['subject']}** at {c['time']}" for c in classes])
            sections.append(f"📅 **Your Schedule for {day}:**\n{class_lines}")
        elif isinstance(classes, dict):
            sections.append(f"📅 **Academic Timetable:** {classes.get('message', 'No scheduled classes found.')}")

    if "academic_quiz" in outputs:
        quiz_data = outputs["academic_quiz"]
        sections.append(f"📝 **Practice Quiz:**\n{quiz_data.get('explanation', '')}")

    if "placement" in outputs:
        p = outputs["placement"]
        if "status" in p:
            company = p.get("company", "Company")
            status = p.get("status")
            status_badge = "✅ **Eligible**" if status == "Eligible" else "❌ **Not Eligible**"
            details = p.get("details", "")
            sections.append(f"💼 **Placement Eligibility ({company}):**\nStatus: {status_badge}\nProfile: CGPA {user_profile.cgpa if user_profile else 8.2} | {user_profile.backlogs if user_profile else 0} Backlogs\nDetails: {details}")
        elif "message" in p:
            sections.append(f"💼 **Placement:** {p['message']}")

    if "knowledge" in outputs:
        ans = outputs["knowledge"].get("answer", "")
        if ans:
            sections.append(f"📖 **Campus Handbook & Guidelines:**\n{ans}")

    if "events" in outputs:
        evts = outputs["events"]
        if isinstance(evts, list) and evts:
            ev_lines = "\n".join([f"  • **{e['title']}** on {e.get('date', 'TBD')} ({e.get('venue', 'Campus')})" for e in evts])
            sections.append(f"🎉 **Upcoming Events:**\n{ev_lines}")
        else:
            sections.append("🎉 **Events:** No matching campus events found.")

    if "notification" in outputs:
        sections.append(f"🔔 **Reminder:** {outputs['notification'].get('message', '')}")

    if "student_services" in outputs:
        srvs = outputs["student_services"]
        if isinstance(srvs, list) and srvs:
            srv_lines = "\n".join([f"  • **{s['service']}**: {s.get('description', '')} ({s.get('office', '')})" for s in srvs])
            sections.append(f"🏫 **Student Services:**\n{srv_lines}")
        elif isinstance(srvs, dict):
            sections.append(f"🏫 **Student Services:** {srvs.get('message', '')}")

    if "response" in outputs:
        sections.append(outputs["response"])

    if not sections:
        return f"Hello {student_name}! I received your query. How else can I assist you with your campus classes, placements, or services today?"

    return "\n\n".join(sections)


def response_node(state: AgentState) -> Dict[str, Any]:
    outputs = state.get("agent_outputs", {})
    messages = state.get("messages", [])
    query = messages[-1].content if messages else ""
    student_id = state.get("student_id")

    db = SessionLocal()
    user_profile = None
    try:
        if student_id:
            user_profile = db.query(User).filter(User.id == student_id).first()
    except Exception as e:
        print(f"Error fetching user profile in response_node: {e}")
    finally:
        db.close()

    synthesized_text = synthesize_conversational_response(outputs, query, user_profile)
    outputs["response"] = synthesized_text

    steps = [
        {
            "id": "response",
            "name": "Response Agent",
            "status": "completed",
            "detail": "Synthesized unified campus intelligence response"
        }
    ]

    return {
        "messages": [
            AIMessage(
                content=json.dumps(outputs)
            )
        ],
        "agent_steps": steps
    }


# ==========================================
# Legacy monolithic runner (backwards compat)
# ==========================================

def router_node(state: AgentState) -> Dict[str, Any]:
    """Preserved for backwards compatibility with any legacy single-node caller."""
    from backend.nodes_legacy import router_node as legacy_runner
    return legacy_runner(state)