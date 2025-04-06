from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Job model (SQLAlchemy)
class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    state = Column(String)
    deadline = Column(String)
    pay = Column(String)
    link = Column(String)

# Create database tables (if they don't exist)
Base.metadata.create_all(bind=engine)

# Pydantic models
class JobBase(BaseModel):
    title: str
    state: str
    deadline: Optional[str] = None  # Allow None for deadline
    pay: Optional[str] = None  # Allow None for pay
    link: Optional[str] = None  # Allow None for link

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    id: int
    class Config:
        orm_mode = True

# FastAPI instance
app = FastAPI()

# CORS middleware setup
origins = [
    "https://state-job-board.onrender.com",  # Add your frontend URL here
    "http://localhost",  # Allow local development if necessary
    "http://localhost:3000",  # Example for React frontend running locally
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from the listed domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers (content-type, etc.)
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API to fetch job listings with pagination and filters
@app.get("/jobs", response_model=List[JobOut])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    title: Optional[str] = None,
    state: Optional[str] = None,
    pay: Optional[str] = None,
    deadline: Optional[str] = None,  # Added deadline filter
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    
    # Filters
    if title:
        query = query.filter(Job.title.contains(title))
    if state:
        states = state.split(',')
        query = query.filter(Job.state.in_(states))
    if pay:
        query = query.filter(Job.pay == pay)
    if deadline:
        query = query.filter(Job.deadline == deadline)  # Filter by deadline
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs

# API to insert a job (used by your scraper)
@app.post("/jobs", response_model=JobOut)
def add_job(job: JobCreate, db: Session = Depends(get_db)):
    try:
        db_job = Job(**job.dict())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error adding job: " + str(e))
