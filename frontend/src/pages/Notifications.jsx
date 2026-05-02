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

export default function Lectures({ role }) {
  const [sessions, setSessions] = useState([]);
  const [userId, setUserId] = useState(null);
  const [activeTab, setActiveTab] = useState("notifications");

  useEffect(() => {
    async function load() {
      if (role === "faculty") {
        const me = await apiFetch("/api/auth/me");
        if (me.ok) {
          const data = await me.json();
          setUserId(data.user?.id || null);
        }
      }

      const sess = await apiFetch("/api/lectures/sessions");
      if (sess.ok) {
        const data = await sess.json();
        setSessions(data.sessions || []);
      }
    }
    load();
  }, [role]);

  const now = new Date();
  const next24 = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const next15 = new Date(now.getTime() + 15 * 60 * 1000);

  let upcoming = sessions.filter((s) => {
    const start = parseSessionStart(s);
    if (!start) return false;
    return start <= next24 && (s.end_time ? new Date(s.end_time) >= now : start >= now);
  });

  if (role === "faculty" && userId) {
    upcoming = upcoming.filter((s) => Number(s.faculty_id) === Number(userId));
  }

  const reminders = upcoming.filter((s) => {
    const start = parseSessionStart(s);
    if (!start) return false;
    return start >= now && start <= next15;
  });

  const onlineUpcoming = upcoming.filter((s) => s.mode === "ONLINE");
  const offlineUpcoming = upcoming.filter((s) => s.mode === "OFFLINE");

  const onlineReminders = reminders.filter((s) => s.mode === "ONLINE");
  const offlineReminders = reminders.filter((s) => s.mode === "OFFLINE");

  const showTabs = true;

  function renderList(list, emptyText) {
    if (list.length === 0) {
      return <div className="text-sm text-[#889696]">{emptyText}</div>;
    }
    return (
      <div className="space-y-3">
        {list.map((s) => (
          <div key={s.id} className="rounded-xl border border-[#B8BDB5] bg-[#E0E2DB] p-4">
            <div className="font-semibold text-[#5F7470]">{s.lecture_title}</div>
            <div className="text-sm text-[#889696]">
              {s.lecture_subject} • {s.lecture_date} • {parseSessionStart(s)?.toLocaleString() || ""}
            </div>
            <div className="text-xs text-[#889696] mt-1">
              Faculty: {s.faculty_name || "Unknown"} • Type: {s.attendance_type}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <SidebarLayout role={role}>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#5F7470]">Lectures</h1>
        <div className="text-sm text-[#889696]">
          Total: <span className="font-semibold">{upcoming.length}</span>
        </div>
      </div>

      {showTabs && (
        <div className="mt-6 flex gap-2">
          <button
            className={`px-4 py-2 rounded-xl border ${activeTab === "notifications" ? "bg-[#E0E2DB] border-[#B8BDB5] text-[#5F7470]" : "bg-white border-[#B8BDB5] text-[#889696]"}`}
            onClick={() => setActiveTab("notifications")}
          >
            Notifications
          </button>
          <button
            className={`px-4 py-2 rounded-xl border ${activeTab === "reminders" ? "bg-[#E0E2DB] border-[#B8BDB5] text-[#5F7470]" : "bg-white border-[#B8BDB5] text-[#889696]"}`}
            onClick={() => setActiveTab("reminders")}
          >
            Reminders (15 mins)
          </button>
        </div>
      )}

      {activeTab === "notifications" && (
        <>
          <div className="mt-6 rounded-2xl border border-[#B8BDB5] bg-[#E0E2DB] shadow-sm p-6">
            <div className="flex items-center justify-between mb-3">
              <div className="font-bold text-[#5F7470]">Online Lectures (Next 24 Hours)</div>
              <span className="text-xs font-semibold bg-[#D2D4C8] text-[#5F7470] border border-[#B8BDB5] rounded-full px-2 py-0.5">{onlineUpcoming.length}</span>
            </div>
            {renderList(onlineUpcoming, "No online lecture.")}
          </div>

          <div className="mt-6 rounded-2xl border border-[#B8BDB5] bg-[#E0E2DB] shadow-sm p-6">
            <div className="flex items-center justify-between mb-3">
              <div className="font-bold text-[#5F7470]">Offline Lectures (Next 24 Hours)</div>
              <span className="text-xs font-semibold bg-[#D2D4C8] text-[#5F7470] border border-[#B8BDB5] rounded-full px-2 py-0.5">{offlineUpcoming.length}</span>
            </div>
            {renderList(offlineUpcoming, "No offline lecture.")}
          </div>
        </>
      )}

      {activeTab === "reminders" && (
        <>
          <div className="mt-6 rounded-2xl border border-[#B8BDB5] bg-[#E0E2DB] shadow-sm p-6">
            <div className="flex items-center justify-between mb-3">
              <div className="font-bold text-[#5F7470]">Online Reminders (Next 15 Minutes)</div>
              <span className="text-xs font-semibold bg-[#D2D4C8] text-[#5F7470] border border-[#B8BDB5] rounded-full px-2 py-0.5">{onlineReminders.length}</span>
            </div>
            {renderList(onlineReminders, "No online reminders.")}
          </div>

          <div className="mt-6 rounded-2xl border border-[#B8BDB5] bg-[#E0E2DB] shadow-sm p-6">
            <div className="flex items-center justify-between mb-3">
              <div className="font-bold text-[#5F7470]">Offline Reminders (Next 15 Minutes)</div>
              <span className="text-xs font-semibold bg-[#D2D4C8] text-[#5F7470] border border-[#B8BDB5] rounded-full px-2 py-0.5">{offlineReminders.length}</span>
            </div>
            {renderList(offlineReminders, "No offline reminders.")}
          </div>
        </>
      )}
    </SidebarLayout>
  );
}
