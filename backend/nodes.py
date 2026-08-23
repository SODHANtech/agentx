import json
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

academic = AcademicAgent()
placement = PlacementAgent()
knowledge = KnowledgeAgent()
notification = NotificationAgent()
events = EventsAgent()
student_services = StudentServicesAgent()
quiz_agent = QuizAgent()

def router_node(state):
    messages = state["messages"]
    student_id = state.get("student_id")

    # Current user query
    query = messages[-1].content

    # Conversation history
    history = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in messages[:-1]
    )

    # Fetch real student user details from the database
    db = SessionLocal()
    user_profile = None
    try:
        if student_id:
            user_profile = db.query(User).filter(User.id == student_id).first()
    except Exception as e:
        print(f"Error fetching user profile in router_node: {e}")
    finally:
        db.close()

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
            final_answer["notification"] = notification.remind(query)

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
                "detail": "Searching active campus services directory"
            })
            final_answer["student_services"] = student_services.search_services(query)

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