#!/usr/bin/env python3
"""
Debug session cookie authentication
"""

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

def test_cookie_auth():
    session = requests.Session()
    
    # Login and check cookies
    form_data = {
        "username": "fra_test_33f5ba61@example.com",
        "password": "FRATest123!"
    }
    
    print(f"🔐 Testing session cookie authentication...")
    print(f"Backend URL: {BACKEND_URL}")
    
    response = session.post(f"{BACKEND_URL}/api/auth/login", data=form_data)
    
    print(f"\n📋 Login Response:")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if 'Set-Cookie' in response.headers:
        print(f"Set-Cookie header: {response.headers['Set-Cookie']}")
    else:
        print("❌ No Set-Cookie header found")
    
    print(f"\n🍪 Session cookies after login:")
    for cookie in session.cookies:
        print(f"  {cookie.name}={cookie.value} (domain={cookie.domain}, secure={cookie.secure})")
    
    # Test authenticated request
    print(f"\n🧪 Testing authenticated request with cookies...")
    auth_response = session.get(f"{BACKEND_URL}/api/auth/me")
    print(f"Auth test status: {auth_response.status_code}")
    
    if auth_response.status_code == 200:
        print(f"✅ Session cookie authentication working!")
        print(f"User data: {auth_response.json()}")
    else:
        print(f"❌ Session cookie authentication failed")
        print(f"Response: {auth_response.text}")

if __name__ == "__main__":
    test_cookie_auth()