import os
import sys
import json
import hashlib
import hmac
import secrets
import random
from datetime import datetime, timedelta

# Ensure project root is in path
BASE_DIR = os.getcwd()
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Add the backend directory to path
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from database import get_db

PBKDF2_ITERATIONS = 200_000
PBKDF2_ALGORITHM = "sha256"

def hash_password(password):
    """Hash password using PBKDF2 (same as backend)"""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"

# Specific faculty data as provided by user
SPECIFIC_FACULTY = [
    {
        "name": "Chintan C Gajjar",
        "faculty_id": "CAG",
        "email": "chintanadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Python Programming"},
            {"semester": "2", "subject": "Advanced Python Programming"},
            {"semester": "3", "subject": "Linux Operating System"},
            {"semester": "4", "subject": "Object Oriented Programming with Java"},
            {"semester": "5", "subject": "Advanced Java Programming"},
            {"semester": "6", "subject": "Software Development"}
        ]
    },
    {
        "name": "Dhaval R Ghandhi",
        "faculty_id": "DRG",
        "email": "dhavaladmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Static Webpage Design"},
            {"semester": "2", "subject": "Environment and Sustainability"},
            {"semester": "3", "subject": "Data Structure with Python"},
            {"semester": "4", "subject": "Fundamentals of Machine Learning"},
            {"semester": "5", "subject": "Foundation of AI and ML"},
            {"semester": "6", "subject": "Cloud and Data Center Technologies"}
        ]
    },
    {
        "name": "Dharmesh N Dhangar",
        "faculty_id": "DND",
        "email": "dharmeshadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Introduction to IT Systems"},
            {"semester": "2", "subject": "Information Security Awareness"},
            {"semester": "3", "subject": "Fundamentals of Software Development"},
            {"semester": "4", "subject": "Essentials of Digital Marketing"},
            {"semester": "5", "subject": "Mobile Computing and Networks"},
            {"semester": "6", "subject": "Cyber Security and Digital Forensics"}
        ]
    },
    {
        "name": "Umang D Shukla",
        "faculty_id": "UDS",
        "email": "umangadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Static Webpage Design"},
            {"semester": "2", "subject": "Basic Electronics"},
            {"semester": "3", "subject": "Linux Operating System"},
            {"semester": "4", "subject": "Essentials of Digital Marketing"},
            {"semester": "5", "subject": "Mobile Application Development"},
            {"semester": "6", "subject": "Foundation of Block Chain"}
        ]
    },
    {
        "name": "Manish D Patel",
        "faculty_id": "MDP",
        "email": "manishadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "5", "subject": "Mobile Computing and Networks"}
        ]
    },
    {
        "name": "Jaymin A Patel",
        "faculty_id": "JAP",
        "email": "jayminadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Mathematics"}
        ]
    },
    {
        "name": "Ashmabanu H Rajavada",
        "faculty_id": "AHR",
        "email": "ashmabanuadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Mathematics"},
            {"semester": "2", "subject": "Engineering Mathematics"}
        ]
    },
    {
        "name": "Divyesh K Antala",
        "faculty_id": "DKV",
        "email": "divyeshadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Mathematics"}
        ]
    },
    {
        "name": "Nirmal M Chaudhari",
        "faculty_id": "NMC",
        "email": "nirmaladmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Communication Skills in English"}
        ]
    },
    {
        "name": "Jay N Mehta",
        "faculty_id": "JNM",
        "email": "jayadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "1", "subject": "Communication Skills in English"},
            {"semester": "2", "subject": "Indian Constitution"}
        ]
    },
    {
        "name": "Bhavik L Prajapati",
        "faculty_id": "BLP",
        "email": "bhavikadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "2", "subject": "Physics"}
        ]
    },
    {
        "name": "Purvi H Patel",
        "faculty_id": "PHP",
        "email": "purviadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "2", "subject": "Physics"}
        ]
    },
    {
        "name": "Tejal C Patel",
        "faculty_id": "TCP",
        "email": "tejaladmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "2", "subject": "Environment and Sustainability"}
        ]
    },
    {
        "name": "J M Vala",
        "faculty_id": "JMV",
        "email": "jmvadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "2", "subject": "Environment and Sustainability"}
        ]
    },
    {
        "name": "N P Jariwala",
        "faculty_id": "NPJ",
        "email": "npjadmin@gmail.com",
        "password": "12345678",
        "department": "Information Technology",
        "subjects": [
            {"semester": "2", "subject": "Physics"}
        ]
    }
]

# Student data (keeping the same)
STUDENT_DATA = {
    "1": [
        {"name": "Shaileh Agrawal", "enrollment": "266120316001", "email": "shaileh@gmail.com", "password": "12345678"},
        {"name": "Gaurav Aniyaliya", "enrollment": "266120316002", "email": "gaurav@gmail.com", "password": "12345678"},
        {"name": "Dravy Bhadani", "enrollment": "266120316004", "email": "dravy@gmail.com", "password": "12345678"},
        {"name": "Aaryan Bhandari", "enrollment": "266120316005", "email": "aaryan@gmail.com", "password": "12345678"},
        {"name": "Harsh Bharambe", "enrollment": "266120316006", "email": "harsh@gmail.com", "password": "12345678"},
        {"name": "Hitesh Bhole", "enrollment": "266120316007", "email": "hitesh@gmail.com", "password": "12345678"},
        {"name": "Hetr Chaudhari", "enrollment": "266120316009", "email": "het@gmail.com", "password": "12345678"},
        {"name": "Yash Chauhan", "enrollment": "266120316012", "email": "yashc@gmail.com", "password": "12345678"},
        {"name": "Tej Chote", "enrollment": "266120316013", "email": "tej@gmail.com", "password": "12345678"},
        {"name": "Preet Gabani", "enrollment": "266120316014", "email": "preet@gmail.com", "password": "12345678"},
        {"name": "Drashti Gadhiya", "enrollment": "266120316016", "email": "drashti@gmail.com", "password": "12345678"},
        {"name": "Jeel Gorasiya", "enrollment": "266120316018", "email": "jeel@gmail.com", "password": "12345678"},
        {"name": "Vishnu Jariwala", "enrollment": "266120316019", "email": "vishnu@gmail.com", "password": "12345678"}
    ],
    "2": [
        {"name": "Milan Jethva", "enrollment": "256120316020", "email": "milan@gmail.com", "password": "12345678"},
        {"name": "Sumit Jogi", "enrollment": "256120316021", "email": "sumit@gmail.com", "password": "12345678"},
        {"name": "Muskan Khalasi", "enrollment": "256120316024", "email": "muskan@gmail.com", "password": "12345678"},
        {"name": "Shreya Khalasi", "enrollment": "256120316025", "email": "shreya@gmail.com", "password": "12345678"},
        {"name": "Vipshi Khalasi", "enrollment": "256120316026", "email": "vipshi@gmail.com", "password": "12345678"},
        {"name": "Yash Khatri", "enrollment": "256120316027", "email": "yashk@gmail.com", "password": "12345678"},
        {"name": "Mahendra Ladva", "enrollment": "256120316029", "email": "mahendra@gmail.com", "password": "12345678"},
        {"name": "Himanshu Lahorkar", "enrollment": "256120316030", "email": "himanshu@gmail.com", "password": "12345678"},
        {"name": "Dhvani Lakkad", "enrollment": "256120316031", "email": "dhvani@gmail.com", "password": "12345678"},
        {"name": "Parth Lathiya", "enrollment": "256120316032", "email": "parth@gmail.com", "password": "12345678"},
        {"name": "Jainam Limbachiya", "enrollment": "256120316033", "email": "jainam@gmail.com", "password": "12345678"},
        {"name": "Vishal Madhad", "enrollment": "256120316034", "email": "vishal@gmail.com", "password": "12345678"},
        {"name": "Aakash Modi", "enrollment": "256120316036", "email": "aakash@gmail.com", "password": "12345678"}
    ],
    "3": [
        {"name": "Hetvi Navadiya", "enrollment": "246120316037", "email": "hetvi@gmail.com", "password": "12345678"},
        {"name": "Yash Paghadar", "enrollment": "246120316038", "email": "yashp@gmail.com", "password": "12345678"},
        {"name": "Sneha Pandey", "enrollment": "246120316040", "email": "sneha@gmail.com", "password": "12345678"},
        {"name": "Bhakti Patel", "enrollment": "246120316041", "email": "bhakti@gmail.com", "password": "12345678"},
        {"name": "Devanshi Patel", "enrollment": "246120316042", "email": "devanshi@gmail.com", "password": "12345678"},
        {"name": "Dhruvi Patel", "enrollment": "246120316043", "email": "dhruvi@gmail.com", "password": "12345678"},
        {"name": "Heer Patel", "enrollment": "246120316044", "email": "heerp@gmail.com", "password": "12345678"},
        {"name": "Het Patel", "enrollment": "246120316045", "email": "hetp@gmail.com", "password": "12345678"},
        {"name": "Jiya Patel", "enrollment": "246120316047", "email": "jiya@gmail.com", "password": "12345678"},
        {"name": "Manav Patel", "enrollment": "246120316049", "email": "manav@gmail.com", "password": "12345678"},
        {"name": "Riyak Patel", "enrollment": "246120316052", "email": "riyak@gmail.com", "password": "12345678"},
        {"name": "Tinisha Patel", "enrollment": "246120316053", "email": "tinisha@gmail.com", "password": "12345678"},
        {"name": "Vaishnavi Patel", "enrollment": "246120316054", "email": "vaishnavi@gmail.com", "password": "12345678"}
    ],
    "4": [
        {"name": "Ved Patel", "enrollment": "226120316055", "email": "ved@gmail.com", "password": "12345678"},
        {"name": "Vidhi Patel", "enrollment": "226120316056", "email": "vidhi@gmail.com", "password": "12345678"},
        {"name": "Umesh Patil", "enrollment": "226120316057", "email": "umesh@gmail.com", "password": "12345678"},
        {"name": "Pritesh Pawar", "enrollment": "226120316058", "email": "pritesh@gmail.com", "password": "12345678"},
        {"name": "Bhargav Prajapati", "enrollment": "226120316059", "email": "bhargav@gmail.com", "password": "12345678"},
        {"name": "Priyanshi Singhal", "enrollment": "226120316060", "email": "priyanshi@gmail.com", "password": "12345678"},
        {"name": "Ayush Radadiya", "enrollment": "226120316061", "email": "ayush@gmail.com", "password": "12345678"},
        {"name": "Fenil Rathod", "enrollment": "226120316062", "email": "fenil@gmail.com", "password": "12345678"},
        {"name": "Tvisha Rathod", "enrollment": "226120316063", "email": "tvisha@gmail.com", "password": "12345678"},
        {"name": "Yug Rathod", "enrollment": "226120316064", "email": "yug@gmail.com", "password": "12345678"},
        {"name": "Krish Sapariya", "enrollment": "226120316067", "email": "krish@gmail.com", "password": "12345678"},
        {"name": "Dhruva Savaliya", "enrollment": "226120316068", "email": "dhruva@gmail.com", "password": "12345678"},
        {"name": "Uvais Shaikh", "enrollment": "226120316069", "email": "uvais@gmail.com", "password": "12345678"}
    ],
    "5": [
        {"name": "Tanvi Shinde", "enrollment": "216120316070", "email": "tanvi@gmail.com", "password": "12345678"},
        {"name": "Ujjaval Solanki", "enrollment": "216120316071", "email": "ujjaval@gmail.com", "password": "12345678"},
        {"name": "Jeet Surati", "enrollment": "216120316072", "email": "jeet@gmail.com", "password": "12345678"},
        {"name": "Meshwa Suthar", "enrollment": "216120316073", "email": "meshwa@gmail.com", "password": "12345678"},
        {"name": "Divyesh Thube", "enrollment": "216120316074", "email": "divyesh@gmail.com", "password": "12345678"},
        {"name": "Kishan Thummar", "enrollment": "216120316075", "email": "kishan@gmail.com", "password": "12345678"},
        {"name": "Yuvrajsingh Rajput", "enrollment": "216120316079", "email": "yuvrajsingh@gmail.com", "password": "12345678"},
        {"name": "Ankita Solanki", "enrollment": "216120316080", "email": "ankita@gmail.com", "password": "12345678"},
        {"name": "Vijesh Jariwala", "enrollment": "216120316081", "email": "vijesh@gmail.com", "password": "12345678"},
        {"name": "Chetan Borse", "enrollment": "216120316082", "email": "chetan@gmail.com", "password": "12345678"},
        {"name": "Gautam Papaliya", "enrollment": "216120316083", "email": "gautam@gmail.com", "password": "12345678"},
        {"name": "Saurabh Gurav", "enrollment": "216120316084", "email": "saurabh@gmail.com", "password": "12345678"},
        {"name": "Fardin Pathan", "enrollment": "216120316085", "email": "fardin@gmail.com", "password": "12345678"}
    ],
    "6": [
        {"name": "Rahul Sharma", "enrollment": "206120316086", "email": "rahul@gmail.com", "password": "12345678"},
        {"name": "Priya Singh", "enrollment": "206120316087", "email": "priya@gmail.com", "password": "12345678"},
        {"name": "Amit Kumar", "enrollment": "206120316088", "email": "amit@gmail.com", "password": "12345678"},
        {"name": "Sneha Gupta", "enrollment": "206120316089", "email": "sneha.g@gmail.com", "password": "12345678"},
        {"name": "Rohit Verma", "enrollment": "206120316090", "email": "rohit@gmail.com", "password": "12345678"},
        {"name": "Kavita Jain", "enrollment": "206120316091", "email": "kavita@gmail.com", "password": "12345678"},
        {"name": "Vikash Tiwari", "enrollment": "206120316092", "email": "vikash@gmail.com", "password": "12345678"},
        {"name": "Meera Choudhary", "enrollment": "206120316093", "email": "meera@gmail.com", "password": "12345678"},
        {"name": "Sandeep Yadav", "enrollment": "206120316094", "email": "sandeep@gmail.com", "password": "12345678"},
        {"name": "Anjali Mishra", "enrollment": "206120316095", "email": "anjali@gmail.com", "password": "12345678"},
        {"name": "Rajesh Gupta", "enrollment": "206120316096", "email": "rajesh@gmail.com", "password": "12345678"},
        {"name": "Poonam Sharma", "enrollment": "206120316097", "email": "poonam@gmail.com", "password": "12345678"},
        {"name": "Manoj Singh", "enrollment": "206120316098", "email": "manoj@gmail.com", "password": "12345678"},
        {"name": "Kiran Patel", "enrollment": "206120316099", "email": "kiran@gmail.com", "password": "12345678"}
    ]
}

def generate_lectures(faculty_data):
    lectures = []
    lecture_id = 1

    # Generate 10-15 lectures per subject
    for faculty in faculty_data:
        for subject_assignment in faculty["subjects"]:
            semester = subject_assignment["semester"]
            subject = subject_assignment["subject"]
            faculty_id = faculty["faculty_id"]

            # Generate 12 lectures per subject (mix of past and future)
            num_lectures = 12

            for i in range(num_lectures):
                # Mix of past and recent dates
                if i < 6:  # Past lectures
                    base_date = datetime.now() - timedelta(days=random.randint(1, 30))
                else:  # Recent/future lectures
                    base_date = datetime.now() + timedelta(days=random.randint(0, 14))

                lecture_date = base_date.strftime("%d-%m-%Y")

                # Random time slots (morning/afternoon)
                if random.choice([True, False]):
                    # Morning slot: 9:00-11:00
                    start_hour = random.randint(9, 10)
                    start_time = f"{start_hour:02d}:{random.choice(['00', '30'])}:00"
                    end_time = f"{start_hour+1:02d}:{random.choice(['00', '30'])}:00"
                else:
                    # Afternoon slot: 14:00-16:00
                    start_hour = random.randint(14, 15)
                    start_time = f"{start_hour:02d}:{random.choice(['00', '30'])}:00"
                    end_time = f"{start_hour+1:02d}:{random.choice(['00', '30'])}:00"

                lectures.append({
                    "id": lecture_id,
                    "title": f"{subject.split(' (')[0]} - Lecture {i+1}",
                    "subject": subject,
                    "semester": semester,
                    "faculty_id": faculty_id,
                    "date": lecture_date,
                    "start_time": start_time,
                    "end_time": end_time
                })
                lecture_id += 1

    return lectures

def generate_attendance_data(lectures, student_data):
    attendance_data = []
    attendance_id = 1

    for lecture in lectures:
        semester = lecture["semester"]
        students = student_data.get(semester, [])

        for student in students:
            # Realistic attendance distribution: 70-80% present, 10-20% late, 5-15% absent
            attendance_type = random.choices(
                ["present", "late", "absent"],
                weights=[75, 15, 10],
                k=1
            )[0]

            if attendance_type == "absent":
                # No attendance record for absent students
                continue

            # Generate join time based on attendance type
            start_time = datetime.strptime(lecture["start_time"], "%H:%M:%S")

            if attendance_type == "present":
                # Join within 0-5 minutes of start
                join_delay = random.randint(0, 5)
            else:  # late
                # Join 6-20 minutes after start
                join_delay = random.randint(6, 20)

            join_time = (start_time + timedelta(minutes=join_delay)).strftime("%H:%M:%S")

            # Generate exit time (during or at end of lecture)
            end_time = datetime.strptime(lecture["end_time"], "%H:%M:%S")
            exit_delay = random.randint(0, 10)  # Exit 0-10 minutes before end
            exit_time = (end_time - timedelta(minutes=exit_delay)).strftime("%H:%M:%S")

            # Calculate duration in minutes
            join_dt = datetime.strptime(join_time, "%H:%M:%S")
            exit_dt = datetime.strptime(exit_time, "%H:%M:%S")
            duration = int((exit_dt - join_dt).total_seconds() / 60)

            attendance_data.append({
                "id": attendance_id,
                "student_enrollment": student["enrollment"],
                "lecture_id": lecture["id"],
                "status": attendance_type,
                "join_time": join_time,
                "exit_time": exit_time,
                "duration": duration
            })
            attendance_id += 1

    return attendance_data

def insert_specific_faculty_data():
    print("Loading specific faculty data...")
    faculty_data = SPECIFIC_FACULTY

    conn = get_db()
    cur = conn.cursor()

    try:
        print("Inserting students...")
        student_count = 0
        for semester, students in STUDENT_DATA.items():
            for student in students:
                # Insert user
                hashed_password = hash_password(student["password"])
                cur.execute("""
                    INSERT INTO users (name, email, password, role)
                    VALUES (?, ?, ?, 'student')
                """, (student["name"], student["email"], hashed_password))

                user_id = cur.lastrowid

                # Insert student
                cur.execute("""
                    INSERT INTO students (user_id, roll_number, department, semester)
                    VALUES (?, ?, 'Information Technology', ?)
                """, (user_id, student["enrollment"], semester))

                student_count += 1

        print(f"Inserted {student_count} students")

        print("Inserting specific faculty...")
        faculty_count = 0
        for faculty in faculty_data:
            # Insert user
            hashed_password = hash_password(faculty["password"])
            cur.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, 'faculty')
            """, (faculty["name"], faculty["email"], hashed_password))

            user_id = cur.lastrowid

            # Insert faculty
            cur.execute("""
                INSERT INTO faculty (user_id, faculty_id, department)
                VALUES (?, ?, ?)
            """, (user_id, faculty["faculty_id"], faculty["department"]))

            faculty_id_db = cur.lastrowid

            # Insert faculty subjects
            for subject in faculty["subjects"]:
                cur.execute("""
                    INSERT INTO faculty_subjects (faculty_id, semester, subject)
                    VALUES (?, ?, ?)
                """, (faculty_id_db, subject["semester"], subject["subject"]))

            faculty_count += 1

        print(f"Inserted {faculty_count} faculty members")

        print("Generating lectures for specific faculty...")
        lectures = generate_lectures(faculty_data)
        print(f"Generated {len(lectures)} lectures")

        print("Inserting lectures...")
        lecture_count = 0
        for lecture in lectures:
            # Convert date from DD-MM-YYYY to YYYY-MM-DD
            date_parts = lecture["date"].split("-")
            db_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"

            # Get faculty user_id
            cur.execute("SELECT user_id FROM faculty WHERE faculty_id = ?", (lecture["faculty_id"],))
            faculty_user_id = cur.fetchone()[0]

            # Insert lecture
            cur.execute("""
                INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius)
                VALUES (?, ?, ?, ?, 21.1702, 72.8311, 50)
            """, (lecture["title"], lecture["subject"], db_date, faculty_user_id))

            lecture_id = cur.lastrowid

            # Insert lecture session
            cur.execute("""
                INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester)
                VALUES (?, ?, ?, 'LOCATION', 0, 'scheduled', 'OFFLINE', '', ?)
            """, (lecture_id, lecture["start_time"], lecture["end_time"], lecture["semester"]))

            lecture_count += 1

        print(f"Inserted {lecture_count} lectures")

        print("Generating attendance data...")
        attendance_data = generate_attendance_data(lectures, STUDENT_DATA)
        print(f"Generated {len(attendance_data)} attendance records")

        print("Inserting attendance records...")
        attendance_count = 0
        for attendance in attendance_data:
            # Get student ID
            cur.execute("SELECT id FROM students WHERE roll_number = ?", (attendance["student_enrollment"],))
            student_result = cur.fetchone()
            if not student_result:
                continue
            student_id = student_result[0]

            # Get session ID for this lecture
            cur.execute("""
                SELECT ls.id FROM lecture_sessions ls
                JOIN lectures l ON l.id = ls.lecture_id
                WHERE l.id = ?
            """, (attendance["lecture_id"],))
            session_result = cur.fetchone()
            if not session_result:
                continue
            session_id = session_result[0]

            # Insert attendance
            cur.execute("""
                INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp)
                VALUES (?, ?, 21.1702, 72.8311, ?, ?, ?, ?)
            """, (student_id, session_id, attendance["status"], attendance["join_time"], attendance["exit_time"], attendance["join_time"]))

            attendance_count += 1

        print(f"Inserted {attendance_count} attendance records")

        conn.commit()
        print("All specific faculty data inserted successfully!")

        # Print summary
        print("\n=== SUMMARY ===")
        print(f"Students: {student_count}")
        print(f"Specific Faculty: {faculty_count}")
        print(f"Lectures: {lecture_count}")
        print(f"Attendance Records: {attendance_count}")

        # Print faculty details
        print("\n=== FACULTY MEMBERS ===")
        for faculty in faculty_data:
            print(f"• {faculty['name']} ({faculty['faculty_id']}) - {faculty['email']}")
            for subject in faculty['subjects']:
                print(f"  - Sem {subject['semester']}: {subject['subject']}")

    except Exception as e:
        conn.rollback()
        print(f"Error inserting data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    insert_specific_faculty_data()