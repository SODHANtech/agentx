from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

connect_args = {}
extra_args = {}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Production PostgreSQL configurations
    extra_args["pool_size"] = 10
    extra_args["max_overflow"] = 20
    extra_args["pool_recycle"] = 1800

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **extra_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# FastAPI dependency to yield database sessions per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
