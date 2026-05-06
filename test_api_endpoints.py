import requests
import json

BASE_URL = "http://localhost:5000"

def test_api_endpoints():
    print("🧪 Testing SAS API Endpoints with Test Data")
    print("=" * 50)

    # Test 1: Health check
    print("\n1. Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Student Login (using first student)
    print("\n2. Student Login")
    try:
        login_data = {
            "email": "shaileh@gmail.com",
            "password": "12345678"
        }
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            student_token = resp.json().get("token")
            print(f"   Token received: {student_token[:50]}...")
        else:
            print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        student_token = None

    # Test 3: Faculty Login (using specific faculty)
    print("\n3. Faculty Login")
    faculty_token = None
    try:
        login_data = {
            "email": "chintanadmin@gmail.com",  # Chintan C Gajjar
            "password": "12345678"
        }
        resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            faculty_token = resp.json().get("token")
            print(f"   Token received: {faculty_token[:50]}...")
        else:
            print(f"   Response: {resp.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 4: Get Student Profile
    if student_token:
        print("\n4. Student Profile")
        try:
            headers = {"Authorization": f"Bearer {student_token}"}
            resp = requests.get(f"{BASE_URL}/api/student/profile", headers=headers)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                profile = resp.json()
                print(f"   Name: {profile.get('name')}")
                print(f"   Role: {profile.get('role')}")
                print(f"   Semester: {profile.get('semester')}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test 5: Get Faculty Profile
    if faculty_token:
        print("\n5. Faculty Profile")
        try:
            headers = {"Authorization": f"Bearer {faculty_token}"}
            resp = requests.get(f"{BASE_URL}/api/faculty/profile", headers=headers)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                profile = resp.json()
                print(f"   Name: {profile.get('name')}")
                print(f"   Role: {profile.get('role')}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test 6: Get Lectures (Faculty)
    if faculty_token:
        print("\n6. Faculty Lectures")
        try:
            headers = {"Authorization": f"Bearer {faculty_token}"}
            resp = requests.get(f"{BASE_URL}/api/lectures/sessions", headers=headers)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                lectures = resp.json()
                print(f"   Total lectures: {len(lectures)}")
                if lectures:
                    print(f"   Sample lecture: {lectures[0].get('title')}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test 7: Get Student Lectures
    if student_token:
        print("\n7. Student Lectures")
        try:
            headers = {"Authorization": f"Bearer {student_token}"}
            resp = requests.get(f"{BASE_URL}/api/lectures/sessions", headers=headers)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                lectures = resp.json()
                print(f"   Total lectures: {len(lectures)}")
                if lectures:
                    print(f"   Sample lecture: {lectures[0].get('title')}")
        except Exception as e:
            print(f"   Error: {e}")

    # Test 8: Get Attendance Records (Student)
    if student_token:
        print("\n8. Student Attendance History")
        try:
            headers = {"Authorization": f"Bearer {student_token}"}
            resp = requests.get(f"{BASE_URL}/api/attendance/history", headers=headers)
            print(f"   Status: {resp.status_code}")
            if resp.status_code == 200:
                attendance = resp.json()
                print(f"   Total attendance records: {len(attendance)}")
                if attendance:
                    print(f"   Sample status: {attendance[0].get('status')}")
        except Exception as e:
            print(f"   Error: {e}")

    print("\n" + "=" * 50)
    print("✅ API Testing Complete!")
    print("\n📊 Test Data Summary:")
    print("   • 79 Students across 6 semesters")
    print("   • 28 Faculty members")
    print("   • 336 Lectures (12 per subject)")
    print("   • 3,475 Attendance records")
    print("\n🌐 Servers Running:")
    print("   • Backend: http://localhost:5000")
    print("   • Frontend: http://localhost:5175")

if __name__ == "__main__":
    test_api_endpoints()