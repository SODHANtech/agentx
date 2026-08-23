from backend.agents.academic_agent import AcademicAgent
from backend.agents.placement_agent import PlacementAgent
from backend.agents.notification_agent import NotificationAgent


class DashboardAgent:

    def __init__(self):

        self.academic = AcademicAgent()
        self.placement = PlacementAgent()
        self.notification = NotificationAgent()

    def get_dashboard(self):

        return {

            "student": {
                "name": "Satya"
            },

            "today_classes":
                self.academic.get_today_classes("Monday"),

            "placement":
                self.placement.check_eligibility("Google"),

            "notifications":
                self.notification.get_reminders()

        }