import os
import sys

# Add backend to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database.session import SessionLocal, engine, Base
from backend.database.models import User, Complaint, Request
from backend.core.security import hash_password

def seed():
    print("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Clear existing user entries
        print("Cleaning up old data...")
        db.query(Complaint).delete()
        db.query(Request).delete()
        db.query(User).delete()
        db.commit()

        print("Seeding users...")
        
        # 1. Admin account
        admin = User(
            name="Campus Administrator",
            email="admin@campus.edu",
            password_hash=hash_password("admin123"),
            role="Admin",
            status="Active"
        )
        
        # 2. Satya (Primary mock student)
        satya = User(
            name="Satya",
            email="satya@campus.edu",
            password_hash=hash_password("student123"),
            role="Student",
            status="Active",
            cgpa=8.2,
            backlogs=0
        )
        
        # 3. Rahul (Mock student with backlogs)
        rahul = User(
            name="Rahul",
            email="rahul@campus.edu",
            password_hash=hash_password("student123"),
            role="Student",
            status="Active",
            cgpa=6.5,
            backlogs=2
        )
        
        # 4. Priya (Mock high-performing student)
        priya = User(
            name="Priya",
            email="priya@campus.edu",
            password_hash=hash_password("student123"),
            role="Student",
            status="Active",
            cgpa=9.1,
            backlogs=0
        )
        
        db.add_all([admin, satya, rahul, priya])
        db.commit()
        
        print("Database seeded successfully!")
        print("Initial Accounts:")
        print("  Admin   : admin@campus.edu / admin123")
        print("  Student : satya@campus.edu / student123")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
