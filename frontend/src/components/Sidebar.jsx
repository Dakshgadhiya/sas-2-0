import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch } from "../services/api";

const studentLinks = [
  { to: "/student/dashboard", label: "DASHBOARD" },
  { to: "/student/profile", label: "PROFILE" },
  { to: "/student/faculty", label: "FACULTY" },
  { to: "/student/lectures", label: "LECTURES" },
  { to: "/student/attendance", label: "MARK ATTENDANCE" },
  { to: "/student/history", label: "ATTENDANCE HISTORY" }
];

const facultyLinks = [
  { to: "/faculty/dashboard", label: "DASHBOARD" },
  { to: "/faculty/profile", label: "PROFILE" },
  { to: "/faculty/create-lecture", label: "CREATE LECTURE" },
  { to: "/faculty/students", label: "STUDENTS" },
  { to: "/faculty/reports", label: "ATTENDANCE REPORTS" }
];

function computeCount(sessions, role, userId) {
  const now = new Date();
  const next24 = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  let upcoming = sessions.filter((s) => {
    const start = new Date(s.start_time);
    return start >= now && start <= next24;
  });
  if (role === "faculty" && userId) {
    upcoming = upcoming.filter((s) => s.faculty_id === userId);
  }
  return upcoming.length;
}

export default function Sidebar({ role }) {
  const links = role === "faculty" ? facultyLinks : studentLinks;
  const [sessions, setSessions] = useState([]);
  const [userId, setUserId] = useState(null);
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/");
  }

  function handleDeleteAccount() {
    if (window.confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
      deleteAccount();
    }
  }

  async function deleteAccount() {
    try {
      const res = await apiFetch("/api/user/delete-account", {
        method: "DELETE"
      });
      
      if (res.ok) {
        alert("Your account has been permanently deleted.");
        handleLogout();
      } else {
        const data = await res.json();
        alert(`Failed to delete account: ${data.error || "Unknown error"}`);
      }
    } catch (error) {
      alert(`Error deleting account: ${error.message}`);
    }
  }

  async function handleResetDatabase() {
    if (window.confirm("WARNING: This will delete ALL students, faculty, and lectures from the system. Are you sure?")) {
      const res = await apiFetch("/api/admin/reset-database", {
        method: "POST"
      });
      if (res.ok) {
        alert("Database reset successfully. All user data has been deleted.");
        handleLogout();
      } else {
        const data = await res.json();
        alert(`Reset failed: ${data.error || "Unknown error"}`);
      }
    }
  }

  useEffect(() => {
    let active = true;
    async function load() {
      if (role === "faculty") {
        const me = await apiFetch("/api/auth/me");
        if (me.ok) {
          const data = await me.json();
          if (active) setUserId(data.user?.id || null);
        }
      }
      const sess = await apiFetch("/api/lectures/sessions");
      if (sess.ok) {
        const data = await sess.json();
        if (active) setSessions(data.sessions || []);
      }
    }
    load();
    return () => { active = false; };
  }, [role]);

  const notifCount = useMemo(() => computeCount(sessions, role, userId), [sessions, role, userId]);

  return (
    <aside className="w-64 bg-gradient-to-b from-[#0466c8] to-[#0353a4] dark:from-[#002855] dark:to-[#001845] text-white shadow-lg px-6 py-8 sticky top-0 h-screen overflow-y-auto">
      {/* Logo */}
      <div className="mb-10">
        <div className="text-2xl font-black text-white mb-1">SAS</div>
        <p className="text-slate-200 dark:text-slate-300 text-xs font-medium tracking-wide">SMART ATTENDANCE SYSTEM</p>
      </div>

      {/* Navigation */}
      <nav className="space-y-1 mb-10">
        <div className="text-xs font-bold text-slate-200 dark:text-slate-300 uppercase tracking-widest px-3 py-2 mb-3">Menu</div>
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className="flex items-center justify-between rounded-lg px-3 py-3 text-slate-100 dark:text-slate-200 hover:bg-[#034ba6] dark:hover:bg-[#33415c] transition-all hover:shadow-md group font-semibold text-sm tracking-wide"
          >
            <span>{link.label}</span>
            {link.key === "notifications" && notifCount > 0 && (
              <span className="ml-2 inline-flex items-center justify-center text-xs font-bold bg-error text-white rounded-full w-5 h-5">
                {notifCount}
              </span>
            )}
          </Link>
        ))}
      </nav>

      {/* Account Actions */}
      <div className="border-t border-slate-400 dark:border-[#33415c] pt-6 space-y-2">
        <button
          onClick={handleLogout}
          className="w-full rounded-lg bg-slate-700 dark:bg-[#001233] hover:bg-slate-600 dark:hover:bg-[#003366] text-white px-3 py-2.5 text-sm font-bold transition-all hover:shadow-md flex items-center justify-center gap-2 uppercase tracking-wide"
        >
          Logout
        </button>
        <button
          onClick={handleDeleteAccount}
          className="w-full rounded-lg bg-error/20 hover:bg-error text-red-100 hover:text-white px-3 py-2.5 text-sm font-bold transition-colors border border-error/40 hover:border-error uppercase tracking-wide"
        >
          Delete Account
        </button>
        {role === "faculty" && (
          <button
            onClick={handleResetDatabase}
            className="w-full rounded-lg bg-warning/20 hover:bg-warning/30 text-yellow-100 px-3 py-2.5 text-xs font-bold transition-all hover:shadow-md border border-warning/40 uppercase tracking-wide"
          >
            Reset Database
          </button>
        )}
      </div>
    </aside>
  );
}
