import json
from pathlib import Path
import re
from sqlalchemy.orm import Session
from backend.database.session import SessionLocal
from backend.database import models

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "student_services.json"


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

    def file_grievance(self, student_id, category: str, description: str, db: Session = None):
        parsed_student_id = 2
        if isinstance(student_id, int):
            parsed_student_id = student_id
        elif isinstance(student_id, str):
            match = re.search(r'\d+', student_id)
            if match:
                parsed_student_id = int(match.group())
                if parsed_student_id == 1:
                    parsed_student_id = 2
        
        local_session = False
        if db is None:
            db = SessionLocal()
            local_session = True
        try:
            new_comp = models.Complaint(
                student_id=parsed_student_id,
                department=category,
                description=description,
                status="Pending"
            )
            db.add(new_comp)
            db.commit()
            db.refresh(new_comp)
            
            return {
                "success": True,
                "message": f"Grievance submitted successfully. Ticket ID: GRV_{new_comp.id:03d}",
                "ticket": {
                    "id": f"GRV_{new_comp.id:03d}",
                    "student_id": f"STUDENT_{new_comp.student_id}",
                    "category": new_comp.department,
                    "description": new_comp.description,
                    "status": new_comp.status
                }
            }
        finally:
            if local_session:
                db.close()

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