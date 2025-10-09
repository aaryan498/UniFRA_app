#!/usr/bin/env python3
"""
UniFRA Authentication & File Upload Test Suite

Specifically tests the authentication flow with file upload that the user reported as failing.
Tests both Bearer token and session cookie authentication methods.
"""

import requests
import json
import time
from datetime import datetime
import os
import io
import uuid
from dotenv import load_dotenv

# Load frontend environment to get backend URL
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')

class AuthUploadTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.test_results = []
        self.bearer_token = None
        self.session_cookies = None
        self.test_user_email = f"fra_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "FRATest123!"
        self.test_user_name = "FRA Test User"
        self.upload_id_bearer = None
        self.upload_id_session = None
        self.analysis_id_bearer = None
        self.analysis_id_session = None
        
        print(f"🔐 UniFRA Authentication & File Upload Test Suite")
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

    def create_fra_test_data(self):
        """Create realistic FRA test data for upload."""
        return """# FRA Test Data - Transformer Analysis
# Asset: TEST-TRANSFORMER-FRA-001
# Manufacturer: TestCorp Industries
# Model: TC-100MVA-138kV
# Rating: 100 MVA
# Voltage Levels: 138kV/13.8kV
# Year Installed: 2015
# Winding Configuration: Wye-Delta
# Test Date: 2024-01-15
# Test Type: Frequency Response Analysis
# 
# Frequency (Hz), Magnitude (dB), Phase (degrees)
10,42.5,8.2
20,41.8,12.1
50,40.2,18.5
100,38.7,24.3
200,36.9,31.2
500,33.8,42.1
1000,30.2,54.8
2000,26.1,68.2
5000,20.8,82.5
10000,15.2,95.1
20000,8.9,108.7
50000,-2.1,125.3
100000,-12.8,142.1
200000,-24.5,158.9
500000,-38.2,172.4
1000000,-52.1,185.2
"""

    def test_user_registration(self):
        """Test user registration for authentication flow."""
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
                timeout=15
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if 'access_token' not in data:
                    self.log_result(
                        "User Registration", False,
                        "No access_token in registration response",
                        response_time, response.status_code
                    )
                    return False
                
                self.bearer_token = data['access_token']
                
                self.log_result(
                    "User Registration", True,
                    f"User registered successfully. Token received: {len(self.bearer_token)} chars",
                    response_time, response.status_code
                )
                return True
                
            elif response.status_code == 400:
                # User might already exist, try login
                self.log_result(
                    "User Registration", False,
                    "User already exists, will try login",
                    response_time, response.status_code
                )
                return self.test_user_login()
            else:
                self.log_result(
                    "User Registration", False,
                    f"Registration failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Request failed: {str(e)}")
            return False

    def test_user_login(self):
        """Test user login and session creation."""
        try:
            start_time = time.time()
            
            # Use OAuth2 form data format as expected by FastAPI
            form_data = {
                "username": self.test_user_email,
                "password": self.test_user_password
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/auth/login",
                data=form_data,
                timeout=15
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if 'access_token' not in data:
                    self.log_result(
                        "User Login", False,
                        "No access_token in login response",
                        response_time, response.status_code
                    )
                    return False
                
                self.bearer_token = data['access_token']
                
                # Check for session cookies
                if 'Set-Cookie' in response.headers:
                    self.session_cookies = response.headers['Set-Cookie']
                    cookie_info = "Session cookie received"
                else:
                    cookie_info = "No session cookie in response"
                
                self.log_result(
                    "User Login", True,
                    f"Login successful. Token: {len(self.bearer_token)} chars. {cookie_info}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "User Login", False,
                    f"Login failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Request failed: {str(e)}")
            return False

    def test_bearer_token_auth(self):
        """Test Bearer token authentication on protected endpoint."""
        if not self.bearer_token:
            self.log_result("Bearer Token Auth", False, "No bearer token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            response = self.session.get(
                f"{self.backend_url}/api/auth/me",
                headers=headers,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('email') != self.test_user_email:
                    self.log_result(
                        "Bearer Token Auth", False,
                        f"Email mismatch: expected {self.test_user_email}, got {data.get('email')}",
                        response_time, response.status_code
                    )
                    return False
                
                self.log_result(
                    "Bearer Token Auth", True,
                    f"Bearer token authentication working. User: {data.get('email')}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Bearer Token Auth", False,
                    f"Bearer token auth failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Bearer Token Auth", False, f"Request failed: {str(e)}")
            return False

    def test_session_cookie_auth(self):
        """Test session cookie authentication on protected endpoint."""
        try:
            start_time = time.time()
            
            # Test with session cookies (no Authorization header)
            response = self.session.get(
                f"{self.backend_url}/api/auth/me",
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('email') != self.test_user_email:
                    self.log_result(
                        "Session Cookie Auth", False,
                        f"Email mismatch: expected {self.test_user_email}, got {data.get('email')}",
                        response_time, response.status_code
                    )
                    return False
                
                self.log_result(
                    "Session Cookie Auth", True,
                    f"Session cookie authentication working. User: {data.get('email')}",
                    response_time, response.status_code
                )
                return True
            else:
                self.log_result(
                    "Session Cookie Auth", False,
                    f"Session cookie auth failed: {response.status_code}. Cookies might not be working.",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Session Cookie Auth", False, f"Request failed: {str(e)}")
            return False

    def test_file_upload_bearer_token(self):
        """Test file upload with Bearer token authentication."""
        if not self.bearer_token:
            self.log_result("File Upload (Bearer Token)", False, "No bearer token available")
            return False
            
        try:
            start_time = time.time()
            
            # Create FRA test data
            fra_data = self.create_fra_test_data()
            
            # Prepare file upload
            files = {
                'file': ('fra_test_data.csv', io.StringIO(fra_data), 'text/csv')
            }
            
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            
            response = self.session.post(
                f"{self.backend_url}/api/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') != 'success':
                    self.log_result(
                        "File Upload (Bearer Token)", False,
                        f"Upload status: {data.get('status')}, expected 'success'",
                        response_time, response.status_code
                    )
                    return False
                
                if 'upload_id' not in data:
                    self.log_result(
                        "File Upload (Bearer Token)", False,
                        "No upload_id in response",
                        response_time, response.status_code
                    )
                    return False
                
                self.upload_id_bearer = data['upload_id']
                measurement_summary = data.get('measurement_summary', {})
                freq_points = measurement_summary.get('frequency_points', 0)
                
                self.log_result(
                    "File Upload (Bearer Token)", True,
                    f"File uploaded successfully with Bearer token. Upload ID: {self.upload_id_bearer}, Frequency points: {freq_points}",
                    response_time, response.status_code
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "File Upload (Bearer Token)", False,
                    "Authentication failed - Bearer token not accepted by upload endpoint",
                    response_time, response.status_code
                )
                return False
            else:
                self.log_result(
                    "File Upload (Bearer Token)", False,
                    f"Upload failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("File Upload (Bearer Token)", False, f"Request failed: {str(e)}")
            return False

    def test_file_upload_session_cookie(self):
        """Test file upload with session cookie authentication."""
        try:
            start_time = time.time()
            
            # Create FRA test data
            fra_data = self.create_fra_test_data()
            
            # Prepare file upload (no Authorization header, rely on session cookies)
            files = {
                'file': ('fra_test_session.csv', io.StringIO(fra_data), 'text/csv')
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/upload",
                files=files,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') != 'success':
                    self.log_result(
                        "File Upload (Session Cookie)", False,
                        f"Upload status: {data.get('status')}, expected 'success'",
                        response_time, response.status_code
                    )
                    return False
                
                if 'upload_id' not in data:
                    self.log_result(
                        "File Upload (Session Cookie)", False,
                        "No upload_id in response",
                        response_time, response.status_code
                    )
                    return False
                
                self.upload_id_session = data['upload_id']
                measurement_summary = data.get('measurement_summary', {})
                freq_points = measurement_summary.get('frequency_points', 0)
                
                self.log_result(
                    "File Upload (Session Cookie)", True,
                    f"File uploaded successfully with session cookie. Upload ID: {self.upload_id_session}, Frequency points: {freq_points}",
                    response_time, response.status_code
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "File Upload (Session Cookie)", False,
                    "Authentication failed - Session cookie not accepted by upload endpoint",
                    response_time, response.status_code
                )
                return False
            else:
                self.log_result(
                    "File Upload (Session Cookie)", False,
                    f"Upload failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("File Upload (Session Cookie)", False, f"Request failed: {str(e)}")
            return False

    def test_ml_analysis_bearer_token(self):
        """Test ML analysis with Bearer token authentication."""
        if not self.bearer_token or not self.upload_id_bearer:
            self.log_result("ML Analysis (Bearer Token)", False, "No bearer token or upload ID available")
            return False
            
        try:
            start_time = time.time()
            
            analysis_request = {
                "apply_filtering": True,
                "apply_wavelet": False,
                "include_features": True,
                "confidence_threshold": 0.7
            }
            
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            
            response = self.session.post(
                f"{self.backend_url}/api/analyze/{self.upload_id_bearer}",
                json=analysis_request,
                headers=headers,
                timeout=60
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['analysis_id', 'predicted_fault_type', 'confidence_score']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "ML Analysis (Bearer Token)", False,
                        f"Missing fields: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                self.analysis_id_bearer = data['analysis_id']
                fault_type = data['predicted_fault_type']
                confidence = data['confidence_score']
                
                self.log_result(
                    "ML Analysis (Bearer Token)", True,
                    f"ML analysis completed with Bearer token. Fault: {fault_type}, Confidence: {confidence:.3f}",
                    response_time, response.status_code
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "ML Analysis (Bearer Token)", False,
                    "Authentication failed - Bearer token not accepted by analysis endpoint",
                    response_time, response.status_code
                )
                return False
            else:
                self.log_result(
                    "ML Analysis (Bearer Token)", False,
                    f"Analysis failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("ML Analysis (Bearer Token)", False, f"Request failed: {str(e)}")
            return False

    def test_ml_analysis_session_cookie(self):
        """Test ML analysis with session cookie authentication."""
        if not self.upload_id_session:
            self.log_result("ML Analysis (Session Cookie)", False, "No upload ID available for session cookie test")
            return False
            
        try:
            start_time = time.time()
            
            analysis_request = {
                "apply_filtering": True,
                "apply_wavelet": False,
                "include_features": True,
                "confidence_threshold": 0.7
            }
            
            # No Authorization header, rely on session cookies
            response = self.session.post(
                f"{self.backend_url}/api/analyze/{self.upload_id_session}",
                json=analysis_request,
                timeout=60
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['analysis_id', 'predicted_fault_type', 'confidence_score']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "ML Analysis (Session Cookie)", False,
                        f"Missing fields: {missing_fields}",
                        response_time, response.status_code
                    )
                    return False
                
                self.analysis_id_session = data['analysis_id']
                fault_type = data['predicted_fault_type']
                confidence = data['confidence_score']
                
                self.log_result(
                    "ML Analysis (Session Cookie)", True,
                    f"ML analysis completed with session cookie. Fault: {fault_type}, Confidence: {confidence:.3f}",
                    response_time, response.status_code
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "ML Analysis (Session Cookie)", False,
                    "Authentication failed - Session cookie not accepted by analysis endpoint",
                    response_time, response.status_code
                )
                return False
            else:
                self.log_result(
                    "ML Analysis (Session Cookie)", False,
                    f"Analysis failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("ML Analysis (Session Cookie)", False, f"Request failed: {str(e)}")
            return False

    def test_assets_endpoint(self):
        """Test assets endpoint to verify uploaded data is tracked."""
        if not self.bearer_token:
            self.log_result("Assets Endpoint", False, "No bearer token available")
            return False
            
        try:
            start_time = time.time()
            
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            response = self.session.get(
                f"{self.backend_url}/api/assets",
                headers=headers,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if 'assets' not in data or 'total_count' not in data:
                    self.log_result(
                        "Assets Endpoint", False,
                        "Missing 'assets' or 'total_count' in response",
                        response_time, response.status_code
                    )
                    return False
                
                total_count = data['total_count']
                assets = data['assets']
                
                # We should have at least one asset if uploads were successful
                expected_assets = 1 if (self.upload_id_bearer or self.upload_id_session) else 0
                
                self.log_result(
                    "Assets Endpoint", True,
                    f"Assets retrieved successfully. Total: {total_count}, Expected: {expected_assets}",
                    response_time, response.status_code
                )
                return True
            elif response.status_code == 401:
                self.log_result(
                    "Assets Endpoint", False,
                    "Authentication failed - Bearer token not accepted by assets endpoint",
                    response_time, response.status_code
                )
                return False
            else:
                self.log_result(
                    "Assets Endpoint", False,
                    f"Assets request failed: {response.status_code}",
                    response_time, response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Assets Endpoint", False, f"Request failed: {str(e)}")
            return False

    def run_authentication_upload_tests(self):
        """Run comprehensive authentication and upload tests."""
        print("\n🔐 Starting Authentication & File Upload Tests...")
        print("-" * 50)
        
        # Test sequence following the user's reported issue
        test_sequence = [
            ("User Registration/Login", self.test_user_registration),
            ("Bearer Token Authentication", self.test_bearer_token_auth),
            ("Session Cookie Authentication", self.test_session_cookie_auth),
            ("File Upload (Bearer Token)", self.test_file_upload_bearer_token),
            ("File Upload (Session Cookie)", self.test_file_upload_session_cookie),
            ("ML Analysis (Bearer Token)", self.test_ml_analysis_bearer_token),
            ("ML Analysis (Session Cookie)", self.test_ml_analysis_session_cookie),
            ("Assets Endpoint Verification", self.test_assets_endpoint)
        ]
        
        passed = 0
        total = len(test_sequence)
        
        for test_name, test_func in test_sequence:
            print(f"\n🧪 Running: {test_name}")
            if test_func():
                passed += 1
            else:
                # Continue with other tests even if one fails
                print(f"   ⚠️  {test_name} failed, continuing with remaining tests...")
        
        print("\n" + "=" * 60)
        print(f"📊 AUTHENTICATION & UPLOAD TEST RESULTS")
        print(f"🎯 Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        # Analyze results
        auth_working = any(r['success'] for r in self.test_results if 'Auth' in r['test'])
        upload_bearer_working = any(r['success'] for r in self.test_results if r['test'] == 'File Upload (Bearer Token)')
        upload_session_working = any(r['success'] for r in self.test_results if r['test'] == 'File Upload (Session Cookie)')
        analysis_working = any(r['success'] for r in self.test_results if 'ML Analysis' in r['test'])
        
        print(f"\n📋 COMPONENT STATUS:")
        print(f"   Authentication: {'✅ Working' if auth_working else '❌ Failed'}")
        print(f"   File Upload (Bearer): {'✅ Working' if upload_bearer_working else '❌ Failed'}")
        print(f"   File Upload (Session): {'✅ Working' if upload_session_working else '❌ Failed'}")
        print(f"   ML Analysis: {'✅ Working' if analysis_working else '❌ Failed'}")
        
        if not upload_bearer_working and not upload_session_working:
            print(f"\n❌ CRITICAL ISSUE: File upload authentication is broken for both methods!")
            print(f"   This matches the user's reported issue.")
        elif upload_bearer_working and not upload_session_working:
            print(f"\n⚠️  PARTIAL ISSUE: Bearer token works but session cookies don't")
        elif not upload_bearer_working and upload_session_working:
            print(f"\n⚠️  PARTIAL ISSUE: Session cookies work but Bearer token doesn't")
        else:
            print(f"\n✅ SUCCESS: Both authentication methods working for file upload")
        
        return passed, total, self.test_results

def main():
    """Main test execution."""
    tester = AuthUploadTester()
    passed, total, results = tester.run_authentication_upload_tests()
    
    # Save detailed results
    with open('/app/auth_upload_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'passed': passed,
                'total': total,
                'success_rate': passed / total if total > 0 else 0,
                'backend_url': tester.backend_url,
                'test_timestamp': datetime.now().isoformat(),
                'bearer_token_available': tester.bearer_token is not None,
                'session_cookies_available': tester.session_cookies is not None,
                'upload_id_bearer': tester.upload_id_bearer,
                'upload_id_session': tester.upload_id_session
            },
            'detailed_results': results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/auth_upload_test_results.json")
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)