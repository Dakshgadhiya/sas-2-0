import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SidebarLayout from "../components/SidebarLayout";
import EmptyState from "../components/EmptyState";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";

export default function MarkAttendance() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marked, setMarked] = useState(false);
  const [markingLoading, setMarkingLoading] = useState(false);
  const navigate = useNavigate();
  const { showSuccess, showError, showInfo, showWarning } = useNotification();

  async function loadActive() {
    setLoading(true);
    try {
      const res = await apiFetch("/api/lectures/sessions/active");
      const data = await res.json();
      const activeSession = data.active ? data.session : null;
      setSession(activeSession);

      if (activeSession) {
        const statusRes = await apiFetch(`/api/attendance/status/${activeSession.id}`);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setMarked(statusData.marked);
        }
      } else {
        showInfo("No lectures available for your semester");
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
    setMarkingLoading(true);

    try {
      const res = await apiFetch("/api/attendance/mark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: session.id
        })
      });
      const data = await res.json();
      
      if (res.ok) {
        showSuccess("Attendance marked successfully");
        setMarked(true);
      } else {
        if (data.error?.includes("late")) {
          showWarning("You joined late. Attendance marked as Late");
          setMarked(true);
        } else if (data.error?.includes("Attendance already")) {
          showInfo("Attendance already marked");
        } else if (data.error?.includes("authorized")) {
          showError("You are not authorized for this lecture");
        } else if (data.error?.includes("not")) {
          showError("Session not started yet");
        } else {
          showError(data.error || "Attendance not allowed at this time");
        }
      }
    } catch (err) {
      showError("Something went wrong. Please try again");
    } finally {
      setMarkingLoading(false);
    }
  }

  function renderSessionCard() {
    if (!session) return null;

    const sessionStart = session.start_time ? new Date(session.start_time).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'N/A';
    const sessionDate = session.lecture_date || 'N/A';

    return (
      <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-8 max-w-lg">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-12 h-12 bg-[#0466c8]/10 dark:bg-[#0466c8]/20 rounded-lg flex items-center justify-center text-xl flex-shrink-0 text-[#0466c8] dark:text-[#60a5fa]">
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{session.lecture_title}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{session.lecture_subject}</p>
          </div>
        </div>

        {/* Details */}
        <div className="space-y-3 pb-6 border-b border-slate-200 dark:border-[#33415c]">
          <div className="flex justify-between text-sm">
            <span className="text-slate-600 dark:text-slate-400">Faculty:</span>
            <span className="font-medium text-slate-900 dark:text-white">{session.faculty_name || "Unknown"}</span>
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

        {/* Status */}
        {marked ? (
          <div className="mt-6 p-4 bg-success/10 dark:bg-success/20 border border-success/30 rounded-lg flex items-center gap-3">
            <div>
              <p className="font-bold text-success dark:text-green-300">Attendance Marked</p>
              <p className="text-sm text-success/80 dark:text-green-200">Your attendance has been recorded</p>
            </div>
          </div>
        ) : (
          <div className="mt-6">
            <button
              onClick={() => handleMarkAttendance(session)}
              disabled={markingLoading}
              className="w-full rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white font-bold py-3 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-md hover:shadow-lg uppercase tracking-wide"
            >
              {markingLoading ? "Marking Attendance..." : "Mark Attendance"}
            </button>
          </div>
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
              <p className="text-sm">Loading session...</p>
            </div>
          ) : !session ? (
            <EmptyState
              title="No Active Lecture"
              description="No lecture session is currently active. Check back when a lecture starts."
            />
          ) : (
            renderSessionCard()
          )}
        </div>
      </div>
    </SidebarLayout>
  );
}
