import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import MetricCard from "../components/MetricCard";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";

function parseSessionStart(session) {
  if (session.start_time) {
    const d = new Date(session.start_time);
    if (!Number.isNaN(d.getTime())) return d;
  }
  if (session.lecture_date) {
    const d = new Date(`${session.lecture_date}T00:00:00`);
    if (!Number.isNaN(d.getTime())) return d;
  }
  return null;
}

// Format time in IST
function formatTimeIST(timestamp) {
  if (!timestamp) return "N/A";
  return new Date(timestamp).toLocaleString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata"
  });
}

export default function FacultyDashboard() {
  const [summary, setSummary] = useState({ total_students: 0, today_attendance: 0, total_sessions: 0 });
  const [sessions, setSessions] = useState([]);
  const [students, setStudents] = useState([]);
  const [userId, setUserId] = useState(null);
  const [selectedSemester, setSelectedSemester] = useState("all");
  const [teachingSemesters, setTeachingSemesters] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showError, showInfo } = useNotification();

  useEffect(() => {
    async function load() {
      try {
        const res = await apiFetch("/api/faculty/summary");
        if (res.ok) setSummary(await res.json());

        const me = await apiFetch("/api/auth/me");
        if (me.ok) {
          const data = await me.json();
          setUserId(data.user?.id || null);
        }

        // Fetch faculty profile to get actual teaching semesters
        const profile = await apiFetch("/api/faculty/profile");
        if (profile.ok) {
          const data = await profile.json();
          const subjects = data.profile?.subjects || [];
          const semesters = [...new Set(subjects.map(s => s.semester))].sort();
          setTeachingSemesters(semesters);
        }

        // Fetch all students to filter by semester
        const studentsRes = await apiFetch("/api/students");
        if (studentsRes.ok) {
          const data = await studentsRes.json();
          setStudents(data.students || []);
        } else {
          showInfo("No students found for selected semester");
        }

        const sess = await apiFetch("/api/lectures/sessions");
        if (sess.ok) {
          const data = await sess.json();
          setSessions(data.sessions || []);
        }
      } catch (err) {
        showError("Something went wrong. Please try again");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // Filter sessions by selected semester
  const filteredSessions = selectedSemester === "all" 
    ? sessions 
    : sessions.filter(s => s.semester === selectedSemester);

  const upcoming = filteredSessions.filter((s) => {
    const start = parseSessionStart(s);
    const end = s.end_time ? new Date(s.end_time) : null;
    const statusOk = !s.status || s.status === "scheduled" || s.status === "active";
    if (!statusOk) return false;

    if (s.status === "active") return true;
    if (start && end) return end >= now;
    if (start) return start >= now;
    if (s.lecture_date) return new Date(`${s.lecture_date}T23:59:59`) >= now;
    return true;
  });

  const myUpcoming = userId ? upcoming.filter((s) => Number(s.faculty_id) === Number(userId)) : upcoming;

  const past = userId 
    ? filteredSessions.filter((s) => {
        const end = s.end_time ? new Date(s.end_time) : null;
        return Number(s.faculty_id) === Number(userId) && end && end < now && (s.status === "closed" || s.status === "ended");
      }).sort((a, b) => new Date(b.end_time) - new Date(a.end_time))
    : [];

  // Calculate semester-specific metrics
  const semesterMetrics = selectedSemester === "all" 
    ? { students: summary.total_students, attendance: summary.today_attendance, sessions: summary.total_sessions }
    : {
        students: students.filter(s => String(s.semester) === String(selectedSemester)).length,
        attendance: filteredSessions.reduce((sum, s) => sum + (s.attendance_count || 0), 0),
        sessions: filteredSessions.filter(s => Number(s.faculty_id) === Number(userId)).length
      };

  return (
    <SidebarLayout role="faculty">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Faculty Dashboard</h1>
        <p className="text-neutral dark:text-slate-400 mt-2">Manage your lectures and track student attendance</p>
      </div>
      
      {/* Semester Selector */}
      <div className="mb-8 flex gap-2 border-b border-slate-200 dark:border-[#33415c] overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedSemester("all")}
          className={`px-4 py-2 font-bold uppercase tracking-wide border-b-2 transition-colors whitespace-nowrap -mb-2 ${
            selectedSemester === "all"
              ? "border-[#0466c8] text-[#0466c8] dark:text-[#60a5fa]"
              : "border-transparent text-neutral dark:text-slate-400 hover:text-[#0466c8] dark:hover:text-[#60a5fa]"
          }`}
        >
          All Semesters
        </button>
        {teachingSemesters.map(sem => (
          <button
            key={sem}
            onClick={() => setSelectedSemester(String(sem))}
            className={`px-4 py-2 font-bold uppercase tracking-wide border-b-2 transition-colors whitespace-nowrap -mb-2 ${
              selectedSemester === String(sem)
                ? "border-[#0466c8] text-[#0466c8] dark:text-[#60a5fa]"
                : "border-transparent text-neutral dark:text-slate-400 hover:text-[#0466c8] dark:hover:text-[#60a5fa]"
            }`}
          >
            Semester {sem}
          </button>
        ))}
      </div>

      {/* Dynamic Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard 
          label={`Total Students${selectedSemester !== "all" ? " (Sem " + selectedSemester + ")" : ""}`} 
          value={semesterMetrics.students} 
        />
        <MetricCard 
          label={`Today Attendance${selectedSemester !== "all" ? " (Sem " + selectedSemester + ")" : ""}`} 
          value={semesterMetrics.attendance} 
        />
        <MetricCard 
          label={`Lecture Sessions${selectedSemester !== "all" ? " (Sem " + selectedSemester + ")" : ""}`} 
          value={semesterMetrics.sessions} 
        />
      </div>

      {/* Scheduled Lectures */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          <h2 className="text-lg font-bold text-[#0466c8] dark:text-[#60a5fa] mb-4 uppercase tracking-wide">Scheduled Lectures</h2>
          
          {myUpcoming.length === 0 ? (
            <div className="text-sm text-[#889696] py-8 text-center">
              No scheduled lectures for the selected semester.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {myUpcoming.map((s) => (
                <div key={s.id} className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#001845] p-4 hover:border-[#0466c8] hover:bg-slate-50 dark:hover:bg-[#002855] transition-all">
                  <div className="font-semibold text-[#0466c8] dark:text-[#60a5fa]">{s.lecture_title}</div>
                  <div className="text-sm text-neutral dark:text-slate-400 mt-1">{s.lecture_subject}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-neutral dark:text-slate-400 mt-2">
                    <div>{s.lecture_date}</div>
                    <div>{formatTimeIST(s.start_time)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Past Lectures */}
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          <h2 className="text-lg font-bold text-[#0466c8] dark:text-[#60a5fa] mb-4 uppercase tracking-wide">Past Lectures</h2>
          
          {past.length === 0 ? (
            <div className="text-sm text-neutral dark:text-slate-400 py-8 text-center">
              No past lectures for the selected semester.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {past.map((s) => (
                <div key={s.id} className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#001845] p-4 hover:border-[#0466c8] hover:bg-slate-50 dark:hover:bg-[#002855] transition-all">
                  <div className="font-semibold text-[#0466c8] dark:text-[#60a5fa]">{s.lecture_title}</div>
                  <div className="text-sm text-neutral dark:text-slate-400 mt-1">{s.lecture_subject}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-neutral dark:text-slate-400 mt-2">
                    <div>{s.lecture_date}</div>
                    <div>{s.attendance_count ?? 0} attendees</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </SidebarLayout>
  );
}
