import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import MetricCard from "../components/MetricCard";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";
import { formatTimeIST, normalizeTimestamp } from "../utils/time";

function parseSessionStart(session) {
  if (session.start_time) {
    try {
      const norm = normalizeTimestamp(session.start_time);
      const ms = Date.parse(norm);
      if (!Number.isNaN(ms)) return new Date(ms);
    } catch (e) {
      // fallthrough
    }
  }
  if (session.lecture_date) {
    try {
      const dms = Date.parse(normalizeTimestamp(`${session.lecture_date}T00:00:00`));
      if (!Number.isNaN(dms)) return new Date(dms);
    } catch (e) {
      // fallthrough
    }
  }
  return null;
}

export default function FacultyDashboard() {
  const [summary, setSummary] = useState({ total_students: 0, today_attendance: 0, total_sessions: 0, semesters: {} });
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
          // Fallback to all semesters if none found
          setTeachingSemesters(semesters.length > 0 ? semesters : ["1", "2", "3", "4", "5", "6"]);
        } else {
          // Fallback if profile fetch fails
          setTeachingSemesters(["1", "2", "3", "4", "5", "6"]);
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
    let end = null;
    if (s.end_time) {
      try {
        const ms = Date.parse(normalizeTimestamp(s.end_time));
        if (!Number.isNaN(ms)) end = new Date(ms);
      } catch (e) {
        end = null;
      }
    }
    const statusOk = !s.status || s.status === "scheduled" || s.status === "active";
    if (!statusOk) return false;

    if (s.status === "active") return true;
    if (start && end) return end >= now;
    if (start) return start >= now;
    if (s.lecture_date) {
      try {
        const dms = Date.parse(normalizeTimestamp(`${s.lecture_date}T23:59:59`));
        if (!Number.isNaN(dms)) return new Date(dms) >= now;
      } catch (e) {
        return false;
      }
    }
    return true;
  });

  const myUpcoming = userId ? upcoming.filter((s) => Number(s.faculty_id) === Number(userId)) : upcoming;

  const past = selectedSemester === "all"
    ? Object.values(summary.semesters).flatMap(sem => sem.past_lectures || []).sort((a, b) => {
        const ad = a.lecture_date || '';
        const bd = b.lecture_date || '';
        return bd.localeCompare(ad);
      })
    : summary.semesters[selectedSemester]?.past_lectures || [];

  // Calculate semester-specific metrics
  const semesterMetrics = selectedSemester === "all" 
    ? { students: summary.total_students, attendance: summary.today_attendance, sessions: summary.total_sessions }
    : summary.semesters[selectedSemester] 
      ? { 
          students: students.filter(s => String(s.semester) === String(selectedSemester)).length,
          attendance: summary.semesters[selectedSemester].today_attendance,
          sessions: summary.semesters[selectedSemester].past_lectures.length
        }
      : { students: 0, attendance: 0, sessions: 0 };

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

      {/* Scheduled & Active Lectures */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          <h2 className="text-lg font-bold text-[#0466c8] dark:text-[#60a5fa] mb-4 uppercase tracking-wide">Scheduled & Active Lectures</h2>
          
          {myUpcoming.length === 0 ? (
            <div className="text-sm text-[#889696] py-8 text-center">
              No scheduled or active lectures for the selected semester.
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {myUpcoming.map((s) => (
                <div key={s.id} className={`rounded-lg border p-4 hover:border-[#0466c8] transition-all ${
                  s.status === 'active' 
                    ? 'border-green-500 bg-green-50 dark:bg-green-950 hover:bg-green-100 dark:hover:bg-green-900'
                    : 'border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#001845] hover:bg-slate-50 dark:hover:bg-[#002855]'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-[#0466c8] dark:text-[#60a5fa]">{s.lecture_title}</div>
                    {s.status === 'active' && (
                      <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded">LIVE</span>
                    )}
                  </div>
                  <div className="text-sm text-neutral dark:text-slate-400 mt-1">{s.lecture_subject}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-neutral dark:text-slate-400 mt-2">
                    <div>📅 {s.lecture_date}</div>
                    <div>⏰ {formatTimeIST(s.start_time)} - {formatTimeIST(s.end_time)}</div>
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
                    <div>📅 {s.lecture_date}</div>
                    <div>⏰ {formatTimeIST(s.start_time)} - {formatTimeIST(s.end_time)}</div>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-2">👥 {s.attendance_count ?? 0} attendees</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </SidebarLayout>
  );
}
