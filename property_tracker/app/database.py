from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import os
from typing import Generator

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class PropertyInquiry(Base):
    __tablename__ = "property_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True)
    search_type = Column(String)  # 'single' or 'bulk'
    status = Column(String)
    # REMOVED: price = Column(String)  # Price removed from database
    property_type = Column(String)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Integer)
    zillow_link = Column(Text)
    realtor_link = Column(Text)
    api_source = Column(String)  # 'zillow' or 'realty_base'
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    user_ip = Column(String)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SearchSession(Base):
    __tablename__ = "search_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    search_type = Column(String)  # 'single' or 'bulk'
    total_addresses = Column(Integer)
    successful_searches = Column(Integer, default=0)
    failed_searches = Column(Integer, default=0)
    user_ip = Column(String)
    user_agent = Column(Text)
    filename = Column(String)  # for bulk uploads
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()