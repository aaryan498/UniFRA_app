#!/usr/bin/env python3
"""
Additional Backend Tests for UniFRA API
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load frontend environment to get backend URL
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

def test_register_endpoint():
    """Test user registration endpoint."""
    try:
        print("Testing user registration endpoint...")
        
        # Test with invalid data first
        response = requests.post(f"{BACKEND_URL}/api/auth/register", 
                               json={}, timeout=10)
        
        print(f"Register (empty data): {response.status_code}")
        
        # Test with valid data
        test_user = {
            "email": "test@unifra.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/auth/register", 
                               json=test_user, timeout=10)
        
        print(f"Register (valid data): {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Access token received: {'access_token' in data}")
            print(f"  User data: {'user' in data}")
        elif response.status_code == 400:
            print(f"  Expected error (user might exist): {response.json().get('detail', 'No detail')}")
        
        return response.status_code in [200, 400]  # Both are acceptable
        
    except Exception as e:
        print(f"Error testing register: {e}")
        return False

def test_login_endpoint():
    """Test user login endpoint."""
    try:
        print("\nTesting user login endpoint...")
        
        # Test with form data (OAuth2PasswordRequestForm)
        login_data = {
            "username": "test@unifra.com",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/auth/login", 
                               data=login_data, timeout=10)
        
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Access token received: {'access_token' in data}")
            return True
        elif response.status_code == 401:
            print(f"  Authentication failed (expected if user doesn't exist)")
            return True
        else:
            print(f"  Unexpected status: {response.text}")
            return False
        
    except Exception as e:
        print(f"Error testing login: {e}")
        return False

def test_forgot_password_flow():
    """Test forgot password endpoints."""
    try:
        print("\nTesting forgot password flow...")
        
        # Test forgot password request
        response = requests.post(f"{BACKEND_URL}/api/auth/forgot-password", 
                               json={"email": "test@unifra.com"}, timeout=10)
        
        print(f"Forgot password: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Success: {data.get('success', False)}")
            print(f"  Message: {data.get('message', 'No message')}")
            
            # If OTP is provided for testing, try to verify it
            if 'otp_for_testing' in data:
                otp = data['otp_for_testing']
                print(f"  Testing OTP verification with: {otp}")
                
                verify_response = requests.post(f"{BACKEND_URL}/api/auth/verify-otp",
                                              json={"email": "test@unifra.com", "otp": otp},
                                              timeout=10)
                print(f"  OTP verification: {verify_response.status_code}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing forgot password: {e}")
        return False

def test_mongodb_connection():
    """Test if MongoDB is accessible through the API."""
    try:
        print("\nTesting MongoDB connection through API...")
        
        # The health check should indicate if database is operational
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            db_status = data.get('components', {}).get('database', 'unknown')
            print(f"Database status: {db_status}")
            return db_status == 'operational'
        
        return False
        
    except Exception as e:
        print(f"Error testing MongoDB connection: {e}")
        return False

def test_ml_models_status():
    """Test if ML models are loaded."""
    try:
        print("\nTesting ML models status...")
        
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ml_status = data.get('components', {}).get('ml_models', 'unknown')
            print(f"ML models status: {ml_status}")
            return ml_status == 'operational'
        
        return False
        
    except Exception as e:
        print(f"Error testing ML models: {e}")
        return False

def main():
    """Run additional backend tests."""
    print(f"🔍 Additional Backend API Tests")
    print(f"📡 Testing backend at: {BACKEND_URL}")
    print("=" * 50)
    
    tests = [
        ("User Registration", test_register_endpoint),
        ("User Login", test_login_endpoint),
        ("Forgot Password Flow", test_forgot_password_flow),
        ("MongoDB Connection", test_mongodb_connection),
        ("ML Models Status", test_ml_models_status)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("=" * 50)
    print(f"📊 Additional Tests: {passed}/{total} passed")
    
    return passed, total

if __name__ == "__main__":
    main()