import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";

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

export default function StudentLectures() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [studentSemester, setStudentSemester] = useState(null);
  const [facultyMap, setFacultyMap] = useState({});

  useEffect(() => {
    async function load() {
      // Get student profile to know their semester
      const profile = await apiFetch("/api/student/profile");
      if (profile.ok) {
        const data = await profile.json();
        setStudentSemester(data.profile?.semester || "1");
      }

      // Fetch all faculty to create name mapping
      const facultyRes = await apiFetch("/api/faculty/list");
      if (facultyRes.ok) {
        const data = await facultyRes.json();
        const fmap = {};
        (data.faculty || []).forEach(f => {
          fmap[f.id] = f.name;
        });
        setFacultyMap(fmap);
      }

      // Fetch all sessions
      const res = await apiFetch("/api/lectures/sessions");
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
      setLoading(false);
    }
    load();
  }, []);

  const now = new Date();

  // Filter sessions for student's semester
  const studentSessions = studentSemester
    ? sessions.filter(s => String(s.semester) === String(studentSemester))
    : sessions;

  // Upcoming lectures
  const upcoming = studentSessions
    .filter(s => {
      const start = parseSessionStart(s);
      const end = s.end_time ? new Date(s.end_time) : null;
      const statusOk = !s.status || s.status === "scheduled" || s.status === "active";
      if (!statusOk) return false;
      if (s.status === "active") return true;
      if (start && end) return end >= now;
      if (start) return start >= now;
      if (s.lecture_date) return new Date(`${s.lecture_date}T23:59:59`) >= now;
      return true;
    })
    .sort((a, b) => parseSessionStart(a)?.getTime() - parseSessionStart(b)?.getTime());

  // Past lectures
  const past = studentSessions
    .filter(s => {
      const end = s.end_time ? new Date(s.end_time) : null;
      return end && end < now && (s.status === "closed" || s.status === "ended");
    })
    .sort((a, b) => new Date(b.end_time) - new Date(a.end_time));

  const LectureCard = ({ session }) => (
    <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-bold text-slate-900 dark:text-white text-lg uppercase tracking-wide">{session.lecture_title}</h3>
          <p className="text-sm text-neutral dark:text-slate-400 mt-1">{session.lecture_subject}</p>
        </div>
        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-[#0466c8]/10 dark:bg-[#0466c8]/20 text-[#0466c8] dark:text-[#60a5fa] ml-2 uppercase tracking-wide">
          Sem {session.semester}
        </span>
      </div>
      <div className="space-y-2 text-sm text-neutral dark:text-slate-400 border-t border-slate-200 dark:border-[#33415c] pt-3">
        <div className="flex items-center">
          <span className="font-medium w-24">Faculty:</span>
          <span className="text-slate-900 dark:text-white">{facultyMap[session.faculty_id] || "N/A"}</span>
        </div>
        <div className="flex items-center">
          <span className="font-medium w-24">Date:</span>
          <span className="text-slate-900 dark:text-white">{session.lecture_date}</span>
        </div>
        <div className="flex items-center">
          <span className="font-medium w-24">Time:</span>
          <span className="text-slate-900 dark:text-white">
            {formatTimeIST(session.start_time)} - {formatTimeIST(session.end_time)}
          </span>
        </div>
        <div className="flex items-center">
          <span className="font-medium w-24">Type:</span>
          <span className="capitalize text-slate-900 dark:text-white">{session.attendance_type || "N/A"}</span>
        </div>
        {session.mode && (
          <div className="flex items-center">
            <span className="font-medium w-24">Mode:</span>
            <span className="capitalize text-slate-900 dark:text-white">{session.mode}</span>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <SidebarLayout role="student">
        <div className="text-center py-12">
          <div className="text-neutral dark:text-slate-400">Loading lectures...</div>
        </div>
      </SidebarLayout>
    );
  }

  return (
    <SidebarLayout role="student">
      <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">My Lectures</h1>
      <p className="text-neutral dark:text-slate-400 mt-2">View your scheduled and past lectures</p>

      {/* Upcoming Lectures */}
      <div className="mt-8">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-[#0466c8] dark:text-[#60a5fa] flex items-center uppercase tracking-wide">
            <span className="inline-block w-1 h-6 bg-[#0466c8] dark:bg-[#60a5fa] rounded mr-3"></span>
            Scheduled / Upcoming Lectures
          </h2>
          <p className="text-sm text-neutral dark:text-slate-400 mt-1">
            {upcoming.length} lecture(s) scheduled
          </p>
        </div>

        {upcoming.length === 0 ? (
          <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-6 text-center">
            <p className="text-neutral dark:text-slate-400">No upcoming lectures</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {upcoming.map(session => (
              <LectureCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>

      {/* Past Lectures */}
      <div className="mt-12">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-neutral dark:text-slate-400 flex items-center uppercase tracking-wide">
            <span className="inline-block w-1 h-6 bg-neutral dark:bg-slate-400 rounded mr-3"></span>
            Past Lectures
          </h2>
          <p className="text-sm text-neutral dark:text-slate-400 mt-1">
            {past.length} lecture(s) completed
          </p>
        </div>

        {past.length === 0 ? (
          <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-6 text-center">
            <p className="text-neutral dark:text-slate-400">No past lectures</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
            {past.map(session => (
              <LectureCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>
    </SidebarLayout>
  );
}
