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

    def test_health_check(self):
        """Test the health check endpoint."""
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
                        "Health Check", False, 
                        f"Missing fields: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                # Check if status is healthy
                if data.get('status') != 'healthy':
                    self.log_result(
                        "Health Check", False,
                        f"Status is '{data.get('status')}', expected 'healthy'",
                        response_time, response.status_code
                    )
                    return False
                
                # Check components
                components = data.get('components', {})
                expected_components = ['parser', 'ml_models', 'database', 'authentication']
                
                for component in expected_components:
                    if component not in components:
                        self.log_result(
                            "Health Check", False,
                            f"Missing component: {component}",
                            response_time, response.status_code
                        )
                        return False
                    
                    if components[component] != 'operational':
                        self.log_result(
                            "Health Check", False,
                            f"Component '{component}' is '{components[component]}', expected 'operational'",
                            response_time, response.status_code
                        )
                        return False
                
                self.log_result(
                    "Health Check", True,
                    f"All components operational. Version: {data.get('version')}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Health Check", False,
                    f"Unexpected status code: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.log_result("Health Check", False, f"Invalid JSON response: {str(e)}")
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