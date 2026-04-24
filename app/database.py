import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env file se variables load karne ke liye
load_dotenv()

# 1. DATABASE_URL Railway/Neon se uthayega, warna local SQLite par chalega
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Railway/Heroku fix: Agar URL 'postgres://' se shuru ho raha hai toh usay 'postgresql://' mein badlein
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Engine Configuration
if SQLALCHEMY_DATABASE_URL:
    # Cloud DB (Neon/Railway) ke liye settings
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        # Neon DB ke liye SSL zaroori hai
        connect_args={"sslmode": "require"} if "neon.tech" in SQLALCHEMY_DATABASE_URL else {},
        pool_pre_ping=True  # Connection drop hone se bachata hai
    )
else:
    # Local Development (Fallback to SQLite)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

# 3. Session aur Base setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. Tables auto-create karne ke liye function
def ensure_schema():
    """
    Ye function models ko dekh kar database mein tables banata hai.
    """
    try:
        # Saare tables create karna
        Base.metadata.create_all(bind=engine)
        
        # Extra columns add karne ke liye (Safe approach)
        dialect = engine.dialect.name
        if dialect in ("postgresql", "postgres"):
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS student_id INTEGER"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS course_id INTEGER"))
        print("✅ Database schema synchronized successfully!")
    except Exception as e:
        print(f"❌ Migration/Schema Error: {e}")

# 5. Dependency injection function for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()