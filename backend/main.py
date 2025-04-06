from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
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
    deadline: str
    pay: str
    link: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    id: int
    class Config:
        orm_mode = True

# FastAPI instance
app = FastAPI()



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
    title: str = None,
    state: Optional[str] = None,
    pay: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Job)
    if title:
        query = query.filter(Job.title.contains(title))
    if state:
        states = state.split(',')
        query = query.filter(Job.state.in_(states))
    if pay:
        query = query.filter(Job.pay == pay)
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
