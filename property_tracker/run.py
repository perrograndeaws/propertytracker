#!/usr/bin/env python3
"""
Simple startup script for the Property Status Checker
"""

import uvicorn
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ['RAPIDAPI_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file")
        return
    
    print("🚀 Starting Property Status Checker...")
    print("📱 Web interface will be available at: http://localhost:8000")
    print("📊 Admin stats available at: http://localhost:8000/admin/stats")
    print("🔍 Health check available at: http://localhost:8000/health")
    print("\n" + "="*50)
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()