from backend.agents.academic_agent import AcademicAgent
from backend.agents.placement_agent import PlacementAgent
from backend.agents.student_services_agent import StudentServicesAgent
from backend.agents.events_agent import EventsAgent
from backend.agents.communications_agent import CommunicationAgent


def test_academic_agent():
    agent = AcademicAgent()
    classes = agent.get_today_classes("Monday")
    assert isinstance(classes, list)
    assert len(classes) > 0
    assert classes[0]["day"] == "Monday"

    not_found = agent.get_today_classes("Someday")
    assert "message" in not_found


def test_placement_agent():
    agent = PlacementAgent()

    # Eligible case (Google requires CGPA >= 8.0, backlogs <= 0)
    eligible = agent.check_eligibility("Google", cgpa=8.5, backlogs=0)
    assert eligible["status"] == "Eligible"
    assert eligible["company"] == "Google"

    # Ineligible case
    ineligible = agent.check_eligibility("Google", cgpa=7.0, backlogs=1)
    assert ineligible["status"] == "Not Eligible"

    # Unknown company
    missing = agent.check_eligibility("NonExistentCorp", cgpa=9.0, backlogs=0)
    assert "not found" in missing["message"]


def test_student_services_agent():
    agent = StudentServicesAgent()
    services = agent.get_services()
    assert isinstance(services, list)

    hostel = agent.get_hostels()
    assert hostel is not None

    library = agent.get_library()
    assert library is not None


def test_events_agent(db_session):
    agent = EventsAgent()
    events = agent.get_events()
    assert isinstance(events, list)


def test_communications_agent(db_session):
    agent = CommunicationAgent()
    draft = agent.draft_email(
        recipient="Registrar",
        subject="Transcript Request",
        purpose="Applying for higher studies"
    )
    assert draft["recipient"] == "Registrar"
    assert "Dear" in draft["body"]
    assert draft["status"] == "Draft Generated"
