import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.session import Base, get_db
from backend.database import models
from backend.core.security import hash_password, create_jwt

# In-memory SQLite engine isolated from production campus.db
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Build schemas and seed baseline test accounts in the in-memory database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed Admin account
        admin = models.User(
            id=1,
            name="Campus Administrator",
            email="admin@campus.edu",
            password_hash=hash_password("admin123"),
            role="Admin",
            cgpa=0.0,
            backlogs=0
        )
        # Seed Student account
        student = models.User(
            id=2,
            name="Satya",
            email="satya@campus.edu",
            password_hash=hash_password("student123"),
            role="Student",
            cgpa=8.5,
            backlogs=0,
            roll_number="CS2026-001",
            department="Computer Science"
        )
        db.add(admin)
        db.add(student)
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provides a transactional database session per test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with isolated in-memory DB override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    token = create_jwt({"sub": 1, "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_headers():
    token = create_jwt({"sub": 2, "role": "Student"})
    return {"Authorization": f"Bearer {token}"}
