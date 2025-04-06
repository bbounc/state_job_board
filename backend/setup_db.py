from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Fetch the database URL from the .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# Database setup using SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Job model (SQLAlchemy)
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)  # Ensure title is not nullable
    state = Column(String, nullable=False)  # Ensure state is not nullable
    deadline = Column(String, nullable=True)  # Allow NULL values for deadline
    pay = Column(String, nullable=True)  # Allow NULL values for pay
    link = Column(String, unique=True, nullable=False)  # Link must be unique and not nullable

# Create database tables (if they don't exist)
Base.metadata.create_all(bind=engine)

print("Database and table created successfully!")
