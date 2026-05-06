import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
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

  // Organize lectures by time
  const upcoming = studentSessions
    .filter(s => {
      if (!s.end_time) return false;
      try {
        const endMs = Date.parse(normalizeTimestamp(s.end_time));
        return !Number.isNaN(endMs) && endMs >= Date.now() && s.status !== "closed";
      } catch (e) {
        return false;
      }
    })
    .sort((a, b) => {
      const am = Date.parse(normalizeTimestamp(a.start_time));
      const bm = Date.parse(normalizeTimestamp(b.start_time));
      return am - bm;
    });

  const past = studentSessions
    .filter(s => {
      if (s.status === "closed") return true;
      if (!s.end_time) return false;
      try {
        const endMs = Date.parse(normalizeTimestamp(s.end_time));
        return !Number.isNaN(endMs) && endMs < Date.now();
      } catch (e) {
        return false;
      }
    })
    .sort((a, b) => {
      const am = a.start_time ? Date.parse(normalizeTimestamp(a.start_time)) : Date.parse(normalizeTimestamp(`${a.lecture_date}T00:00:00`));
      const bm = b.start_time ? Date.parse(normalizeTimestamp(b.start_time)) : Date.parse(normalizeTimestamp(`${b.lecture_date}T00:00:00`));
      return bm - am;
    });

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
      <p className="text-neutral dark:text-slate-400 mt-2">View your upcoming lectures and attendance history</p>

      {/* Upcoming/Active Lectures */}
      <div className="mt-8">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-[#0466c8] dark:text-[#60a5fa] flex items-center uppercase tracking-wide">
            <span className="inline-block w-1 h-6 bg-[#0466c8] dark:bg-[#60a5fa] rounded mr-3"></span>
            Upcoming Lectures
          </h2>
          <p className="text-sm text-neutral dark:text-slate-400 mt-1">
            {upcoming.length} lecture(s) available
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
      <div className="mt-8">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-neutral dark:text-slate-400 flex items-center uppercase tracking-wide">
            <span className="inline-block w-1 h-6 bg-neutral dark:bg-slate-400 rounded mr-3"></span>
            Lecture History
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
