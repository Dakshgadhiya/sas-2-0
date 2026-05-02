# SAS_2.0 – Location-Based Attendance System

SAS_2.0 is a full stack web application designed to automate attendance using real-time GPS location. The system allows faculty to create lecture sessions and enables students to mark attendance only when they are physically present within the allowed location and time.

Attendance is validated using three main factors: student’s current location, lecture timing, and distance from the lecture location. The system ensures transparency and reduces proxy attendance.

---

## Tech Stack

Backend: Python (Flask)  
Frontend: React with Tailwind CSS  
Database: SQLite  
API Used: Browser Geolocation API  

---

## Key Features

Faculty Side:
- Create lecture sessions with automatic location detection  
- Select semester and subject  
- View dashboard analytics including total students, attendance, and lecture sessions  
- View attendance reports based on semester, subject, and session  
- Track late attendance  

Student Side:
- Register with semester details  
- View scheduled and upcoming lectures  
- View past lectures  
- Mark attendance using real-time GPS location  
- Attendance status includes Present, Late, and Absent  
- View attendance history  

---

## How It Works

1. Faculty creates a lecture session  
2. System captures the lecture location automatically  
3. Student opens the lecture session  
4. Student’s current location is fetched using browser GPS  
5. System checks distance and lecture time  
6. Attendance is marked based on conditions  

Present: Student is within allowed location and time  
Late: Student is within location but joins after 15 minutes  
Absent: Student is outside allowed range or invalid time  

---

## Attendance Logic

if student_location within allowed range AND within lecture time:
    mark Present
elif within range but after 15 minutes:
    mark Late
else:
    mark Absent

---

## Project Structure

SAS_2.0/

backend/  
- app.py  
- routes/  
- models/  
- services/  

frontend/  
- src/  
  - pages/  
  - components/  
  - services/  

requirements.txt  
README.md  

---

## Run Locally

Backend:

pip install -r requirements.txt  
python backend/app.py  

Backend runs on: http://localhost:5000  

Frontend:

cd frontend  
npm install  
npm run dev  

Frontend runs on: http://localhost:5173  

---

## Notes

- Location access must be enabled in the browser  
- Works best on mobile devices for accurate GPS  
- Late attendance is counted as present but marked separately  

---

## Future Improvements

- Online lecture support  
- Notification system for new lectures  
- Cloud database integration  
- Mobile application version  

---

## Author

Daksh Gadhiya  

---

## License

This project is created for educational purposes.