import React, { useEffect, useState, useMemo } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";

export default function StudentList() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSemester, setSelectedSemester] = useState("1");

  useEffect(() => {
    async function loadStudents() {
      const res = await apiFetch("/api/admin/students");
      if (res.ok) {
        const data = await res.json();
        // Sort students by enrollment number in ascending order
        const sorted = data.sort((a, b) => {
          const aRoll = parseInt(a.roll_number) || 0;
          const bRoll = parseInt(b.roll_number) || 0;
          return aRoll - bRoll;
        });
        setStudents(sorted);
      }
      setLoading(false);
    }
    loadStudents();
  }, []);

  // Get all semesters from students
  const allSemesters = useMemo(() => {
    const semesters = [...new Set(students.map(s => s.semester))].sort();
    return semesters;
  }, [students]);

  // Filter students by selected semester
  const semesterStudents = useMemo(() => {
    return students.filter(s => s.semester === selectedSemester);
  }, [students, selectedSemester]);

  if (loading) return <SidebarLayout role="faculty"><div className="text-neutral dark:text-slate-400">Loading...</div></SidebarLayout>;

  return (
    <SidebarLayout role="faculty">
      <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] mb-6 uppercase tracking-wide">Student List</h1>
      
      {/* Semester Tabs */}
      {allSemesters.length > 0 && (
        <div className="mb-6 flex gap-2 flex-wrap">
          {allSemesters.map(sem => (
            <button
              key={sem}
              onClick={() => setSelectedSemester(sem)}
              className={`px-4 py-2 rounded-lg font-bold transition-colors uppercase tracking-wide ${
                selectedSemester === sem
                  ? "bg-[#0466c8] dark:bg-[#0353a4] text-white shadow-md"
                  : "bg-slate-200 dark:bg-[#33415c] text-slate-900 dark:text-white hover:bg-slate-300 dark:hover:bg-[#4a5270]"
              }`}
            >
              Semester {sem}
            </button>
          ))}
        </div>
      )}

      {/* Student Table */}
      <div className="bg-white dark:bg-[#002855] rounded-lg shadow border border-slate-200 dark:border-[#33415c] overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 dark:border-[#33415c] bg-slate-50 dark:bg-[#001845]">
              <th className="text-left py-3 px-6 text-[#0466c8] dark:text-[#60a5fa] font-bold uppercase tracking-wide">Enrollment No</th>
              <th className="text-left py-3 px-6 text-[#0466c8] dark:text-[#60a5fa] font-bold uppercase tracking-wide">Full Name</th>
              <th className="text-left py-3 px-6 text-[#0466c8] dark:text-[#60a5fa] font-bold uppercase tracking-wide">Email ID</th>
              <th className="text-left py-3 px-6 text-[#0466c8] dark:text-[#60a5fa] font-bold uppercase tracking-wide">Department</th>
              <th className="text-left py-3 px-6 text-[#0466c8] dark:text-[#60a5fa] font-bold uppercase tracking-wide">Semester</th>
            </tr>
          </thead>
          <tbody>
            {semesterStudents.map((student, idx) => (
              <tr key={idx} className="border-b border-slate-200 dark:border-[#33415c] hover:bg-slate-50 dark:hover:bg-[#001845] transition-colors">
                <td className="py-3 px-6 text-slate-900 dark:text-white font-bold">{student.roll_number}</td>
                <td className="py-3 px-6 text-slate-900 dark:text-white">{student.name}</td>
                <td className="py-3 px-6 text-neutral dark:text-slate-400">{student.email}</td>
                <td className="py-3 px-6 text-neutral dark:text-slate-400">{student.department || "-"}</td>
                <td className="py-3 px-6 text-neutral dark:text-slate-400">{student.semester || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {semesterStudents.length === 0 && (
          <div className="text-center py-8 text-neutral dark:text-slate-400">
            No students found in Semester {selectedSemester}.
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="mt-4 text-sm text-neutral dark:text-slate-400">
        Showing {semesterStudents.length} student(s) in Semester {selectedSemester} 
        {allSemesters.length > 0 && ` (Total: ${students.length})`}
      </div>
    </SidebarLayout>
  );
}