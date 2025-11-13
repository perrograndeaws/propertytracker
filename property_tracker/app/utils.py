import pandas as pd
from typing import List
from .models import PropertyResult
from .api_clients import PropertyAPIClient
from .database import PropertyInquiry, SearchSession, get_db
from sqlalchemy.orm import Session
import time
import uuid
from datetime import datetime

def log_property_inquiry(
    db: Session,
    address: str,
    result: PropertyResult,
    search_type: str,
    session_id: str,
    user_ip: str,
    user_agent: str
) -> PropertyInquiry:
    """Log property inquiry to database"""
    
    inquiry = PropertyInquiry(
        address=address,
        search_type=search_type,
        status=result.status,
        price=result.price,
        property_type=result.property_type,
        bedrooms=result.bedrooms,
        bathrooms=result.bathrooms,
        square_feet=result.square_feet,
        zillow_link=result.zillow_link,
        realtor_link=result.realtor_link,
        api_source=result.api_source,
        success=result.status not in ["Error", "Not Found"],
        error_message=result.error,
        user_ip=user_ip,
        user_agent=user_agent
    )
    
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry

def create_search_session(
    db: Session,
    search_type: str,
    total_addresses: int,
    user_ip: str,
    user_agent: str,
    filename: str = None
) -> str:
    """Create a new search session and return session ID"""
    
    session_id = str(uuid.uuid4())
    
    session = SearchSession(
        session_id=session_id,
        search_type=search_type,
        total_addresses=total_addresses,
        user_ip=user_ip,
        user_agent=user_agent,
        filename=filename
    )
    
    db.add(session)
    db.commit()
    return session_id

def update_search_session(
    db: Session,
    session_id: str,
    successful: int,
    failed: int
):
    """Update search session with results"""
    
    session = db.query(SearchSession).filter(SearchSession.session_id == session_id).first()
    if session:
        session.successful_searches = successful
        session.failed_searches = failed
        session.completed_at = datetime.utcnow()
        db.commit()

def process_property_address(
    address: str, 
    api_client: PropertyAPIClient,
    db: Session = None,
    search_type: str = "single",
    session_id: str = None,
    user_ip: str = None,
    user_agent: str = None
) -> PropertyResult:
    """Process a single property address and return results"""
    
    # Generate links
    links = api_client.generate_links(address)
    
    # Initialize result
    result = PropertyResult(
        address=address,
        zillow_link=links["zillow_link"],
        realtor_link=links["realtor_link"]
    )
    
    try:
        # Search Zillow first
        zillow_data = api_client.search_zillow(address)
        
        if "error" not in zillow_data and zillow_data.get("results"):
            # Extract first result from Zillow
            first_result = zillow_data["results"][0]
            result.status = first_result.get("statusText", "Active")
            result.price = first_result.get("formattedPrice", "N/A")
            result.property_type = first_result.get("propertyType", "N/A")
            result.bedrooms = first_result.get("bedrooms")
            result.bathrooms = first_result.get("bathrooms")
            result.square_feet = first_result.get("livingArea")
            result.api_source = "zillow"
        else:
            # Try Realty Base if Zillow fails
            time.sleep(0.5)  # Rate limiting
            realty_data = api_client.search_realty_base(address)
            
            if "error" not in realty_data and realty_data.get("data"):
                # Process Realty Base data
                first_result = realty_data["data"][0] if realty_data["data"] else {}
                result.status = "Active" if first_result else "Not Found"
                result.price = first_result.get("price", "N/A")
                result.bedrooms = first_result.get("beds")
                result.bathrooms = first_result.get("baths")
                result.api_source = "realty_base"
            else:
                result.status = "Not Found"
                result.error = "No data found in either API"
    
    except Exception as e:
        result.error = str(e)
        result.status = "Error"
    
    # Log to database if db session provided
    if db and session_id:
        log_property_inquiry(
            db=db,
            address=address,
            result=result,
            search_type=search_type,
            session_id=session_id,
            user_ip=user_ip or "unknown",
            user_agent=user_agent or "unknown"
        )
    
    return result

def process_csv_file(
    file_path: str,
    db: Session = None,
    user_ip: str = None,
    user_agent: str = None,
    filename: str = None
) -> tuple[List[PropertyResult], str]:
    """Process uploaded CSV/Excel file and return property results with session ID"""
    
    try:
        # Read file (supports both CSV and Excel)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Find address column (flexible column names)
        address_columns = ['address', 'Address', 'property_address', 'Property Address', 'full_address']
        address_col = None
        
        for col in address_columns:
            if col in df.columns:
                address_col = col
                break
        
        if not address_col:
            # If no standard column found, use first column
            address_col = df.columns[0]
        
        addresses = df[address_col].dropna().tolist()
        
        # Create search session
        session_id = None
        if db:
            session_id = create_search_session(
                db=db,
                search_type="bulk",
                total_addresses=len(addresses),
                user_ip=user_ip or "unknown",
                user_agent=user_agent or "unknown",
                filename=filename
            )
        
        # Process each address
        api_client = PropertyAPIClient()
        results = []
        
        for i, address in enumerate(addresses):
            if i > 0:  # Rate limiting - wait between requests
                time.sleep(1)
            
            result = process_property_address(
                address=str(address),
                api_client=api_client,
                db=db,
                search_type="bulk",
                session_id=session_id,
                user_ip=user_ip,
                user_agent=user_agent
            )
            results.append(result)
        
        # Update session with final counts
        if db and session_id:
            successful = len([r for r in results if r.status not in ["Error", "Not Found"]])
            failed = len(results) - successful
            update_search_session(db, session_id, successful, failed)
        
        return results, session_id or str(uuid.uuid4())
    
    except Exception as e:
        # Return error result
        return [PropertyResult(
            address="File Error",
            status="Error",
            error=f"Failed to process file: {str(e)}"
        )], str(uuid.uuid4())