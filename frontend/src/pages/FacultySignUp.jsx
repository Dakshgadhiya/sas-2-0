import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { setToken, apiFetch } from "../services/api";
import { SEMESTER_SUBJECTS, DEPARTMENT, getFullSubjectName } from "../constants/subjects";

const ODD_SEMESTERS = ["1", "3", "5"];
const EVEN_SEMESTERS = ["2", "4", "6"];

export default function FacultySignup() {
  const [form, setForm] = useState({
    name: "",
    faculty_id: "",
    email: "",
    password: "",
    department: DEPARTMENT
  });
  const [subjects, setSubjects] = useState([{ semester: "1", subject: SEMESTER_SUBJECTS["1"][0] }]);
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  function addSubject() {
    setSubjects([...subjects, { semester: "1", subject: SEMESTER_SUBJECTS["1"][0] }]);
  }

  function removeSubject(index) {
    if (subjects.length > 1) {
      setSubjects(subjects.filter((_, i) => i !== index));
    }
  }

  function updateSubject(index, field, value) {
    const updated = [...subjects];
    updated[index][field] = value;
    // If semester changed, reset subject to first of new semester
    if (field === "semester") {
      updated[index].subject = SEMESTER_SUBJECTS[value][0];
    }
    setSubjects(updated);
  }

  function getValidSemesters() {
    // Return all semesters (allow duplicates for same semester)
    return ["1", "2", "3", "4", "5", "6"];
  }

  function getSubjectsForSemester(semester) {
    return SEMESTER_SUBJECTS[semester] || [];
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    setIsSubmitting(true);

    // Validate that at least one subject is selected
    if (subjects.length === 0) {
      setMessage("Please add at least one semester-subject pair");
      setIsSubmitting(false);
      return;
    }

    // Validate odd/even semesters
    for (const subj of subjects) {
      const sem = subj.semester;
      const semNum = parseInt(sem);
      if (semNum % 2 === 1 && !ODD_SEMESTERS.includes(sem)) {
        setMessage(`Invalid odd semester: ${sem}. Valid odd semesters: 1, 3, 5`);
        setIsSubmitting(false);
        return;
      }
      if (semNum % 2 === 0 && !EVEN_SEMESTERS.includes(sem)) {
        setMessage(`Invalid even semester: ${sem}. Valid even semesters: 2, 4, 6`);
        setIsSubmitting(false);
        return;
      }
    }

    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ 
        ...form, 
        role: "faculty",
        subjects: subjects
      })
    });
    const data = await res.json();
    if (res.ok) {
      setToken(data.token);
      setMessage("Faculty registration completed successfully.");
      
      // Redirect to faculty dashboard after successful registration
      setTimeout(() => {
        navigate("/faculty/dashboard");
      }, 1000);
    } else {
      setMessage(data.error || "Registration failed.");
    }
    setIsSubmitting(false);
  }

  return (
    <div className="min-h-screen bg-white dark:bg-[#001845] flex items-center justify-center p-8">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-8">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Faculty Signup</h1>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          {[
            ["name", "Full Name"],
            ["faculty_id", "Faculty ID"],
            ["email", "Email"],
            ["password", "Password"]
          ].map(([key, label]) => (
            <input
              key={key}
              type={key === "password" ? "password" : "text"}
              placeholder={label}
              className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          ))}
          
          <div>
            <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Department</label>
            <div className="w-full rounded-lg bg-slate-100 dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white font-medium">
              {DEPARTMENT}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Teaching Assignments</label>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {subjects.map((subj, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <select
                    className="flex-1 rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] text-sm transition-all"
                    value={subj.semester}
                    onChange={(e) => updateSubject(idx, "semester", e.target.value)}
                  >
                    {getValidSemesters().map(sem => (
                      <option key={sem} value={sem}>Semester {sem}</option>
                    ))}
                  </select>
                  <select
                    className="flex-1 rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] text-sm transition-all"
                    value={subj.subject}
                    onChange={(e) => updateSubject(idx, "subject", e.target.value)}
                  >
                    {getSubjectsForSemester(subj.semester).map(s => (
                      <option key={s} value={s}>{getFullSubjectName(s)}</option>
                    ))}
                  </select>
                  {subjects.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeSubject(idx)}
                      className="px-3 py-2 rounded-lg bg-slate-200 dark:bg-[#33415c] text-slate-900 dark:text-white hover:bg-slate-300 dark:hover:bg-[#4a5270] transition-colors border border-slate-300 dark:border-[#33415c] font-bold"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={addSubject}
              className="mt-2 w-full py-2 px-3 rounded-lg border border-dashed border-slate-300 dark:border-[#33415c] text-slate-900 dark:text-white hover:bg-slate-100 dark:hover:bg-[#001233] transition-colors text-sm font-bold uppercase tracking-wide"
            >
              + Add Another Semester
            </button>
          </div>

          <button
            className="w-full rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white font-bold py-3 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-md hover:shadow-lg uppercase tracking-wide"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Create Account"}
          </button>
        </form>
        <div className="flex items-center justify-between mt-4 text-sm text-neutral dark:text-slate-400">
          <button
            type="button"
            className="text-[#0466c8] dark:text-[#60a5fa] underline hover:text-[#034ba6] dark:hover:text-[#93c5fd]"
            onClick={() => navigate(-1)}
          >
            Back
          </button>
          <Link className="text-[#0466c8] dark:text-[#60a5fa] underline hover:text-[#034ba6] dark:hover:text-[#93c5fd]" to="/faculty/login">Already have an account? Login</Link>
        </div>
        {message && <div className={`text-sm mt-4 p-3 rounded-lg ${message.includes("successfully") ? "bg-success/10 text-success dark:text-green-300" : "bg-error/10 text-error dark:text-red-300"}`}>{message}</div>}
      </div>
    </div>
  );
}
