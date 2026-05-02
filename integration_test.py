#!/usr/bin/env python3
"""
Integration test for SAS 2.0 Phase 3
Tests: Offline attendance, faculty semester management, semester filtering
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
TIMESTAMP = int(time.time())

class TestRunner:
    def __init__(self):
        self.student_token = None
        self.student_id = None
        self.faculty_token = None
        self.faculty_id = None
        self.lecture_id = None
        self.session_id = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def log(self, message, level="INFO"):
        """Log message with formatting"""
        prefix = f"[{level}]"
        print(f"{prefix} {message}")

    def assert_equal(self, actual, expected, test_name):
        """Assert equality and log result"""
        if actual == expected:
            self.log(f"PASS: {test_name}: PASSED", "PASS")
            self.tests_passed += 1
            self.test_results.append((test_name, "PASSED"))
        else:
            self.log(f"FAIL: {test_name}: FAILED - Expected {expected}, got {actual}", "FAIL")
            self.tests_failed += 1
            self.test_results.append((test_name, "FAILED"))

    def assert_status(self, response, expected_status, test_name):
        """Assert response status code"""
        if response.status_code == expected_status:
            self.log(f"PASS: {test_name}: Status {response.status_code}", "PASS")
            self.tests_passed += 1
            self.test_results.append((test_name, "PASSED"))
        else:
            self.log(f"FAIL: {test_name}: Expected {expected_status}, got {response.status_code}", "FAIL")
            self.log(f"   Response: {response.text[:200]}", "ERROR")
            self.tests_failed += 1
            self.test_results.append((test_name, "FAILED"))

    def test_student_signup(self):
        """Test student signup with semester and department"""
        self.log("\n=== Testing Student Signup ===", "TEST")
        
        payload = {
            "name": "John Doe",
            "email": f"john{TIMESTAMP}@example.com",
            "password": "password123",
            "role": "student",
            "roll_number": f"CSE2024{TIMESTAMP}",
            "department": "Computer Science",
            "semester": "3"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        self.assert_status(response, 200, "Student Registration")
        
        if response.status_code == 200:
            data = response.json()
            self.student_token = data.get("token")
            self.student_id = data.get("user_id")
            self.log(f"   Student ID: {self.student_id}", "INFO")

    def test_faculty_signup(self):
        """Test faculty signup with subject and semesters"""
        self.log("\n=== Testing Faculty Signup ===", "TEST")
        
        payload = {
            "name": "Prof. Smith",
            "email": f"smith{TIMESTAMP}@example.com",
            "password": "password123",
            "role": "faculty",
            "faculty_id": f"FAC{TIMESTAMP}",
            "subject": "Data Structures",
            "semesters": ["2", "4", "6"]
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        self.assert_status(response, 200, "Faculty Registration")
        
        if response.status_code == 200:
            data = response.json()
            self.faculty_token = data.get("token")
            self.faculty_id = data.get("user_id")
            self.log(f"   Faculty ID: {self.faculty_id}", "INFO")

    def test_faculty_profile(self):
        """Test faculty profile retrieval with semesters"""
        self.log("\n=== Testing Faculty Profile ===", "TEST")
        
        headers = {"Authorization": f"Bearer {self.faculty_token}"}
        response = requests.get(f"{BASE_URL}/api/faculty/profile", headers=headers)
        self.assert_status(response, 200, "Get Faculty Profile")
        
        if response.status_code == 200:
            data = response.json().get("profile", {})
            self.log(f"   Faculty: {data.get('name')}", "INFO")
            self.log(f"   Subject: {data.get('subject')}", "INFO")
            self.log(f"   Teaching Semesters: {data.get('semesters')}", "INFO")
            self.assert_equal(data.get("subject"), "Data Structures", "Faculty Subject")

    def test_lecture_creation(self):
        """Test lecture creation with semester validation"""
        self.log("\n=== Testing Lecture Creation ===", "TEST")
        
        now = datetime.now()
        start_time = now + timedelta(hours=1)
        end_time = now + timedelta(hours=2)
        
        payload = {
            "lecture_title": "Introduction to DSA",
            "subject": "Data Structures",
            "date": now.strftime("%Y-%m-%d"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "semester": "4"  # Faculty teaches semester 4
        }
        
        headers = {"Authorization": f"Bearer {self.faculty_token}"}
        response = requests.post(f"{BASE_URL}/api/lectures/sessions", json=payload, headers=headers)
        self.assert_status(response, 200, "Create Lecture (Valid Semester)")
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
            self.log(f"   Session ID: {self.session_id}", "INFO")

    def test_lecture_creation_invalid_semester(self):
        """Test lecture creation with invalid semester (should fail)"""
        self.log("\n=== Testing Lecture Validation ===", "TEST")
        
        now = datetime.now()
        start_time = now + timedelta(hours=3)
        end_time = now + timedelta(hours=4)
        
        payload = {
            "lecture_title": "Advanced DSA",
            "subject": "Data Structures",
            "date": now.strftime("%Y-%m-%d"),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "semester": "5"  # Faculty does NOT teach semester 5
        }
        
        headers = {"Authorization": f"Bearer {self.faculty_token}"}
        response = requests.post(f"{BASE_URL}/api/lectures/sessions", json=payload, headers=headers)
        self.assert_status(response, 403, "Create Lecture (Invalid Semester)")
        
        if response.status_code == 403:
            data = response.json()
            self.log(f"   Error: {data.get('error')}", "INFO")

    def test_offline_attendance_marking(self):
        """Test marking attendance for offline lecture"""
        self.log("\n=== Testing Offline Attendance ===", "TEST")
        
        if not self.session_id:
            self.log("Skipping - No session ID from lecture creation", "WARN")
            return
        
        payload = {"session_id": self.session_id}
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        response = requests.post(f"{BASE_URL}/api/attendance/mark", json=payload, headers=headers)
        self.assert_status(response, 200, "Mark Attendance (First Time)")
        
        # Try to mark again - should return 409 (already marked)
        response = requests.post(f"{BASE_URL}/api/attendance/mark", json=payload, headers=headers)
        self.assert_status(response, 409, "Mark Attendance (Already Marked)")

    def test_student_profile_semester(self):
        """Test student profile with semester field"""
        self.log("\n=== Testing Student Profile ===", "TEST")
        
        headers = {"Authorization": f"Bearer {self.student_token}"}
        response = requests.get(f"{BASE_URL}/api/student/profile", headers=headers)
        self.assert_status(response, 200, "Get Student Profile")
        
        if response.status_code == 200:
            data = response.json().get("profile", {})
            self.log(f"   Student: {data.get('name')}", "INFO")
            self.log(f"   Department: {data.get('department')}", "INFO")
            self.log(f"   Semester: {data.get('semester')}", "INFO")
            self.assert_equal(data.get("department"), "Computer Science", "Student Department")
            self.assert_equal(data.get("semester"), "3", "Student Semester")

    def run_all_tests(self):
        """Run all integration tests"""
        self.log("=" * 60, "START")
        self.log("SAS 2.0 Phase 3 Integration Tests", "START")
        self.log("=" * 60, "START")
        
        self.test_student_signup()
        self.test_faculty_signup()
        self.test_faculty_profile()
        self.test_lecture_creation()
        self.test_lecture_creation_invalid_semester()
        self.test_offline_attendance_marking()
        self.test_student_profile_semester()
        
        # Print summary
        self.log("\n" + "=" * 60, "SUMMARY")
        self.log(f"Tests Passed: {self.tests_passed}", "SUMMARY")
        self.log(f"Tests Failed: {self.tests_failed}", "SUMMARY")
        self.log("=" * 60, "SUMMARY")
        
        # Print detailed results
        self.log("\nDetailed Results:", "DETAIL")
        for test_name, result in self.test_results:
            status_icon = "PASS" if result == "PASSED" else "FAIL"
            self.log(f"  [{status_icon}] {test_name}: {result}", "DETAIL")

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
