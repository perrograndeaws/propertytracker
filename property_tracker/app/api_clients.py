import requests
import os
from typing import Dict, Any, Optional
import time
import urllib.parse

class PropertyAPIClient:
    def __init__(self):
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.base_headers = {
            "X-RapidAPI-Key": self.rapidapi_key
        }
    
    def search_zillow(self, address: str) -> Dict[Any, Any]:
        """Search Zillow API for property by address"""
        headers = {
            **self.base_headers,
            "X-RapidAPI-Host": "zillow56.p.rapidapi.com"
        }
        
        url = "https://zillow56.p.rapidapi.com/search"
        querystring = {
            "location": address
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def search_realty_base(self, address: str) -> Dict[Any, Any]:
        """Search Realty Base API for property by address"""
        headers = {
            **self.base_headers,
            "X-RapidAPI-Host": "realty-base-us.p.rapidapi.com"
        }
        
        # Try to extract city and state from address
        parts = address.split(',')
        if len(parts) >= 2:
            city = parts[-2].strip()
            state = parts[-1].strip().split()[0]  # Get state code
        else:
            city = address
            state = ""
        
        url = "https://realty-base-us.p.rapidapi.com/search-buy"
        querystring = {
            "city": city,
            "state": state
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            return response.json() if response.status_code == 200 else {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def generate_links(self, address: str) -> Dict[str, str]:
        """Generate properly formatted direct links to Zillow and Realtor.com"""
        
        # URL encode the address for better link generation
        encoded_address = urllib.parse.quote_plus(address)
        
        # Clean address for Zillow (they prefer dashes and specific format)
        clean_address_zillow = address.replace(" ", "-").replace(",", "").lower()
        clean_address_zillow = ''.join(c for c in clean_address_zillow if c.isalnum() or c in '-')
        
        # Clean address for Realtor.com (they prefer underscores)
        clean_address_realtor = address.replace(" ", "_").replace(",", "").lower()
        clean_address_realtor = ''.join(c for c in clean_address_realtor if c.isalnum() or c in '_')
        
        # Generate search URLs (more reliable than direct property URLs)
        zillow_link = f"https://www.zillow.com/homes/{encoded_address}_rb/"
        realtor_link = f"https://www.realtor.com/realestateandhomes-search/{encoded_address}"
        
        return {
            "zillow_link": zillow_link,
            "realtor_link": realtor_link
        }