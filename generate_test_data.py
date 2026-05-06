import json
import random
from datetime import datetime, timedelta
import uuid

# Student data from the message
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
        # Note: User mentioned 14 students for sem 6 but only provided 13 in sem 5 list
        # I'll add one more student for sem 6 to make it 14
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

# Subject mapping from the constants
SUBJECTS = {
    "1": ["Mathematics", "Communication Skills in English", "Python Programming (PP)", "Introduction to IT Systems (IIS)", "Static Webpage Design (SWD)"],
    "2": ["Environment and Sustainability (ES)", "Physics", "Indian Constitution (IC)", "Engineering Mathematics", "Basic Electronics (BE)", "Advanced Python Programming (APP)", "Information Security Awareness (ISA)"],
    "3": ["Data Structure with Python (DSP)", "Linux Operating System (LOS)", "Database Management (DBMS)", "Fundamentals of Software Development (FSD)"],
    "4": ["Essentials of Digital Marketing (EDM)", "Object Oriented Programming with JAVA (OOPJ)", "Fundamentals of Machine Learning (FML)", "Web Development using PHP (PHP)"],
    "5": ["Foundation of AI and ML (FAIML)", "Mobile Computing and Networks (MCN)", "Advanced Java Programming (AJP)", "Mobile Application Development (MAD)"],
    "6": ["Cyber Security and Digital Forensics (CSDF)", "Cloud and Data Center Technologies (CDCT)", "Foundation of Block Chain (FBC)", "Software Development (SD)"]
}

# Generate faculty data (since not provided, I'll create reasonable faculty assignments)
def generate_faculty_data():
    faculty_data = []
    faculty_id = 1

    # Create faculty for each semester's subjects
    for semester, subjects in SUBJECTS.items():
        for subject in subjects:
            faculty_name = f"Prof. {subject.split(' (')[0].split()[-1]}"
            faculty_email = f"faculty{semester}{faculty_id}@college.edu"
            faculty_data.append({
                "name": faculty_name,
                "faculty_id": f"F{faculty_id:03d}",
                "email": faculty_email,
                "password": "12345678",
                "department": "Information Technology",
                "subjects": [{"semester": semester, "subject": subject}]
            })
            faculty_id += 1

    return faculty_data

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

def main():
    print("Generating comprehensive test data for SAS system...")

    # Generate faculty data
    faculty_data = generate_faculty_data()
    print(f"Generated {len(faculty_data)} faculty records")

    # Generate lectures
    lectures = generate_lectures(faculty_data)
    print(f"Generated {len(lectures)} lecture records")

    # Generate attendance data
    attendance_data = generate_attendance_data(lectures, STUDENT_DATA)
    print(f"Generated {len(attendance_data)} attendance records")

    # Count total students
    total_students = sum(len(students) for students in STUDENT_DATA.values())
    print(f"Total students: {total_students}")

    # Create output data structure
    output_data = {
        "students": STUDENT_DATA,
        "faculty": faculty_data,
        "lectures": lectures,
        "attendance": attendance_data,
        "summary": {
            "total_students": total_students,
            "total_faculty": len(faculty_data),
            "total_lectures": len(lectures),
            "total_attendance_records": len(attendance_data)
        }
    }

    # Save to JSON file
    with open("sas_test_data.json", "w") as f:
        json.dump(output_data, f, indent=2)

    print("Data saved to sas_test_data.json")

    # Generate SQL insert statements
    generate_sql_inserts(output_data)

def generate_sql_inserts(data):
    sql_statements = []

    # Students
    for semester, students in data["students"].items():
        for student in students:
            sql = f"""INSERT INTO users (name, email, password, role) VALUES ('{student["name"]}', '{student["email"]}', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8JZwHdQ9G', 'student');
INSERT INTO students (user_id, roll_number, department, semester) VALUES ((SELECT id FROM users WHERE email = '{student["email"]}'), '{student["enrollment"]}', 'Information Technology', '{semester}');"""
            sql_statements.append(sql)

    # Faculty
    for faculty in data["faculty"]:
        subjects_json = json.dumps(faculty["subjects"])
        sql = f"""INSERT INTO users (name, email, password, role) VALUES ('{faculty["name"]}', '{faculty["email"]}', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8JZwHdQ9G', 'faculty');
INSERT INTO faculty (user_id, faculty_id, department) VALUES ((SELECT id FROM users WHERE email = '{faculty["email"]}'), '{faculty["faculty_id"]}', '{faculty["department"]}');"""
        for subject in faculty["subjects"]:
            sql += f"""
INSERT INTO faculty_subjects (faculty_id, semester, subject) VALUES ((SELECT id FROM faculty WHERE faculty_id = '{faculty["faculty_id"]}'), '{subject["semester"]}', '{subject["subject"]}');"""
        sql_statements.append(sql)

    # Lectures
    for lecture in data["lectures"]:
        # Convert date format from DD-MM-YYYY to YYYY-MM-DD for database
        date_parts = lecture["date"].split("-")
        db_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"

        sql = f"""INSERT INTO lectures (title, subject, date, faculty_id, latitude, longitude, radius) VALUES ('{lecture["title"]}', '{lecture["subject"]}', '{db_date}', (SELECT user_id FROM faculty WHERE faculty_id = '{lecture["faculty_id"]}'), 21.1702, 72.8311, 50);
INSERT INTO lecture_sessions (lecture_id, start_time, end_time, attendance_type, threshold, status, mode, join_url, semester) VALUES ((SELECT id FROM lectures WHERE title = '{lecture["title"]}'), '{lecture["start_time"]}', '{lecture["end_time"]}', 'LOCATION', 0, 'scheduled', 'OFFLINE', '', '{lecture["semester"]}');"""
        sql_statements.append(sql)

    # Attendance
    for attendance in data["attendance"]:
        sql = f"""INSERT INTO attendance (student_id, session_id, latitude, longitude, status, start_time, end_time, timestamp) VALUES ((SELECT id FROM students WHERE roll_number = '{attendance["student_enrollment"]}'), (SELECT ls.id FROM lecture_sessions ls JOIN lectures l ON l.id = ls.lecture_id WHERE l.title = (SELECT title FROM lectures WHERE id = {attendance["lecture_id"]})), 21.1702, 72.8311, '{attendance["status"]}', '{attendance["join_time"]}', '{attendance["exit_time"]}', '{attendance["join_time"]}');"""
        sql_statements.append(sql)

    # Save SQL statements
    with open("sas_test_data.sql", "w") as f:
        f.write("-- SAS Test Data SQL Insert Statements\n\n")
        for sql in sql_statements:
            f.write(sql + "\n\n")

    print("SQL insert statements saved to sas_test_data.sql")

if __name__ == "__main__":
    main()