#!/usr/bin/env python3
"""
CORS Headers Test for UniFRA Backend
"""

import requests
import os
from dotenv import load_dotenv

# Load frontend environment to get backend URL
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

def test_cors_headers():
    """Test CORS headers with GET request."""
    try:
        print(f"Testing CORS headers at: {BACKEND_URL}/api/health")
        
        # Test with GET request
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower() or 'cors' in header.lower():
                print(f"  {header}: {value}")
        
        # Check specific CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print("\nCORS Headers Analysis:")
        for header, value in cors_headers.items():
            status = "✅ Present" if value else "❌ Missing"
            print(f"  {header}: {value or 'Not found'} - {status}")
        
        # Test with OPTIONS request
        print(f"\nTesting OPTIONS request...")
        options_response = requests.options(f"{BACKEND_URL}/api/health", timeout=10)
        print(f"OPTIONS Status Code: {options_response.status_code}")
        
        if options_response.status_code == 405:
            print("OPTIONS method not allowed - this is normal for some FastAPI configurations")
        
        return response.headers
        
    except Exception as e:
        print(f"Error testing CORS: {e}")
        return None

if __name__ == "__main__":
    test_cors_headers()