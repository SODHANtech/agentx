import os
import sys
import json
import re
from datetime import datetime

# Add backend to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database.session import SessionLocal, engine, Base
from backend.database import models

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

def get_target_student_id(db, student_ref):
    if not student_ref:
        return 2
    # If it is already an int
    if isinstance(student_ref, int):
        return student_ref
    
    # Parse numbers from student_ref (e.g. S001, STUDENT_1, etc.)
    match = re.search(r'\d+', str(student_ref))
    if match:
        num = int(match.group())
        # Map S001/1 to Satya (ID 2), 2 to Rahul (ID 3), 3 to Priya (ID 4)
        if num == 1:
            return 2
        elif num == 2:
            return 3
        elif num == 3:
            return 4
        else:
            # Check if user exists with this ID
            user = db.query(models.User).filter(models.User.id == num).first()
            if user:
                return user.id
    return 2  # Default fallback to Satya (ID 2)

def migrate():
    # Make sure all tables are created
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Get Admin user id
    admin = db.query(models.User).filter(models.User.role == "Admin").first()
    admin_id = admin.id if admin else 1
    
    stats = {
        "event_registrations": {"read": 0, "migrated": 0, "skipped": 0},
        "grievances": {"read": 0, "migrated": 0, "skipped": 0},
        "appointments": {"read": 0, "migrated": 0, "skipped": 0},
        "reminders": {"read": 0, "migrated": 0, "skipped": 0},
        "announcements": {"read": 0, "migrated": 0, "skipped": 0}
    }
    
    try:
        # 1. Event Registrations
        evt_reg_path = os.path.join(DATA_DIR, "event_registrations.json")
        if os.path.exists(evt_reg_path):
            with open(evt_reg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["event_registrations"]["read"] = len(data)
                for item in data:
                    try:
                        student_id = get_target_student_id(db, item.get("student_id"))
                        event_title = item.get("event")
                        registered = bool(item.get("registered", True))
                        date = item.get("date")
                        venue = item.get("venue")
                        
                        # Check duplicate
                        exists = db.query(models.EventRegistration).filter(
                            models.EventRegistration.student_id == student_id,
                            models.EventRegistration.event_title == event_title
                        ).first()
                        
                        if not exists:
                            new_reg = models.EventRegistration(
                                student_id=student_id,
                                event_title=event_title,
                                registered=registered,
                                date=date,
                                venue=venue
                            )
                            db.add(new_reg)
                            stats["event_registrations"]["migrated"] += 1
                        else:
                            stats["event_registrations"]["skipped"] += 1
                    except Exception as e:
                        print(f"Error migrating event registration {item}: {e}")
            db.commit()
            
        # 2. Grievances
        grievances_path = os.path.join(DATA_DIR, "grievances.json")
        if os.path.exists(grievances_path):
            with open(grievances_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["grievances"]["read"] = len(data)
                for item in data:
                    try:
                        student_id = get_target_student_id(db, item.get("student_id"))
                        department = item.get("category", "General")
                        description = item.get("description")
                        status = item.get("status", "Pending")
                        
                        # Check duplicate
                        exists = db.query(models.Complaint).filter(
                            models.Complaint.student_id == student_id,
                            models.Complaint.description == description
                        ).first()
                        
                        if not exists:
                            new_comp = models.Complaint(
                                student_id=student_id,
                                department=department,
                                description=description,
                                status=status
                            )
                            db.add(new_comp)
                            stats["grievances"]["migrated"] += 1
                        else:
                            stats["grievances"]["skipped"] += 1
                    except Exception as e:
                        print(f"Error migrating grievance {item}: {e}")
            db.commit()

        # 3. Appointments
        appointments_path = os.path.join(DATA_DIR, "appointments.json")
        if os.path.exists(appointments_path):
            with open(appointments_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["appointments"]["read"] = len(data)
                for item in data:
                    try:
                        student_id = get_target_student_id(db, item.get("student_id"))
                        officer = item.get("officer")
                        date = item.get("date")
                        time_slot = item.get("time_slot")
                        reason = item.get("reason")
                        status = item.get("status", "Confirmed")
                        
                        # Check duplicate
                        exists = db.query(models.Appointment).filter(
                            models.Appointment.student_id == student_id,
                            models.Appointment.date == date,
                            models.Appointment.time_slot == time_slot
                        ).first()
                        
                        if not exists:
                            new_apt = models.Appointment(
                                student_id=student_id,
                                officer=officer,
                                date=date,
                                time_slot=time_slot,
                                reason=reason,
                                status=status
                            )
                            db.add(new_apt)
                            stats["appointments"]["migrated"] += 1
                        else:
                            stats["appointments"]["skipped"] += 1
                    except Exception as e:
                        print(f"Error migrating appointment {item}: {e}")
            db.commit()

        # 4. Reminders (to Notifications)
        reminders_path = os.path.join(DATA_DIR, "reminders.json")
        if os.path.exists(reminders_path):
            with open(reminders_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["reminders"]["read"] = len(data)
                for item in data:
                    try:
                        # Reminders don't have student_id in json, default to Satya (ID 2)
                        student_id = 2
                        query = item.get("query")
                        status = item.get("status", "Pending")
                        
                        # Check duplicate
                        exists = db.query(models.Notification).filter(
                            models.Notification.student_id == student_id,
                            models.Notification.query == query
                        ).first()
                        
                        if not exists:
                            created_at_dt = datetime.utcnow()
                            if item.get("created_at"):
                                try:
                                    created_at_dt = datetime.strptime(item.get("created_at"), "%Y-%m-%d %H:%M:%S")
                                except:
                                    pass
                            
                            new_notif = models.Notification(
                                student_id=student_id,
                                query=query,
                                status=status,
                                created_at=created_at_dt
                            )
                            db.add(new_notif)
                            stats["reminders"]["migrated"] += 1
                        else:
                            stats["reminders"]["skipped"] += 1
                    except Exception as e:
                        print(f"Error migrating reminder {item}: {e}")
            db.commit()

        # 5. Announcements
        announcements_path = os.path.join(DATA_DIR, "announcements.json")
        if os.path.exists(announcements_path):
            with open(announcements_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["announcements"]["read"] = len(data)
                for item in data:
                    try:
                        title = item.get("title")
                        content = item.get("content")
                        category = item.get("category", "General")
                        
                        # Check duplicate
                        exists = db.query(models.Announcement).filter(
                            models.Announcement.title == title,
                            models.Announcement.description == content
                        ).first()
                        
                        if not exists:
                            created_at_dt = datetime.utcnow()
                            if item.get("date"):
                                try:
                                    created_at_dt = datetime.strptime(item.get("date"), "%Y-%m-%d")
                                except:
                                    pass
                                    
                            new_ann = models.Announcement(
                                title=title,
                                description=content,
                                category=category,
                                author_id=admin_id,
                                created_at=created_at_dt
                            )
                            db.add(new_ann)
                            stats["announcements"]["migrated"] += 1
                        else:
                            stats["announcements"]["skipped"] += 1
                    except Exception as e:
                        print(f"Error migrating announcement {item}: {e}")
            db.commit()

        print("\n=== MIGRATION STATISTICS ===")
        for key, val in stats.items():
            print(f"{key}: Read={val['read']}, Migrated={val['migrated']}, Skipped={val['skipped']}")
        print("============================\n")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
