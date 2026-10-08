import json
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from backend.llm import llm

class RoutingResult(BaseModel):
    agents: List[str] = Field(
        default=[],
        description="The agents that should handle this query. Options: AcademicAgent, PlacementAgent, KnowledgeAgent, NotificationAgent, EventsAgent, StudentServicesAgent, ResumeAgent, CommunicationAgent."
    )
    day: Optional[str] = Field(
        None,
        description="Extracted day of the week if mentioned (e.g. 'Monday', 'Tuesday', etc.) or relative (e.g. 'tomorrow')."
    )
    company: Optional[str] = Field(
        None,
        description="Extracted company name if mentioned (Google, Microsoft, Amazon, Infosys, TCS)."
    )

SYSTEM_PROMPT = """
You are the Intelligent Router and Entity Extractor for the Smart Campus AI.

Analyze the user's query and conversation history, and perform two tasks:
1. Identify which agents should handle the request (can be multiple or empty).
2. Extract parameters for specific agents if mentioned (day of week and/or company name).

Available Agents:
- AcademicAgent: For queries about timetables, classes, schedules, lectures, and generating practice quizzes or explaining academic topics.
- PlacementAgent: For queries about placement eligibility, company requirements, job drives, and corporate visits.
- KnowledgeAgent: For general questions about college policies, rules, handbook, and attendance criteria.
- NotificationAgent: For setting reminders or alerts.
- EventsAgent: For upcoming events, hackathons, seminars, or event registration/cancellation.
- StudentServicesAgent: For hostel, library, transport, scholarships, and submitting grievances.
- ResumeAgent: For resume analysis and ATS score checks.
- CommunicationAgent: For drafting emails, broadcasting notices, announcements, and booking appointments.

Current Reference Date Context: Sunday, August 23, 2026. Use this to resolve relative days (e.g. "tomorrow" -> "Monday", "today" -> "Sunday", "day after tomorrow" -> "Tuesday").

Return ONLY a valid JSON object matching the following structure:
{
    "agents": ["AgentName1", "AgentName2"],
    "parameters": {
        "day": "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday",
        "company": "Google|Microsoft|Amazon|Infosys|TCS"
    }
}

Rules:
- If no agent is needed (general chit-chat, greetings, or off-topic questions), return empty "agents" array and null parameters.
- Valid "day" values are: "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday".
- Valid "company" values are: "Google", "Microsoft", "Amazon", "Infosys", "TCS".
"""

VALID_AGENTS = {
    "AcademicAgent",
    "PlacementAgent",
    "KnowledgeAgent",
    "NotificationAgent",
    "EventsAgent",
    "CommunicationAgent",
    "StudentServicesAgent",
    "ResumeAgent",
}

def deterministic_route(query: str) -> dict:
    """
    Multi-Intent Deterministic Router & Entity Extractor.
    Extracts all matching agents and parameters from campus queries.
    """
    q_lower = query.lower()
    matched_agents = []
    params = {"day": None, "company": None}

    # 1. Academic Agent (Timetable, schedule, classes, days of week)
    if any(k in q_lower for k in [
        "timetable", "class", "classes", "schedule", "lecture", "lectures",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "tomorrow", "today", "quiz", "practice", "syllabus"
    ]):
        matched_agents.append("AcademicAgent")
        if "tomorrow" in q_lower:
            params["day"] = "Monday"
        elif "today" in q_lower:
            params["day"] = "Sunday"
        else:
            for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if d.lower() in q_lower:
                    params["day"] = d
                    break

    # 2. Placement Agent (Eligibility, companies, job drives)
    if any(k in q_lower for k in [
        "placement", "placements", "eligible", "eligibility", "cgpa", "backlog", "backlogs",
        "google", "microsoft", "amazon", "infosys", "tcs"
    ]):
        matched_agents.append("PlacementAgent")
        for c in ["Google", "Microsoft", "Amazon", "Infosys", "TCS"]:
            if c.lower() in q_lower:
                params["company"] = c
                break

    # 3. Events Agent
    if any(k in q_lower for k in ["event", "events", "hackathon", "seminar", "workshop", "fest"]):
        matched_agents.append("EventsAgent")

    # 4. Student Services Agent
    if any(k in q_lower for k in ["hostel", "library", "transport", "bus", "complaint", "grievance", "scholarship", "scholarships"]):
        matched_agents.append("StudentServicesAgent")

    # 5. Resume Agent
    if any(k in q_lower for k in ["resume", "cv", "portfolio", "ats score"]):
        matched_agents.append("ResumeAgent")

    # 6. Communication Agent
    if any(k in q_lower for k in ["draft email", "draft mail", "schedule appointment", "book appointment", "announcement"]):
        matched_agents.append("CommunicationAgent")

    # 7. Knowledge Agent (Handbook, attendance policy, exams)
    if any(k in q_lower for k in ["rule", "rules", "policy", "handbook", "attendance criteria", "grading", "exam rules"]):
        matched_agents.append("KnowledgeAgent")

    # 8. Notification Agent
    if any(k in q_lower for k in ["remind me", "set reminder", "alert me"]):
        matched_agents.append("NotificationAgent")

    if matched_agents:
        # Preserve uniqueness while maintaining order
        unique_agents = list(dict.fromkeys(matched_agents))
        return {
            "agents": unique_agents,
            "parameters": params
        }

    return {"agents": [], "parameters": params}


def route(query: str) -> dict:
    """
    Intelligent Router:
    1. Attempts Groq LLM structured extraction first.
    2. Falls back to multi-intent deterministic router if Groq API key is offline or invalid.
    """
    current_question = query
    if "Current User Question:" in query:
        current_question = query.split("Current User Question:")[-1].strip()

    # Try Groq LLM first
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        structured_llm = llm.with_structured_output(RoutingResult)
        result = structured_llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query)
        ])

        agents = [agent for agent in result.agents if agent in VALID_AGENTS]
        agents = list(dict.fromkeys(agents))

        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        day = result.day
        if day and day.title() in valid_days:
            day = day.title()
        else:
            day = None

        company = result.company
        if company and company.title() in {"Google", "Microsoft", "Amazon", "Infosys", "TCS"}:
            company = company.title()
        else:
            company = None

        print(f"[Router: Groq LLM] Matched Agents: {agents}, Params: day={day}, company={company}")
        return {
            "agents": agents,
            "parameters": {"day": day, "company": company}
        }

    except Exception as llm_err:
        # Graceful fallback to deterministic multi-intent router
        det_res = deterministic_route(current_question)
        print(f"[Router: Fallback] (LLM offline: {llm_err.__class__.__name__}) Matched Agents: {det_res['agents']}, Params: {det_res['parameters']}")
        return det_res