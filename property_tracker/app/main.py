from fastapi import FastAPI, File, UploadFile, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import shutil
from typing import List
import uuid

from .models import PropertyResult, SearchResponse, InquiryStats
from .utils import process_property_address, process_csv_file, create_search_session, update_search_session
from .api_clients import PropertyAPIClient
from .database import get_db, PropertyInquiry, SearchSession

app = FastAPI(title="Property Status Checker", description="Search property status without price information")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def get_user_agent(request: Request) -> str:
    """Get user agent"""
    return request.headers.get("User-Agent", "Unknown")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search-single", response_model=PropertyResult)
async def search_single_property(
    address: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Search for a single property by address"""
    
    # Get user info
    user_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Create session for single search
    session_id = create_search_session(
        db=db,
        search_type="single",
        total_addresses=1,
        user_ip=user_ip,
        user_agent=user_agent
    )
    
    # Process search
    api_client = PropertyAPIClient()
    result = process_property_address(
        address=address,
        api_client=api_client,
        db=db,
        search_type="single",
        session_id=session_id,
        user_ip=user_ip,
        user_agent=user_agent
    )
    
    # Update session
    successful = 1 if result.status not in ["Error", "Not Found"] else 0
    failed = 1 - successful
    update_search_session(db, session_id, successful, failed)
    
    return result

@app.post("/upload-file", response_model=SearchResponse)
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Upload CSV/Excel file and process all addresses"""
    
    # Get user info
    user_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process file with database logging
        results, session_id = process_csv_file(
            file_path=file_path,
            db=db,
            user_ip=user_ip,
            user_agent=user_agent,
            filename=file.filename
        )
        
        # Calculate stats
        successful = len([r for r in results if r.status not in ["Error", "Not Found"]])
        failed = len(results) - successful
        
        return SearchResponse(
            results=results,
            total_searched=len(results),
            successful=successful,
            failed=failed,
            session_id=session_id
        )
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/admin/stats", response_model=InquiryStats)
async def get_inquiry_stats(db: Session = Depends(get_db)):
    """Get inquiry statistics (admin endpoint)"""
    
    # Total inquiries
    total_inquiries = db.query(PropertyInquiry).count()
    
    # Total sessions
    total_sessions = db.query(SearchSession).count()
    
    # Success/failure counts
    successful_searches = db.query(PropertyInquiry).filter(PropertyInquiry.success == True).count()
    failed_searches = db.query(PropertyInquiry).filter(PropertyInquiry.success == False).count()
    
    # Top searched addresses
    top_addresses = db.query(
        PropertyInquiry.address,
        db.func.count(PropertyInquiry.address).label('count')
    ).group_by(PropertyInquiry.address).order_by(db.func.count(PropertyInquiry.address).desc()).limit(10).all()
    
    top_searched_addresses = [{"address": addr, "count": count} for addr, count in top_addresses]
    
    # Recent searches
    recent = db.query(PropertyInquiry).order_by(PropertyInquiry.created_at.desc()).limit(10).all()
    recent_searches = [
        {
            "address": r.address,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "search_type": r.search_type
        } for r in recent
    ]
    
    return InquiryStats(
        total_inquiries=total_inquiries,
        total_sessions=total_sessions,
        successful_searches=successful_searches,
        failed_searches=failed_searches,
        top_searched_addresses=top_searched_addresses,
        recent_searches=recent_searches
    )

@app.get("/admin/inquiries")
async def get_all_inquiries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all inquiries with pagination"""
    
    inquiries = db.query(PropertyInquiry).offset(skip).limit(limit).all()
    return inquiries

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Property Status Checker is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)