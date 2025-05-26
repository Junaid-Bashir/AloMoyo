# File: app/database/db.py

import os
import sys
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from app.core.config import settings

# Determine the SQLite file path (fallback if DATABASE_URL not set)
default_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "alokazi.db")
)
DATABASE_URL = settings.DATABASE_URL or f"sqlite:///{default_path}"

# Debug output so you can confirm which DB is used
print("▶ DATABASE_URL =", DATABASE_URL, file=sys.stderr)
print("▶ DB file exists:", os.path.exists(DATABASE_URL.replace("sqlite:///", "")), file=sys.stderr)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)


def init_db() -> None:
    """
    DEVELOPMENT ONLY: Drops all tables and re-creates them on startup,
    ensuring your Python models match your database, and sets up FTS.
    """
    # 1) Drop & recreate all regular tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    # 2) Create the FTS5 virtual tables and triggers
    with engine.begin() as conn:
        # Business FTS table + triggers
        conn.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS business_fts 
        USING fts5(
          name, 
          short_description, 
          content='business', 
          content_rowid='id'
        );
        """))
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS business_ai 
        AFTER INSERT ON business
        BEGIN
          INSERT INTO business_fts(rowid, name, short_description)
          VALUES (new.id, new.name, new.short_description);
        END;
        """))
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS business_ad 
        AFTER DELETE ON business
        BEGIN
          INSERT INTO business_fts(business_fts, rowid, name, short_description)
          VALUES('delete', old.id, old.name, old.short_description);
        END;
        """))
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS business_au
        AFTER UPDATE ON business
        BEGIN
          INSERT INTO business_fts(business_fts, rowid, name, short_description)
          VALUES('delete', old.id, old.name, old.short_description);
          INSERT INTO business_fts(rowid, name, short_description)
          VALUES (new.id, new.name, new.short_description);
        END;
        """))

        # POI FTS table + triggers
        conn.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS poi_fts 
        USING fts5(
          label, 
          short_description, 
          content='favourable_place', 
          content_rowid='id'
        );
        """))
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS poi_ai 
        AFTER INSERT ON favourable_place
        BEGIN
          INSERT INTO poi_fts(rowid, label, short_description)
          VALUES (new.id, new.label, new.short_description);
        END;
        """))
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS poi_ad 
        AFTER DELETE ON favourable_place
        BEGIN
          INSERT INTO poi_fts(poi_fts, rowid, label, short_description)
          VALUES('delete', old.id, old.label, old.short_description);
        END;
        """))
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS poi_au
        AFTER UPDATE ON favourable_place
        BEGIN
          INSERT INTO poi_fts(poi_fts, rowid, label, short_description)
          VALUES('delete', old.id, old.label, old.short_description);
          INSERT INTO poi_fts(rowid, label, short_description)
          VALUES (new.id, new.label, new.short_description);
        END;
        """))


def get_db():
    """
    Dependency for FastAPI routes: yields a session and closes it when done.
    """
    with Session(engine) as session:
        yield session
