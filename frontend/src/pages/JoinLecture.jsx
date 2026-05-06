import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import EmptyState from "../components/EmptyState";
import { apiFetch } from "../services/api";
import { formatTimeIST, normalizeTimestamp } from "../utils/time";

export default function JoinLecture() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadSessions() {
    setLoading(true);
    const res = await apiFetch("/api/lectures/sessions");
    const data = await res.json();
    const allSessions = data.sessions || [];
    const now = new Date();

    const upcoming = allSessions
      .filter(s => {
        try {
          const ts = normalizeTimestamp(s.start_time);
          const ms = Date.parse(ts);
          if (Number.isNaN(ms)) return false;
          return new Date(ms) > now;
        } catch (e) {
          return false;
        }
      })
      .sort((a, b) => {
        const am = Date.parse(normalizeTimestamp(a.start_time));
        const bm = Date.parse(normalizeTimestamp(b.start_time));
        return am - bm;
      })
      .slice(0, 10);

    setSessions(upcoming);
    setLoading(false);
  }

  useEffect(() => {
    loadSessions();
  }, []);

  return (
    <SidebarLayout role="student">
      <h1 className="text-2xl font-bold text-[#5F7470]">Upcoming Lectures</h1>
      <div className="mt-4 rounded-2xl border border-[#B8BDB5] bg-[#E0E2DB] p-4 text-sm text-[#5F7470]">
        📌 All lectures are offline. Use "Mark Attendance" to mark your presence when the lecture is active.
      </div>
      <div className="mt-6">
        {loading ? (
          <div className="text-[#889696]">Loading lectures...</div>
        ) : sessions.length === 0 ? (
          <EmptyState
            title="No Upcoming Lectures"
            description="There are no upcoming lectures scheduled."
          />
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div key={session.id} className="rounded-xl border border-[#B8BDB5] bg-[#E0E2DB] p-4">
                <div className="font-semibold text-[#5F7470]">{session.lecture_title}</div>
                <div className="text-sm text-[#889696] mt-1">
                  {session.lecture_subject} • {session.lecture_date} • {session.faculty_name || "Unknown"}
                </div>
                <div className="text-xs text-[#889696] mt-2">
                  📅 {formatTimeIST(session.start_time)} - {formatTimeIST(session.end_time)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </SidebarLayout>
  );
}
