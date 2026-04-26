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
    # Production DB Settings
    is_postgres = any(p in SQLALCHEMY_DATABASE_URL for p in ("postgresql", "postgres"))
    
    engine_args = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }
    
    # SSL Configuration (Zaroori for Cloud DBs like Neon/Supabase/Vercel Postgres)
    if is_postgres:
        engine_args["connect_args"] = {"sslmode": "require"}
        
    engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_args)
    print(f"📡 Database engine initialized (Dialect: {engine.dialect.name})")
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

def ensure_schema():
    """
    Ye function models ko dekh kar database mein tables banata hai aur 
    missing columns (migrations) handle karta hai.
    """
    try:
        # 1. Saare tables create karna jo missing hain
        Base.metadata.create_all(bind=engine)
        
        # 2. Manual column additions (Agar migrations file nahi banayi)
        dialect = engine.dialect.name
        if dialect in ("postgresql", "postgres"):
            with engine.connect() as conn:
                # Users table fixes
                for col in ["student_id", "course_id"]:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} INTEGER"))
                        conn.commit()
                    except Exception as e:
                        print(f"ℹ️ Column '{col}' check: {e}")
                
                # Students table fixes (Optional: course_id column)
                try:
                    conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS course_id INTEGER"))
                    conn.commit()
                except Exception as e:
                    print(f"ℹ️ Students course_id check: {e}")
                    
        print("✅ Database schema synchronized successfully!")
    except Exception as e:
        print(f"⚠️ Database Schema Sync Warning: {e}")

# 5. Dependency injection function for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()