#!/usr/bin/env python3
"""
API Endpoint Testing Script for Nature Quest Mock Server
Tests all available endpoints and reports results.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5002/api/v1"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

class APITester:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log(self, message, status="INFO"):
        """Log test results with color coding."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "PASS":
            print(f"{GREEN}[{timestamp}] ✓ {message}{RESET}")
            self.passed += 1
        elif status == "FAIL":
            print(f"{RED}[{timestamp}] ✗ {message}{RESET}")
            self.failed += 1
        elif status == "WARN":
            print(f"{YELLOW}[{timestamp}] ⚠ {message}{RESET}")
        else:
            print(f"[{timestamp}] {message}")

    def make_request(self, method, endpoint, data=None, headers=None, expected_status=None):
        """Make HTTP request and return response."""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return None
            
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "FAIL")
            return None

    def test_health_endpoint(self):
        """Test health check endpoint."""
        print("\n" + "="*60)
        print("TESTING: Health Check Endpoint")
        print("="*60)
        
        response = self.make_request("GET", "/health/")
        if response and response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"].get("status") == "ok":
                self.log("Health check endpoint working correctly", "PASS")
            else:
                self.log("Health check response format incorrect", "FAIL")
        else:
            self.log(f"Health check failed: {response.status_code if response else 'No response'}", "FAIL")

    def test_authentication_endpoints(self):
        """Test authentication endpoints."""
        print("\n" + "="*60)
        print("TESTING: Authentication Endpoints")
        print("="*60)
        
        # Test registration
        register_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = self.make_request("POST", "/users/auth/register/", register_data)
        if response and response.status_code == 201:
            data = response.json()
            if data.get("success") and "data" in data:
                self.access_token = data["data"].get("access")
                self.refresh_token = data["data"].get("refresh")
                self.log("User registration successful", "PASS")
            else:
                self.log("Registration response format incorrect", "FAIL")
        else:
            self.log(f"Registration failed: {response.status_code if response else 'No response'}", "FAIL")
            return

        # Test login
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        response = self.make_request("POST", "/users/auth/login/", login_data)
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                self.access_token = data["data"].get("access")
                self.refresh_token = data["data"].get("refresh")
                self.log("User login successful", "PASS")
            else:
                self.log("Login response format incorrect", "FAIL")
        else:
            self.log(f"Login failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test token refresh
        if self.refresh_token:
            refresh_data = {"refresh": self.refresh_token}
            response = self.make_request("POST", "/users/auth/token/refresh/", refresh_data)
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    self.log("Token refresh successful", "PASS")
                else:
                    self.log("Token refresh response format incorrect", "FAIL")
            else:
                self.log(f"Token refresh failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test invalid login
        invalid_login = {"email": "test@example.com", "password": "wrongpassword"}
        response = self.make_request("POST", "/users/auth/login/", invalid_login)
        if response and response.status_code == 401:
            self.log("Invalid login correctly rejected", "PASS")
        else:
            self.log("Invalid login should return 401", "WARN")

    def test_quest_endpoints(self):
        """Test quest endpoints."""
        print("\n" + "="*60)
        print("TESTING: Quest Endpoints")
        print("="*60)
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        # Test list quests
        response = self.make_request("GET", "/quests/", headers=headers)
        if response and response.status_code == 200:
            self.log("List quests endpoint working", "PASS")
        else:
            self.log(f"List quests failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test create quest
        quest_data = {
            "title": "Test Quest",
            "description": "A test quest",
            "quest_type": "outdoor",
            "difficulty": 1,
            "duration_minutes": 30,
            "experience_reward": 50
        }
        response = self.make_request("POST", "/quests/", quest_data, headers)
        if response and response.status_code == 201:
            self.log("Create quest endpoint working", "PASS")
        else:
            self.log(f"Create quest failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test get quest
        response = self.make_request("GET", "/quests/1/", headers=headers)
        if response and response.status_code == 200:
            self.log("Get quest endpoint working", "PASS")
        else:
            self.log(f"Get quest failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test find nearby
        response = self.make_request("GET", "/quests/find-nearby/?latitude=40.7&longitude=-74.0&radius=10", headers=headers)
        if response and response.status_code == 200:
            self.log("Find nearby quests endpoint working", "PASS")
        else:
            self.log(f"Find nearby failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test discover
        response = self.make_request("GET", "/quests/discover/?latitude=40.7&longitude=-74.0", headers=headers)
        if response and response.status_code == 200:
            self.log("Discover quests endpoint working", "PASS")
        else:
            self.log(f"Discover failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test start quest
        response = self.make_request("POST", "/quests/1/start/", headers=headers)
        if response and response.status_code in [200, 201]:
            self.log("Start quest endpoint working", "PASS")
        else:
            self.log(f"Start quest failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test complete quest
        response = self.make_request("POST", "/quests/1/complete/", headers=headers)
        if response and response.status_code == 200:
            self.log("Complete quest endpoint working", "PASS")
        else:
            self.log(f"Complete quest failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test abandon quest
        response = self.make_request("POST", "/quests/1/abandon/", headers=headers)
        if response and response.status_code == 200:
            self.log("Abandon quest endpoint working", "PASS")
        else:
            self.log(f"Abandon quest failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test validate location
        location_data = {"latitude": 40.785091, "longitude": -73.968285}
        response = self.make_request("POST", "/quests/1/validate-location/", location_data, headers)
        if response and response.status_code == 200:
            self.log("Validate location endpoint working", "PASS")
        else:
            self.log(f"Validate location failed: {response.status_code if response else 'No response'}", "FAIL")

    def test_challenge_endpoints(self):
        """Test challenge endpoints."""
        print("\n" + "="*60)
        print("TESTING: Challenge Endpoints")
        print("="*60)
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        # Test list challenges
        response = self.make_request("GET", "/challenges/", headers=headers)
        if response and response.status_code == 200:
            self.log("List challenges endpoint working", "PASS")
        else:
            self.log(f"List challenges failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test create challenge
        challenge_data = {
            "title": "Test Challenge",
            "description": "A test challenge",
            "is_mandatory": False,
            "experience_reward": 100
        }
        response = self.make_request("POST", "/challenges/", challenge_data, headers)
        if response and response.status_code == 201:
            self.log("Create challenge endpoint working", "PASS")
        else:
            self.log(f"Create challenge failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test get challenge
        response = self.make_request("GET", "/challenges/1/", headers=headers)
        if response and response.status_code == 200:
            self.log("Get challenge endpoint working", "PASS")
        else:
            self.log(f"Get challenge failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test start challenge
        response = self.make_request("POST", "/challenges/1/start/", headers=headers)
        if response and response.status_code in [200, 201]:
            self.log("Start challenge endpoint working", "PASS")
        else:
            self.log(f"Start challenge failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test complete challenge
        response = self.make_request("POST", "/challenges/1/complete/", headers=headers)
        if response and response.status_code == 200:
            self.log("Complete challenge endpoint working", "PASS")
        else:
            self.log(f"Complete challenge failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test abandon challenge
        response = self.make_request("POST", "/challenges/1/abandon/", headers=headers)
        if response and response.status_code == 200:
            self.log("Abandon challenge endpoint working", "PASS")
        else:
            self.log(f"Abandon challenge failed: {response.status_code if response else 'No response'}", "FAIL")

    def test_gamification_endpoints(self):
        """Test gamification endpoints."""
        print("\n" + "="*60)
        print("TESTING: Gamification Endpoints")
        print("="*60)
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        
        # Test profile
        response = self.make_request("GET", "/gamification/profile/", headers=headers)
        if response and response.status_code == 200:
            self.log("Gamification profile endpoint working", "PASS")
        else:
            self.log(f"Profile failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test badges
        response = self.make_request("GET", "/gamification/badges/", headers=headers)
        if response and response.status_code == 200:
            self.log("Badges endpoint working", "PASS")
        else:
            self.log(f"Badges failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test leaderboards
        response = self.make_request("GET", "/gamification/leaderboards/", headers=headers)
        if response and response.status_code == 200:
            self.log("Leaderboards endpoint working", "PASS")
        else:
            self.log(f"Leaderboards failed: {response.status_code if response else 'No response'}", "FAIL")

        # Test environmental impact
        response = self.make_request("GET", "/gamification/environmental-impact/", headers=headers)
        if response and response.status_code == 200:
            self.log("Environmental impact endpoint working", "PASS")
        else:
            self.log(f"Environmental impact failed: {response.status_code if response else 'No response'}", "FAIL")

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints."""
        print("\n" + "="*60)
        print("TESTING: Unauthorized Access")
        print("="*60)
        
        # Test accessing protected endpoint without token
        response = self.make_request("GET", "/quests/")
        if response and response.status_code == 401:
            self.log("Unauthorized access correctly rejected", "PASS")
        else:
            self.log("Protected endpoints should require authentication", "WARN")

    def run_all_tests(self):
        """Run all API tests."""
        print("\n" + "="*60)
        print("NATURE QUEST API ENDPOINT TESTING")
        print("="*60)
        print(f"Base URL: {BASE_URL}")
        print("="*60)

        try:
            self.test_health_endpoint()
            self.test_authentication_endpoints()
            self.test_quest_endpoints()
            self.test_challenge_endpoints()
            self.test_gamification_endpoints()
            self.test_unauthorized_access()
        except Exception as e:
            self.log(f"Test execution error: {e}", "FAIL")

        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = self.passed + self.failed
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        if total > 0:
            print(f"Success Rate: {(self.passed/total)*100:.1f}%")
        print("="*60)

        return self.failed == 0

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
