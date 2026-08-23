import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "student_services.json"
GRIEVANCE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "grievances.json"
)


class StudentServicesAgent:

    # =============================
    # Data Loader
    # =============================

    def get_services(self):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    # =============================
    # Helper to Search Flat List
    # =============================

    def get_service_by_name(self, name: str):
        services = self.get_services()
        for service in services:
            if name.lower() in service.get("service", "").lower():
                return service
        return {"message": f"Service '{name}' not found."}

    # =============================
    # Category Handlers
    # =============================

    def get_hostels(self):
        return self.get_service_by_name("Hostel")

    def get_library(self):
        return self.get_service_by_name("Library")

    def get_scholarships(self):
        return self.get_service_by_name("Scholarships")

    def get_transport(self):
        return self.get_service_by_name("Bus Transport")

    def get_faqs(self):
        return self.get_services()

    # =============================
    # Grievance Ticketing System
    # =============================

    def file_grievance(self, student_id: str, category: str, description: str):
        try:
            with open(GRIEVANCE_PATH, "r", encoding="utf-8") as f:
                grievances = json.load(f)
        except FileNotFoundError:
            grievances = []

        new_entry = {
            "id": f"GRV_{len(grievances) + 1:03d}",
            "student_id": student_id,
            "category": category,
            "description": description,
            "status": "Pending"
        }
        grievances.append(new_entry)

        with open(GRIEVANCE_PATH, "w", encoding="utf-8") as f:
            json.dump(grievances, f, indent=4)

        return {
            "success": True,
            "message": f"Grievance submitted successfully. Ticket ID: {new_entry['id']}",
            "ticket": new_entry
        }

    # =============================
    # Smart Search
    # =============================

    def search_services(self, query: str):
        services = self.get_services()
        query = query.lower().strip()

        keywords = [word for word in query.split() if len(word) > 2]
        results = []

        for service in services:
            searchable_text = (
                service.get("service", "")
                + " "
                + service.get("description", "")
                + " "
                + service.get("office", "")
            ).lower()

            score = sum(1 for keyword in keywords if keyword in searchable_text)

            if score > 0:
                results.append((score, service))

        results.sort(key=lambda x: x[0], reverse=True)

        if not results:
            return {"message": "No matching student service found."}

        return [item[1] for item in results]