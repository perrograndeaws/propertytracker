from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PropertyResult(BaseModel):
    address: str
    status: Optional[str] = "Not Found"
    price: Optional[str] = None  # Still shown to user, just not stored
    zillow_link: Optional[str] = None
    realtor_link: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    error: Optional[str] = None
    api_source: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[PropertyResult]
    total_searched: int
    successful: int
    failed: int
    session_id: str

class InquiryStats(BaseModel):
    total_inquiries: int
    total_sessions: int
    successful_searches: int
    failed_searches: int
    top_searched_addresses: List[dict]
    recent_searches: List[dict]

# Database Models (for responses) - Price removed
class PropertyInquiryResponse(BaseModel):
    id: int
    address: str
    search_type: str
    status: Optional[str]
    # REMOVED: price: Optional[str]  # Price removed from database response
    property_type: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True