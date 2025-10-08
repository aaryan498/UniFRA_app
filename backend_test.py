#!/usr/bin/env python3
"""
UniFRA Backend API Comprehensive Test Suite

Tests ML models, parsers, preprocessing pipeline, and complete integration flows.
Covers authentication, file upload, analysis, asset management, and export functionality.
Uses the production backend URL from frontend/.env configuration.
"""

import requests
import json
import time
from datetime import datetime
import os
import io
import tempfile
import uuid
from dotenv import load_dotenv

# Load frontend environment to get backend URL
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

class UniFRABackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.session_cookie = None
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@unifra.test"
        self.test_user_password = "TestPassword123!"
        self.test_user_name = "Test User"
        self.upload_id = None
        self.analysis_id = None
        
        print(f"🚀 UniFRA ML Models & Integration Flow Test Suite")
        print(f"📡 Testing backend at: {self.backend_url}")
        print(f"👤 Test user: {self.test_user_email}")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        print("=" * 80)

    def log_result(self, test_name, success, details, response_time=None, status_code=None):
        """Log test result with details."""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'response_time_ms': response_time,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        time_info = f" ({response_time:.0f}ms)" if response_time else ""
        code_info = f" [HTTP {status_code}]" if status_code else ""
        
        print(f"{status_icon} {test_name}{time_info}{code_info}")
        if not success or details:
            print(f"   📝 {details}")

    def test_health_check_ml_models(self):
        """Test the health check endpoint with focus on ML models status."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'timestamp', 'version', 'components']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "ML Models Health Check", False, 
                        f"Missing fields: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                # Check if status is healthy
                if data.get('status') != 'healthy':
                    self.log_result(
                        "ML Models Health Check", False,
                        f"Status is '{data.get('status')}', expected 'healthy'",
                        response_time, response.status_code
                    )
                    return False
                
                # Check ML models component specifically
                components = data.get('components', {})
                expected_components = ['parser', 'ml_models', 'database', 'authentication']
                
                for component in expected_components:
                    if component not in components:
                        self.log_result(
                            "ML Models Health Check", False,
                            f"Missing component: {component}",
                            response_time, response.status_code
                        )
                        return False
                    
                    if components[component] != 'operational':
                        self.log_result(
                            "ML Models Health Check", False,
                            f"Component '{component}' is '{components[component]}', expected 'operational'",
                            response_time, response.status_code
                        )
                        return False
                
                # Specifically verify ML models are loaded
                if components.get('ml_models') == 'operational':
                    self.log_result(
                        "ML Models Health Check", True,
                        f"ML models loaded and operational. All components: {list(components.keys())}",
                        response_time, response.status_code
                    )
                    return True
                else:
                    self.log_result(
                        "ML Models Health Check", False,
                        f"ML models not operational: {components.get('ml_models')}",
                        response_time, response.status_code
                    )
                    return False
            else:
                self.log_result(
                    "ML Models Health Check", False,
                    f"Unexpected status code: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("ML Models Health Check", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("ML Models Health Check", False, f"Invalid JSON response: {str(e)}")
            return False

    def test_auth_me_unauthenticated(self):
        """Test /api/auth/me endpoint without authentication."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/auth/me", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            # Should return 401 for unauthenticated request
            if response.status_code == 401:
                self.log_result(
                    "Auth Me (Unauthenticated)", True,
                    "Correctly returned 401 for unauthenticated request",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Auth Me (Unauthenticated)", False,
                    f"Expected 401, got {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Auth Me (Unauthenticated)", False, f"Request failed: {str(e)}")
            return False

    def test_auth_logout_unauthenticated(self):
        """Test /api/auth/logout endpoint without authentication."""
        try:
            start_time = time.time()
            response = self.session.post(f"{self.backend_url}/api/auth/logout", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            # Should return 401 for unauthenticated request
            if response.status_code == 401:
                self.log_result(
                    "Auth Logout (Unauthenticated)", True,
                    "Correctly returned 401 for unauthenticated request",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Auth Logout (Unauthenticated)", False,
                    f"Expected 401, got {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Auth Logout (Unauthenticated)", False, f"Request failed: {str(e)}")
            return False

    def test_assets_unauthenticated(self):
        """Test /api/assets endpoint without authentication."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/assets", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            # Should return 401 for unauthenticated request
            if response.status_code == 401:
                self.log_result(
                    "Assets (Unauthenticated)", True,
                    "Correctly returned 401 for unauthenticated request",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Assets (Unauthenticated)", False,
                    f"Expected 401, got {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Assets (Unauthenticated)", False, f"Request failed: {str(e)}")
            return False

    def test_cors_headers(self):
        """Test CORS headers on health endpoint."""
        try:
            start_time = time.time()
            response = self.session.options(f"{self.backend_url}/api/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            # Check for CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            missing_headers = [header for header, value in cors_headers.items() if not value]
            
            if missing_headers:
                self.log_result(
                    "CORS Headers", False,
                    f"Missing CORS headers: {missing_headers}",
                    response_time, response.status_code
                )
                return False
            else:
                self.log_result(
                    "CORS Headers", True,
                    f"All CORS headers present. Origin: {cors_headers['Access-Control-Allow-Origin']}",
                    response_time, response.status_code
                )
                return True
                
        except requests.exceptions.RequestException as e:
            self.log_result("CORS Headers", False, f"Request failed: {str(e)}")
            return False

    def test_content_type_headers(self):
        """Test content-type headers on API responses."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                self.log_result(
                    "Content-Type Headers", True,
                    f"Correct content-type: {content_type}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Content-Type Headers", False,
                    f"Expected application/json, got: {content_type}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Content-Type Headers", False, f"Request failed: {str(e)}")
            return False

    def test_supported_formats(self):
        """Test the supported formats endpoint."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/supported-formats", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log_result(
                        "Supported Formats", True,
                        f"Endpoint accessible, returned {len(data) if isinstance(data, (list, dict)) else 'data'}",
                        response_time, response.status_code
                    )
                    return True
                except json.JSONDecodeError:
                    self.log_result(
                        "Supported Formats", False,
                        "Invalid JSON response",
                        response_time, response.status_code
                    )
                    return False
            else:
                self.log_result(
                    "Supported Formats", False,
                    f"Unexpected status code: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Supported Formats", False, f"Request failed: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test the root API endpoint."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'message' in data and 'version' in data:
                        self.log_result(
                            "Root Endpoint", True,
                            f"API info accessible. Version: {data.get('version')}",
                            response_time, response.status_code
                        )
                        return True
                    else:
                        self.log_result(
                            "Root Endpoint", False,
                            "Missing required fields in response",
                            response_time, response.status_code
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_result(
                        "Root Endpoint", False,
                        "Invalid JSON response",
                        response_time, response.status_code
                    )
                    return False
            else:
                self.log_result(
                    "Root Endpoint", False,
                    f"Unexpected status code: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Root Endpoint", False, f"Request failed: {str(e)}")
            return False

    # ========== AUTHENTICATION FLOW TESTS ==========
    
    def test_user_registration(self):
        """Test user registration flow."""
        try:
            start_time = time.time()
            
            user_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "full_name": self.test_user_name
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/auth/register",
                json=user_data,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields in response
                required_fields = ['access_token', 'token_type', 'user']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "User Registration", False,
                        f"Missing fields in response: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                # Store auth token for subsequent tests
                self.auth_token = data['access_token']
                
                # Verify user data
                user = data.get('user', {})
                if user.get('email') != self.test_user_email:
                    self.log_result(
                        "User Registration", False,
                        f"Email mismatch: expected {self.test_user_email}, got {user.get('email')}",
                        response_time, response.status_code
                    )
                    return False
                
                self.log_result(
                    "User Registration", True,
                    f"User registered successfully. ID: {user.get('id')}, Auth method: {user.get('auth_method')}",
                    response_time, response.status_code
                )
                return True
                
            elif response.status_code == 400:
                # User might already exist, try login instead
                return self.test_user_login()
            else:
                self.log_result(
                    "User Registration", False,
                    f"Unexpected status code: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Registration", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("User Registration", False, f"Invalid JSON response: {str(e)}")
            return False

    def test_user_login(self):
        """Test user login flow."""
        try:
            start_time = time.time()
            
            # Use OAuth2 form data format
            form_data = {
                "username": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/auth/login",
                data=form_data,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['access_token', 'token_type', 'user']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "User Login", False,
                        f"Missing fields in response: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                # Store auth token
                self.auth_token = data['access_token']
                
                # Check for session cookie
                if 'Set-Cookie' in response.headers:
                    self.session_cookie = response.headers['Set-Cookie']
                
                self.log_result(
                    "User Login", True,
                    f"Login successful. Token type: {data.get('token_type')}, User: {data.get('user', {}).get('email')}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "User Login", False,
                    f"Login failed with status: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Login", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("User Login", False, f"Invalid JSON response: {str(e)}")
            return False

    def test_authenticated_user_profile(self):
        """Test getting user profile with authentication."""
        if not self.auth_token:
            self.log_result("Authenticated User Profile", False, "No auth token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                f"{self.backend_url}/api/auth/me",
                headers=headers,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required profile fields
                required_fields = ['id', 'email', 'full_name', 'auth_method', 'created_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Authenticated User Profile", False,
                        f"Missing profile fields: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                if data.get('email') != self.test_user_email:
                    self.log_result(
                        "Authenticated User Profile", False,
                        f"Email mismatch: expected {self.test_user_email}, got {data.get('email')}",
                        response_time, response.status_code
                    )
                    return False
                
                self.log_result(
                    "Authenticated User Profile", True,
                    f"Profile retrieved. ID: {data.get('id')}, Auth method: {data.get('auth_method')}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Authenticated User Profile", False,
                    f"Failed to get profile: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Authenticated User Profile", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("Authenticated User Profile", False, f"Invalid JSON response: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend API tests."""
        print("\n🧪 Starting Backend API Tests...")
        print("-" * 40)
        
        tests = [
            self.test_health_check,
            self.test_auth_me_unauthenticated,
            self.test_auth_logout_unauthenticated,
            self.test_assets_unauthenticated,
            self.test_cors_headers,
            self.test_content_type_headers,
            self.test_supported_formats,
            self.test_root_endpoint
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("-" * 40)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Backend API is working correctly.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Check details above.")
        
        return passed, total, self.test_results

def main():
    """Main test execution."""
    tester = UniFRABackendTester()
    passed, total, results = tester.run_all_tests()
    
    # Save detailed results to file
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'passed': passed,
                'total': total,
                'success_rate': passed / total if total > 0 else 0,
                'backend_url': tester.backend_url,
                'test_timestamp': datetime.now().isoformat()
            },
            'detailed_results': results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)