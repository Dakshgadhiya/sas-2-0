import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import EmptyState from "../components/EmptyState";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";
import { formatTimeIST, normalizeTimestamp } from "../utils/time";

export default function MarkAttendance() {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marked, setMarked] = useState(false);
  const [markingLoading, setMarkingLoading] = useState(false);
  const { showSuccess, showError, showInfo, showWarning } = useNotification();

  async function loadActive() {
    setLoading(true);
    try {
      // Get student's semester first
      const profileRes = await apiFetch("/api/student/profile");
      const studentSemester = profileRes.ok ? (await profileRes.json()).profile?.semester : null;

      const res = await apiFetch("/api/lectures/sessions");
      const data = await res.json();
      const allSessions = data.sessions || [];
      
      const now = new Date();
      // Show lectures that are ACTIVE (currently ongoing) or UPCOMING (not ended)
      // AND match the student's semester
      const activeSessions = allSessions.filter(session => {
        // Filter by student's semester
        if (studentSemester && String(session.semester) !== String(studentSemester)) {
          return false;
        }
        
        let start = null;
        let end = null;
        if (session.start_time) {
          const ms = Date.parse(normalizeTimestamp(session.start_time));
          start = Number.isNaN(ms) ? null : new Date(ms);
        }
        if (session.end_time) {
          const ms = Date.parse(normalizeTimestamp(session.end_time));
          end = Number.isNaN(ms) ? null : new Date(ms);
        }
        // Include sessions that haven't ended yet and are not closed
        return end && end >= now && session.status !== 'closed';
      });

      setSessions(activeSessions);

      if (activeSessions.length === 1) {
        setSelectedSession(activeSessions[0]);
        const statusRes = await apiFetch(`/api/attendance/status/${activeSessions[0].id}`);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setMarked(statusData.marked);
        }
      }
    } catch (err) {
      showError("Something went wrong. Please try again");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadActive();
  }, []);

  async function handleMarkAttendance(session) {
    // Check if lecture has started
    const now = new Date();
    let startTime = null;
    if (session.start_time) {
      const ms = Date.parse(normalizeTimestamp(session.start_time));
      startTime = Number.isNaN(ms) ? null : new Date(ms);
    }
    
    if (startTime && now < startTime) {
      showError("Attendance not started yet. Please wait for the lecture to begin.");
      return;
    }

    setMarkingLoading(true);
    try {
      const res = await apiFetch("/api/attendance/mark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: session.id })
      });
      const data = await res.json();
      
      if (res.ok) {
        showSuccess("Attendance marked successfully");
        setMarked(true);
      } else if (data.error?.includes("late")) {
        showWarning("You joined late. Attendance marked as Late");
        setMarked(true);
      } else {
        showError(data.error || "Attendance not allowed at this time");
      }
    } catch (err) {
      showError("Something went wrong. Please try again");
    } finally {
      setMarkingLoading(false);
    }
  }

  function handleSessionSelect(session) {
    setSelectedSession(session);
    setMarked(false);
    apiFetch(`/api/attendance/status/${session.id}`)
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data?.marked) setMarked(true);
      })
      .catch(err => console.error(err));
  }

  function renderSessionCard() {
    if (!selectedSession) return null;
    const sessionStart = selectedSession.start_time ? formatTimeIST(selectedSession.start_time) : 'N/A';
    const sessionDate = selectedSession.lecture_date || 'N/A';

    return (
      <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-8 max-w-lg">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-12 h-12 bg-[#0466c8]/10 dark:bg-[#0466c8]/20 rounded-lg flex items-center justify-center text-xl flex-shrink-0 text-[#0466c8] dark:text-[#60a5fa]" />
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{selectedSession.lecture_title}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{selectedSession.lecture_subject}</p>
          </div>
        </div>

        <div className="space-y-3 pb-6 border-b border-slate-200 dark:border-[#33415c]">
          <div className="flex justify-between text-sm">
            <span className="text-slate-600 dark:text-slate-400">Faculty:</span>
            <span className="font-medium text-slate-900 dark:text-white">{selectedSession.faculty_name || "Unknown"}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-600 dark:text-slate-400">Date:</span>
            <span className="font-medium text-slate-900 dark:text-white">{sessionDate}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-600 dark:text-slate-400">Time:</span>
            <span className="font-medium text-slate-900 dark:text-white">{sessionStart}</span>
          </div>
        </div>

        {marked ? (
          <div className="mt-6 p-4 bg-success/10 dark:bg-success/20 border border-success/30 rounded-lg">
            <p className="font-bold text-success dark:text-green-300">Attendance Marked</p>
            <p className="text-sm text-success/80 dark:text-green-200">Your attendance has been recorded</p>
          </div>
        ) : (
          <button
            onClick={() => handleMarkAttendance(selectedSession)}
            disabled={markingLoading}
            className="w-full mt-6 rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white font-bold py-3 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-md hover:shadow-lg uppercase tracking-wide"
          >
            {markingLoading ? "Marking Attendance..." : "Mark Attendance"}
          </button>
        )}
      </div>
    );
  }

  return (
    <SidebarLayout role="student">
      <div>
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Mark Attendance</h1>
        <p className="text-neutral dark:text-slate-400 mb-8">Mark your attendance for the active lecture session</p>
        
        <div className="mt-6">
          {loading ? (
            <div className="p-8 text-center bg-info/10 dark:bg-info/20 rounded-lg text-info dark:text-[#60a5fa]">
              <p className="text-sm">Loading sessions...</p>
            </div>
          ) : sessions.length === 0 ? (
            <EmptyState
              title="No Active Lecture"
              description="No lecture session is currently active for your semester. Check back when a lecture starts."
            />
          ) : sessions.length === 1 ? (
            renderSessionCard()
          ) : (
            <div>
              <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                {sessions.map(session => (
                  <button
                    key={session.id}
                    onClick={() => handleSessionSelect(session)}
                    className={`rounded-lg border p-4 transition-all text-left ${
                      selectedSession?.id === session.id
                        ? 'border-[#0466c8] bg-[#0466c8]/5 dark:bg-[#0466c8]/10 shadow-md'
                        : 'border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] hover:border-[#0466c8]'
                    }`}
                  >
                    <p className="font-bold text-slate-900 dark:text-white">{session.lecture_title}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{session.lecture_subject}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                      {session.start_time ? formatTimeIST(session.start_time) : 'N/A'}
                    </p>
                  </button>
                ))}
              </div>
              {renderSessionCard()}
            </div>
          )}
        </div>
      </div>
    </SidebarLayout>
  );
}
