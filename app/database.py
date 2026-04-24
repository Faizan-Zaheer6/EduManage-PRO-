import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL should be set in .env (e.g. postgresql://user:pass@host/db?sslmode=require)
# Fallback to sqlite for local dev if no DB URL is provided
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# For Postgres (Neon), we usually need sslmode=require
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema():
    """
    Lightweight auto-migration for local/dev.
    Production recommendation: replace with Alembic migrations.
    """
    try:
        dialect = engine.dialect.name
    except Exception:
        return

    # Only needed because SQLAlchemy create_all does NOT alter existing tables.
    if dialect in ("postgresql", "postgres"):
        with engine.begin() as conn:
            # Add users.student_id if missing (safe to run multiple times)
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS student_id INTEGER"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS course_id INTEGER"))
            # FK constraint is handled by Alembic in production; omit here to avoid errors.

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
