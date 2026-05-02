// Semester & Subject Mapping - Fixed for IT Department
export const SEMESTER_SUBJECTS = {
  "1": [
    "Mathematics",
    "Communication Skills in English",
    "Python Programming (PP)",
    "Introduction to IT Systems (IIS)",
    "Static Webpage Design (SWD)"
  ],
  "2": [
    "Environment and Sustainability (ES)",
    "Physics",
    "Indian Constitution (IC)",
    "Engineering Mathematics",
    "Basic Electronics (BE)",
    "Advanced Python Programming (APP)",
    "Information Security Awareness (ISA)"
  ],
  "3": [
    "Data Structure with Python (DSP)",
    "Linux Operating System (LOS)",
    "Database Management (DBMS)",
    "Fundamentals of Software Development (FSD)"
  ],
  "4": [
    "Essentials of Digital Marketing (EDM)",
    "Object Oriented Programming with JAVA (OOPJ)",
    "Fundamentals of Machine Learning (FML)",
    "Web Development using PHP (PHP)"
  ],
  "5": [
    "Foundation of AI and ML (FAIML)",
    "Mobile Computing and Networks (MCN)",
    "Advanced Java Programming (AJP)",
    "Mobile Application Development (MAD)"
  ],
  "6": [
    "Cyber Security and Digital Forensics (CSDF)",
    "Cloud and Data Center Technologies (CDCT)",
    "Foundation of Block Chain (FBC)",
    "Software Development (SD)"
  ]
};

export const DEPARTMENT = "Information Technology";
export const DEPARTMENT_CODE = "IT";

// Extract full name without short form (e.g., "Python Programming (PP)" → "Python Programming")
export function getFullSubjectName(subject) {
  return subject.replace(/\s*\([^)]*\)$/, '');
}

// Extract short form from subject name (e.g., "Python Programming (PP)" → "PP")
export function getShortSubjectForm(subject) {
  const match = subject.match(/\(([^)]+)\)$/);
  return match ? match[1] : subject; // Return short form or full name if no short form
}

// Get subjects for a specific semester
export function getSubjectsForSemester(semester) {
  return SEMESTER_SUBJECTS[semester] || [];
}

// Get all semesters as options
export function getAllSemesters() {
  return ["1", "2", "3", "4", "5", "6"].map(sem => ({
    value: sem,
    label: `Semester ${sem}`
  }));
}
