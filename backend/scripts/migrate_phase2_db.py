import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set python path so we can import backend packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.session import engine, SessionLocal
from backend.database import models

def migrate():
    print("=== STARTING PHASE 2 DATABASE MIGRATION ===")
    
    # 1. Check/Add columns to users table
    db = SessionLocal()
    try:
        print("Checking users table columns...")
        # Check if roll_number exists
        cursor = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in cursor.fetchall()]
        
        if "roll_number" not in columns:
            print("Adding roll_number column to users table...")
            db.execute(text("ALTER TABLE users ADD COLUMN roll_number VARCHAR"))
        if "department" not in columns:
            print("Adding department column to users table...")
            db.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR"))
        db.commit()
    except Exception as e:
        print(f"Error checking/adding user columns: {e}")
        db.rollback()

    # 2. Back up old event_registrations
    old_regs = []
    try:
        print("Backing up legacy event registrations...")
        # Check if table exists
        cursor = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='event_registrations'"))
        if cursor.fetchone():
            cursor = db.execute(text("SELECT student_id, event_title, registered, date, venue, created_at FROM event_registrations"))
            for row in cursor.fetchall():
                old_regs.append({
                    "student_id": row[0],
                    "event_title": row[1],
                    "registered": row[2],
                    "date": row[3],
                    "venue": row[4],
                    "created_at": row[5]
                })
            print(f"Backed up {len(old_regs)} registrations.")
    except Exception as e:
        print(f"Skipped registration backup (possibly fresh database): {e}")

    # 3. Back up old notifications
    old_notifs = []
    try:
        print("Backing up legacy notifications...")
        cursor = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"))
        if cursor.fetchone():
            # Check if columns are the old layout
            cursor = db.execute(text("PRAGMA table_info(notifications)"))
            cols = [r[1] for r in cursor.fetchall()]
            if "query" in cols and "recipient_id" not in cols:
                cursor = db.execute(text("SELECT student_id, query, status, created_at FROM notifications"))
                for row in cursor.fetchall():
                    old_notifs.append({
                        "student_id": row[0],
                        "query": row[1],
                        "status": row[2],
                        "created_at": row[3]
                    })
                print(f"Backed up {len(old_notifs)} old notifications.")
    except Exception as e:
        print(f"Skipped notifications backup: {e}")

    # 4. Drop old tables that we are refactoring
    try:
        print("Dropping legacy tables for schema recreation...")
        db.execute(text("DROP TABLE IF EXISTS event_registrations"))
        db.execute(text("DROP TABLE IF EXISTS notifications"))
        db.commit()
    except Exception as e:
        print(f"Error dropping tables: {e}")
        db.rollback()

    # 5. Create new tables via SQLAlchemy Base
    print("Recreating database tables with new schemas...")
    models.Base.metadata.create_all(bind=engine)

    # 6. Seed unified events from events.json
    events_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events.json")
    created_events = {}
    if os.path.exists(events_json_path):
        print(f"Seeding events table from {events_json_path}...")
        try:
            with open(events_json_path, "r", encoding="utf-8") as f:
                json_events = json.load(f)
            
            # Find an admin user to be creator
            admin_user = db.query(models.User).filter(models.User.role == "Admin").first()
            admin_id = admin_user.id if admin_user else 1

            for je in json_events:
                # Check if event already exists
                existing = db.query(models.Event).filter(models.Event.title == je["title"]).first()
                if not existing:
                    # Parse date/time
                    dt_str = f"{je['date']} 10:00:00" # Default 10 AM
                    if je.get("time"):
                        try:
                            # e.g. "10:00 AM" or "9:00 AM"
                            time_parsed = datetime.strptime(je["time"].strip(), "%I:%M %p").time()
                            dt_str = f"{je['date']} {time_parsed.strftime('%H:%M:%S')}"
                        except Exception:
                            pass
                    
                    try:
                        start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        start_dt = datetime.now()

                    category = "Event"
                    if "hackathon" in je["title"].lower():
                        category = "Hackathon"
                    elif "workshop" in je["title"].lower():
                        category = "Workshop"
                    elif "seminar" in je["title"].lower():
                        category = "Seminar"

                    new_event = models.Event(
                        title=je["title"],
                        category=category,
                        description=f"Campus {category} - {je['title']}",
                        venue=je["venue"],
                        start_datetime=start_dt,
                        end_datetime=start_dt,
                        published=True,
                        created_by=admin_id
                    )
                    db.add(new_event)
                    db.commit()
                    db.refresh(new_event)
                    print(f"  [SEED] Created Event: {new_event.title} (Category: {category})")
                    created_events[new_event.title] = new_event.id
                else:
                    created_events[existing.title] = existing.id
        except Exception as e:
            print(f"Error seeding events from json: {e}")
            db.rollback()

    # 7. Restore and translate event_registrations
    if old_regs:
        print("Restoring and migrating event registrations...")
        for r in old_regs:
            # Find event ID
            title = r["event_title"]
            evt_id = created_events.get(title)
            if not evt_id:
                # If not found in seed, check DB directly
                db_evt = db.query(models.Event).filter(models.Event.title == title).first()
                if db_evt:
                    evt_id = db_evt.id

            if evt_id:
                # Check for duplicate
                dup = db.query(models.EventRegistration).filter(
                    models.EventRegistration.event_id == evt_id,
                    models.EventRegistration.student_id == r["student_id"]
                ).first()
                if not dup:
                    new_reg = models.EventRegistration(
                        event_id=evt_id,
                        student_id=r["student_id"],
                        status="Registered" if r["registered"] else "Cancelled",
                        registered_at=r["created_at"] if isinstance(r["created_at"], datetime) else datetime.now()
                    )
                    db.add(new_reg)
            else:
                print(f"  [WARN] Could not find event '{title}' to migrate registration for student ID {r['student_id']}.")
        db.commit()
        print("Event registrations migrated successfully.")

    # 8. Restore notifications
    if old_notifs:
        print("Restoring legacy notifications...")
        for n in old_notifs:
            new_n = models.Notification(
                recipient_id=n["student_id"],
                title="Reminder Alert" if "remind" in n["query"].lower() else "Campus Notification",
                message=n["query"],
                type="Reminder",
                read=(n["status"] == "Read"),
                created_at=n["created_at"] if isinstance(n["created_at"], datetime) else datetime.now(),
                # Populate legacy fields for compatibility
                student_id=n["student_id"],
                query=n["query"],
                status=n["status"]
            )
            db.add(new_n)
        db.commit()
        print("Notifications migrated successfully.")

    # 9. Clean up static JSON if required
    # Note: We keep events.json as backup but SQLite is the single source of truth now.
    
    # 10. Update default student users with mock roll numbers & departments
    try:
        satya = db.query(models.User).filter(models.User.email == "satya@campus.edu").first()
        if satya:
            satya.roll_number = "CS2023004"
            satya.department = "Computer Science"
            
        test_student_a = db.query(models.User).filter(models.User.email == "studentA@campus.edu").first()
        if test_student_a:
            test_student_a.roll_number = "EC2023101"
            test_student_a.department = "Electronics & Communication"

        test_student_b = db.query(models.User).filter(models.User.email == "studentB@campus.edu").first()
        if test_student_b:
            test_student_b.roll_number = "ME2023202"
            test_student_b.department = "Mechanical Engineering"
            
        db.commit()
        print("Mock user profiles seeded with roll numbers and departments.")
    except Exception as e:
        print(f"Error seeding user profiles: {e}")
        db.rollback()

    db.close()
    print("=== MIGRATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    migrate()
