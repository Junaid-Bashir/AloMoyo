# File: app/database/db.py

import os
import sys
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

# Determine the SQLite file path (fallback if DATABASE_URL not set)
default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alokazi.db"))
DATABASE_URL = settings.DATABASE_URL or f"sqlite:///{default_path}"

# Debug output so you can confirm which DB is used
print("▶ DATABASE_URL =", DATABASE_URL, file=sys.stderr)
print("▶ DB file exists:", os.path.exists(DATABASE_URL.replace("sqlite:///", "")), file=sys.stderr)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

def init_db() -> None:
    """
    DEVELOPMENT ONLY: Drops all tables and re-creates them on startup,
    ensuring your Python models (with nullable postal_code/full_address)
    match your database without any migration conflicts.
    """
    # Drop every table
    SQLModel.metadata.drop_all(engine)
    # Recreate all tables based on current models
    SQLModel.metadata.create_all(engine)

def get_db():
    """
    Dependency for FastAPI routes: yields a session and closes it when done.
    """
    with Session(engine) as session:
        yield session
