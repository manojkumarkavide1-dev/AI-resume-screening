from sqlalchemy import Column, Integer, String, Float, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Candidate(Base):
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    filename = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    match_score = Column(Float, default=0.0)
    skills = Column(String(500), default="") # Comma separated skills
    
import os

# Database initialization
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Use Postgres (or another DB) if provided in environment variables
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Fallback to SQLite
    # On Vercel, the filesystem is read-only except for /tmp.
    if os.environ.get("VERCEL"):
        db_path = 'sqlite:////tmp/resumes.db'
    else:
        db_path = 'sqlite:///resumes.db'
    engine = create_engine(db_path, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
