from backend.agents.academic_agent import AcademicAgent
from backend.agents.placement_agent import PlacementAgent
from backend.agents.notification_agent import NotificationAgent


class DashboardAgent:

    def __init__(self):

        self.academic = AcademicAgent()
        self.placement = PlacementAgent()
        self.notification = NotificationAgent()

    def get_dashboard(self, student_id: int = None, db = None):
        # Import dynamically to prevent circular import issues
        from backend.database.models import User
        student_name = "Satya"
        cgpa = 8.2
        backlogs = 0
        
        if student_id and db:
            user = db.query(User).filter(User.id == student_id).first()
            if user:
                student_name = user.name
                cgpa = user.cgpa
                backlogs = user.backlogs

        return {
            "student": {
                "name": student_name,
                "cgpa": cgpa,
                "backlogs": backlogs
            },
            "today_classes":
                self.academic.get_today_classes("Monday"),
            "placement":
                self.placement.check_eligibility("Google", cgpa=cgpa, backlogs=backlogs),
            "notifications":
                self.notification.get_reminders(student_id=student_id, db=db)
        }