import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
COMPANY_FILE = BASE_DIR / "data" / "companies.json"

class PlacementAgent:

    def check_eligibility(self, company_name: str, cgpa: float = 8.2, backlogs: int = 0):
        """
        Determines student placement eligibility deterministically based on company rules 
        and the student's actual database profile (CGPA and backlogs).
        """
        companies = self.get_companies()

        for company in companies:
            if company["company"].lower() == company_name.lower():
                if (
                    cgpa >= company["cgpa"]
                    and backlogs <= company["backlogs"]
                ):
                    return {
                        "status": "Eligible",
                        "company": company["company"],
                        "details": f"Meets criteria (CGPA >= {company['cgpa']} and backlogs <= {company['backlogs']})"
                    }
                return {
                    "status": "Not Eligible",
                    "company": company["company"],
                    "details": f"Does not meet criteria (Required CGPA: {company['cgpa']}, Backlogs: {company['backlogs']})"
                }

        return {
            "message": f"Company '{company_name}' not found"
        }

    def get_companies(self):
        if not COMPANY_FILE.exists():
            return []
        with open(COMPANY_FILE, "r") as f:
            return json.load(f)