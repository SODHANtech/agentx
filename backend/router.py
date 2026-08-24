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

Return ONLY a valid JSON object matching the following structure (do NOT wrap in markdown block, do NOT include any other text):
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
    Level 1 — Deterministic Regex Router.
    Parses common campus keywords locally to bypass LLM and function when unconfigured.
    """
    q_lower = query.lower()
    
    # 1. Placement Agent
    if any(k in q_lower for k in ["placement", "eligible", "eligibility", "cgpa", "backlog", "google", "microsoft", "amazon", "infosys", "tcs"]):
        company = None
        for c in ["Google", "Microsoft", "Amazon", "Infosys", "TCS"]:
            if c.lower() in q_lower:
                company = c
                break
        return {
            "agents": ["PlacementAgent"],
            "parameters": {"day": None, "company": company}
        }
        
    # 2. Academic Agent
    if any(k in q_lower for k in ["timetable", "class", "schedule", "lecture", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "tomorrow", "today", "quiz", "practice", "chapter"]):
        day = None
        if "tomorrow" in q_lower:
            day = "Monday"
        elif "today" in q_lower:
            day = "Sunday"
        else:
            for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                if d.lower() in q_lower:
                    day = d
                    break
        return {
            "agents": ["AcademicAgent"],
            "parameters": {"day": day, "company": None}
        }
        
    # 3. Events Agent
    if any(k in q_lower for k in ["event", "register", "cancel", "export", "hackathon", "seminar"]):
        return {
            "agents": ["EventsAgent"],
            "parameters": {"day": None, "company": None}
        }

    # 4. Student Services Agent
    if any(k in q_lower for k in ["hostel", "library", "transport", "bus", "complaint", "grievance", "scholarship"]):
        return {
            "agents": ["StudentServicesAgent"],
            "parameters": {"day": None, "company": None}
        }

    # 5. Resume Agent
    if any(k in q_lower for k in ["resume", "cv", "portfolio", "ats"]):
        return {
            "agents": ["ResumeAgent"],
            "parameters": {"day": None, "company": None}
        }
        
    # 6. Notification Agent
    if any(k in q_lower for k in ["remind", "alert", "notification"]):
        return {
            "agents": ["NotificationAgent"],
            "parameters": {"day": None, "company": None}
        }
        
    # 7. Knowledge Agent
    if any(k in q_lower for k in ["rule", "policy", "handbook", "attendance", "grading", "pass"]):
        return {
            "agents": ["KnowledgeAgent"],
            "parameters": {"day": None, "company": None}
        }

    return None

def route(query: str) -> dict:
    # LEVEL 1: Deterministic routing check
    current_question = query
    if "Current User Question:" in query:
        current_question = query.split("Current User Question:")[-1].strip()

    det_res = deterministic_route(current_question)
    if det_res:
        print("========== LEVEL 1: DETERMINISTIC ROUTER ==========")
        print("Query :", current_question.strip())
        print("Agents:", det_res["agents"])
        print("Params:", det_res["parameters"])
        print("====================================================")
        return det_res

    # LEVEL 2: Fallback LLM routing check
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "{query}")
        ])
        
        structured_llm = llm.with_structured_output(RoutingResult)
        chain = prompt | structured_llm
        result = chain.invoke({"query": query})
        
        # Filter and validate active agents
        agents = [
            agent
            for agent in result.agents
            if agent in VALID_AGENTS
        ]
        agents = list(dict.fromkeys(agents))
        
        valid_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        valid_companies = {"Google", "Microsoft", "Amazon", "Infosys", "TCS"}
        
        day = result.day
        if day and day.title() in valid_days:
            day = day.title()
        else:
            day = None
            
        company = result.company
        if company:
            matched_company = next(
                (c for c in valid_companies if c.lower() == company.lower()), 
                None
            )
            company = matched_company
        else:
            company = None

        parameters = {
            "day": day,
            "company": company
        }

        print("========== LEVEL 2: LLM ROUTER (STRUCTURED) ==========")
        print("Query :", query.strip())
        print("Agents:", agents)
        print("Params:", parameters)
        print("======================================================")

        return {
            "agents": agents,
            "parameters": parameters
        }

    except Exception as e:
        print("========== ROUTER ERROR ==========")
        print(e)
        print("==================================")
        return {
            "agents": [],
            "parameters": {"day": None, "company": None}
        }