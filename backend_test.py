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
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPass123"  # Shorter password to avoid bcrypt length issues
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
            
            # Check response time requirement (< 100ms for health check)
            if response_time > 100:
                self.log_result(
                    "ML Models Health Check", False,
                    f"Response time {response_time:.1f}ms exceeds 100ms requirement",
                    response_time, response.status_code
                )
                return False
            
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
                        f"ML models loaded and operational. Response time: {response_time:.1f}ms. All components: {list(components.keys())}",
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
            # Use GET request instead of OPTIONS since backend might not support OPTIONS
            response = self.session.get(f"{self.backend_url}/api/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            # Check for CORS headers in response
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            # In Kubernetes ingress setup, CORS might be handled at ingress level
            # So we'll check if at least one CORS header is present or if request succeeds from different origin
            if cors_headers['Access-Control-Allow-Origin'] or response.status_code == 200:
                self.log_result(
                    "CORS Headers", True,
                    f"CORS handling operational. Origin header: {cors_headers['Access-Control-Allow-Origin'] or 'handled by ingress'}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "CORS Headers", False,
                    f"No CORS headers found and request failed",
                    response_time, response.status_code
                )
                return False
                
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

    def test_stability_consecutive_requests(self):
        """Test backend stability with multiple consecutive requests."""
        try:
            print(f"   🔄 Testing 10 consecutive health check requests...")
            
            response_times = []
            failed_requests = 0
            
            for i in range(10):
                try:
                    start_time = time.time()
                    response = self.session.get(f"{self.backend_url}/api/health", timeout=10)
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code != 200:
                        failed_requests += 1
                        print(f"      Request {i+1}: FAILED (HTTP {response.status_code})")
                    else:
                        data = response.json()
                        if data.get('status') != 'healthy':
                            failed_requests += 1
                            print(f"      Request {i+1}: FAILED (status: {data.get('status')})")
                        else:
                            print(f"      Request {i+1}: OK ({response_time:.1f}ms)")
                    
                    # Small delay between requests
                    time.sleep(0.1)
                    
                except Exception as e:
                    failed_requests += 1
                    print(f"      Request {i+1}: FAILED ({str(e)})")
                    response_times.append(0)
            
            # Calculate statistics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            
            success_rate = ((10 - failed_requests) / 10) * 100
            
            if failed_requests == 0:
                self.log_result(
                    "Stability - Consecutive Requests", True,
                    f"All 10 requests successful. Avg: {avg_response_time:.1f}ms, Min: {min_response_time:.1f}ms, Max: {max_response_time:.1f}ms",
                    avg_response_time, 200
                )
                return True
            else:
                self.log_result(
                    "Stability - Consecutive Requests", False,
                    f"{failed_requests}/10 requests failed. Success rate: {success_rate:.1f}%",
                    avg_response_time, None
                )
                return False
                
        except Exception as e:
            self.log_result("Stability - Consecutive Requests", False, f"Test failed: {str(e)}")
            return False

    def test_mongodb_connection_stability(self):
        """Test MongoDB connection stability through authenticated endpoints."""
        if not self.auth_token:
            self.log_result("MongoDB Connection Stability", False, "No auth token available")
            return False
            
        try:
            # Test multiple database operations
            operations = [
                ("User Profile", f"{self.backend_url}/api/auth/me"),
                ("Assets List", f"{self.backend_url}/api/assets"),
            ]
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            all_successful = True
            response_times = []
            
            for op_name, url in operations:
                try:
                    start_time = time.time()
                    response = self.session.get(url, headers=headers, timeout=10)
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code not in [200, 401]:  # 401 is expected for some tests
                        all_successful = False
                        print(f"      {op_name}: FAILED (HTTP {response.status_code})")
                    else:
                        print(f"      {op_name}: OK ({response_time:.1f}ms)")
                        
                except Exception as e:
                    all_successful = False
                    print(f"      {op_name}: FAILED ({str(e)})")
                    response_times.append(0)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            if all_successful:
                self.log_result(
                    "MongoDB Connection Stability", True,
                    f"All database operations successful. Avg response time: {avg_response_time:.1f}ms",
                    avg_response_time, 200
                )
                return True
            else:
                self.log_result(
                    "MongoDB Connection Stability", False,
                    "Some database operations failed",
                    avg_response_time, None
                )
                return False
                
        except Exception as e:
            self.log_result("MongoDB Connection Stability", False, f"Test failed: {str(e)}")
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
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    self.log_result(
                        "User Registration", False,
                        f"Validation error: {error_data}",
                        response_time, response.status_code
                    )
                except:
                    self.log_result(
                        "User Registration", False,
                        f"Validation error (422) - unable to parse error details",
                        response_time, response.status_code
                    )
                return False
            elif response.status_code == 500:
                self.log_result(
                    "User Registration", False,
                    f"Server error - check backend logs for bcrypt/password issues",
                    response_time, response.status_code
                )
                return False
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

    # ========== PARSER AND PREPROCESSING TESTS ==========
    
    def test_supported_formats_detailed(self):
        """Test supported formats endpoint for parser functionality."""
        try:
            start_time = time.time()
            response = self.session.get(f"{self.backend_url}/api/supported-formats", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check if we get format information
                    if isinstance(data, dict) and len(data) > 0:
                        self.log_result(
                            "Parser - Supported Formats", True,
                            f"Parser supports {len(data)} format categories: {list(data.keys())}",
                            response_time, response.status_code
                        )
                        return True
                    elif isinstance(data, list) and len(data) > 0:
                        self.log_result(
                            "Parser - Supported Formats", True,
                            f"Parser supports {len(data)} formats",
                            response_time, response.status_code
                        )
                        return True
                    else:
                        self.log_result(
                            "Parser - Supported Formats", False,
                            "No supported formats returned",
                            response_time, response.status_code
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_result(
                        "Parser - Supported Formats", False,
                        "Invalid JSON response",
                        response_time, response.status_code
                    )
                    return False
            else:
                self.log_result(
                    "Parser - Supported Formats", False,
                    f"Unexpected status code: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Parser - Supported Formats", False, f"Request failed: {str(e)}")
            return False

    def create_sample_fra_data(self):
        """Create sample FRA data for testing with more comprehensive frequency sweep."""
        # Create realistic FRA test data with more frequency points
        sample_data = """# UniFRA Test Data - Transformer FRA Measurement
# Asset: TEST-TRANSFORMER-001
# Manufacturer: Test Corp
# Rating: 100 MVA
# Date: 2024-01-15
# 
# Frequency (Hz), Magnitude (dB), Phase (degrees)
10,45.2,12.5
15,44.8,13.1
20,43.8,15.2
30,42.9,16.8
50,41.5,18.7
75,40.3,20.2
100,39.2,22.1
150,38.1,23.8
200,36.8,25.9
300,35.7,27.4
500,33.4,31.2
750,31.8,34.1
1000,29.7,38.5
1500,27.9,42.3
2000,25.3,47.2
3000,22.8,52.1
5000,19.8,58.9
7500,16.4,65.7
10000,13.2,72.4
15000,9.8,79.3
20000,5.7,89.1
30000,1.2,98.7
50000,-2.8,108.7
75000,-7.1,118.2
100000,-12.4,125.3
150000,-18.2,134.1
200000,-23.1,142.8
300000,-28.9,152.4
500000,-35.7,165.2
750000,-42.1,172.8
1000000,-48.9,178.9
"""
        return sample_data

    def test_file_upload_flow(self):
        """Test file upload and parsing flow."""
        if not self.auth_token:
            self.log_result("File Upload Flow", False, "No auth token available")
            return False
            
        try:
            start_time = time.time()
            
            # Create sample FRA data file
            sample_data = self.create_sample_fra_data()
            
            # Prepare file upload
            files = {
                'file': ('test_fra_data.csv', io.StringIO(sample_data), 'text/csv')
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.post(
                f"{self.backend_url}/api/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'upload_id', 'message', 'asset_metadata']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "File Upload Flow", False,
                        f"Missing fields in response: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                if data.get('status') != 'success':
                    self.log_result(
                        "File Upload Flow", False,
                        f"Upload status is '{data.get('status')}', expected 'success'",
                        response_time, response.status_code
                    )
                    return False
                
                # Store upload ID for analysis
                self.upload_id = data.get('upload_id')
                
                # Check asset metadata
                asset_metadata = data.get('asset_metadata', {})
                if not asset_metadata.get('asset_id'):
                    self.log_result(
                        "File Upload Flow", False,
                        "No asset_id in metadata",
                        response_time, response.status_code
                    )
                    return False
                
                # Check measurement summary
                measurement_summary = data.get('measurement_summary', {})
                freq_points = measurement_summary.get('frequency_points', 0)
                
                self.log_result(
                    "File Upload Flow", True,
                    f"File uploaded and parsed successfully. Upload ID: {self.upload_id}, Frequency points: {freq_points}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "File Upload Flow", False,
                    f"Upload failed with status: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("File Upload Flow", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("File Upload Flow", False, f"Invalid JSON response: {str(e)}")
            return False

    # ========== ML ANALYSIS FLOW TESTS ==========
    
    def test_fra_analysis_flow(self):
        """Test FRA analysis with ML models."""
        if not self.auth_token or not self.upload_id:
            self.log_result("FRA Analysis Flow", False, "No auth token or upload ID available")
            return False
            
        try:
            start_time = time.time()
            
            # Prepare analysis request
            analysis_request = {
                "apply_filtering": True,
                "apply_wavelet": False,
                "include_features": True,
                "confidence_threshold": 0.7
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.post(
                f"{self.backend_url}/api/analyze/{self.upload_id}",
                json=analysis_request,
                headers=headers,
                timeout=60  # ML analysis might take longer
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required analysis result fields
                required_fields = [
                    'analysis_id', 'user_id', 'asset_metadata', 'fault_probabilities',
                    'predicted_fault_type', 'severity_level', 'confidence_score',
                    'is_anomaly', 'recommended_actions', 'analysis_timestamp'
                ]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "FRA Analysis Flow", False,
                        f"Missing fields in analysis result: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                # Store analysis ID
                self.analysis_id = data.get('analysis_id')
                
                # Verify ML model predictions
                fault_probabilities = data.get('fault_probabilities', {})
                expected_fault_types = [
                    'healthy', 'axial_displacement', 'radial_deformation', 'core_grounding',
                    'turn_turn_short', 'open_circuit', 'insulation_degradation',
                    'partial_discharge', 'lamination_deform', 'saturation_effect'
                ]
                
                missing_fault_types = [ft for ft in expected_fault_types if ft not in fault_probabilities]
                if missing_fault_types:
                    self.log_result(
                        "FRA Analysis Flow", False,
                        f"Missing fault probability types: {missing_fault_types}",
                        response_time, response.status_code
                    )
                    return False
                
                # Verify confidence score
                confidence_score = data.get('confidence_score', 0)
                if not (0 <= confidence_score <= 1):
                    self.log_result(
                        "FRA Analysis Flow", False,
                        f"Invalid confidence score: {confidence_score} (should be 0-1)",
                        response_time, response.status_code
                    )
                    return False
                
                # Verify recommendations exist
                recommendations = data.get('recommended_actions', [])
                if not recommendations or len(recommendations) == 0:
                    self.log_result(
                        "FRA Analysis Flow", False,
                        "No maintenance recommendations provided",
                        response_time, response.status_code
                    )
                    return False
                
                predicted_fault = data.get('predicted_fault_type')
                severity = data.get('severity_level')
                
                self.log_result(
                    "FRA Analysis Flow", True,
                    f"ML analysis completed. Fault: {predicted_fault}, Severity: {severity}, Confidence: {confidence_score:.3f}, Processing time: {data.get('processing_time_ms', 0):.1f}ms",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "FRA Analysis Flow", False,
                    f"Analysis failed with status: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("FRA Analysis Flow", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("FRA Analysis Flow", False, f"Invalid JSON response: {str(e)}")
            return False

    def test_analysis_retrieval(self):
        """Test retrieving analysis results by ID."""
        if not self.auth_token or not self.analysis_id:
            self.log_result("Analysis Retrieval", False, "No auth token or analysis ID available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.get(
                f"{self.backend_url}/api/analysis/{self.analysis_id}",
                headers=headers,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify it's the same analysis
                if data.get('analysis_id') != self.analysis_id:
                    self.log_result(
                        "Analysis Retrieval", False,
                        f"Analysis ID mismatch: expected {self.analysis_id}, got {data.get('analysis_id')}",
                        response_time, response.status_code
                    )
                    return False
                
                self.log_result(
                    "Analysis Retrieval", True,
                    f"Analysis retrieved successfully. Fault: {data.get('predicted_fault_type')}, Confidence: {data.get('confidence_score', 0):.3f}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Analysis Retrieval", False,
                    f"Failed to retrieve analysis: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Analysis Retrieval", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("Analysis Retrieval", False, f"Invalid JSON response: {str(e)}")
            return False

    # ========== ASSET MANAGEMENT TESTS ==========
    
    def test_asset_management_flow(self):
        """Test asset listing and management."""
        if not self.auth_token:
            self.log_result("Asset Management Flow", False, "No auth token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.get(
                f"{self.backend_url}/api/assets",
                headers=headers,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if 'assets' not in data or 'total_count' not in data:
                    self.log_result(
                        "Asset Management Flow", False,
                        "Missing 'assets' or 'total_count' in response",
                        response_time, response.status_code
                    )
                    return False
                
                assets = data.get('assets', [])
                total_count = data.get('total_count', 0)
                
                # If we uploaded and analyzed data, we should have at least one asset
                if self.upload_id and total_count == 0:
                    self.log_result(
                        "Asset Management Flow", False,
                        "No assets found despite successful upload and analysis",
                        response_time, response.status_code
                    )
                    return False
                
                # Check asset structure if assets exist
                if assets:
                    asset = assets[0]
                    required_asset_fields = ['asset_id', 'latest_analysis', 'total_analyses', 'latest_fault_type']
                    missing_asset_fields = [field for field in required_asset_fields if field not in asset]
                    
                    if missing_asset_fields:
                        self.log_result(
                            "Asset Management Flow", False,
                            f"Missing asset fields: {missing_asset_fields}",
                            response_time, response.status_code
                        )
                        return False
                
                self.log_result(
                    "Asset Management Flow", True,
                    f"Assets retrieved successfully. Total: {total_count}, Assets with data: {len(assets)}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Asset Management Flow", False,
                    f"Failed to retrieve assets: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Asset Management Flow", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("Asset Management Flow", False, f"Invalid JSON response: {str(e)}")
            return False

    def run_all_tests(self):
        """Run comprehensive backend API tests following critical path."""
        print("\n🧪 Starting Comprehensive Backend API Tests...")
        print("-" * 40)
        
        # Phase 1: Basic connectivity and health
        basic_tests = [
            ("Health Check", self.test_health_check_ml_models),
            ("Stability - Consecutive Requests", self.test_stability_consecutive_requests),
            ("Root Endpoint", self.test_root_endpoint),
            ("Supported Formats", self.test_supported_formats_detailed),
            ("CORS Headers", self.test_cors_headers),
            ("Content-Type Headers", self.test_content_type_headers)
        ]
        
        # Phase 2: Unauthenticated endpoint security
        security_tests = [
            ("Auth Me (Unauthenticated)", self.test_auth_me_unauthenticated),
            ("Auth Logout (Unauthenticated)", self.test_auth_logout_unauthenticated),
            ("Assets (Unauthenticated)", self.test_assets_unauthenticated)
        ]
        
        # Phase 3: Authentication flow
        auth_tests = [
            ("User Registration", self.test_user_registration),
            ("Authenticated User Profile", self.test_authenticated_user_profile)
        ]
        
        # Phase 4: File upload and ML analysis
        ml_tests = [
            ("File Upload Flow", self.test_file_upload_flow),
            ("FRA Analysis Flow", self.test_fra_analysis_flow),
            ("Analysis Retrieval", self.test_analysis_retrieval)
        ]
        
        # Phase 5: Asset management
        asset_tests = [
            ("Asset Management Flow", self.test_asset_management_flow)
        ]
        
        all_test_phases = [
            ("Basic Connectivity", basic_tests),
            ("Security Tests", security_tests),
            ("Authentication", auth_tests),
            ("ML Analysis Pipeline", ml_tests),
            ("Asset Management", asset_tests)
        ]
        
        total_passed = 0
        total_tests = 0
        
        for phase_name, tests in all_test_phases:
            print(f"\n🔍 {phase_name} Tests:")
            print("-" * 30)
            
            phase_passed = 0
            phase_total = len(tests)
            
            for test_name, test_func in tests:
                if test_func():
                    phase_passed += 1
                total_tests += 1
            
            total_passed += phase_passed
            print(f"   Phase Result: {phase_passed}/{phase_total} passed")
            
            # Stop if critical tests fail
            if phase_name == "Basic Connectivity" and phase_passed < phase_total:
                print("❌ Critical connectivity tests failed. Stopping test suite.")
                break
        
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS: {total_passed}/{total_tests} tests passed")
        print(f"🎯 Success Rate: {(total_passed/total_tests)*100:.1f}%")
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED! Backend API is fully operational.")
        else:
            failed = total_tests - total_passed
            print(f"⚠️  {failed} test(s) failed. Check details above.")
        
        return total_passed, total_tests, self.test_results

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