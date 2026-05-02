import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";

// Format time in IST (12-hour format with AM/PM)
function formatTimeIST(timestamp) {
  if (!timestamp) return "N/A";
  const date = new Date(timestamp);
  return date.toLocaleString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
    timeZone: "Asia/Kolkata"
  });
}

export default function AttendanceHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showError, showInfo } = useNotification();

  useEffect(() => {
    async function load() {
      try {
        const res = await apiFetch("/api/attendance/history");
        if (res.ok) {
          const data = await res.json();
          if (!data.history || data.history.length === 0) {
            showInfo("No attendance data available");
          }
          setHistory(data.history || []);
        } else {
          showError("Failed to load attendance history");
        }
      } catch (err) {
        showError("Something went wrong. Please try again");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const getStatusColor = (status) => {
    switch(status) {
      case 'present':
        return 'bg-green-50 text-green-700 border border-green-200';
      case 'late':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      default:
        return 'bg-red-50 text-red-700 border border-red-200';
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'present':
        return '✅';
      case 'late':
        return '⏰';
      default:
        return '❌';
    }
  };

  return (
    <SidebarLayout role="student">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Attendance History</h1>
        <p className="text-neutral dark:text-slate-400 mt-2">View your lecture attendance records</p>
      </div>

      {loading ? (
        <div className="p-8 text-center bg-info/10 dark:bg-info/20 rounded-lg text-info dark:text-[#60a5fa]">
          <p className="text-sm">Loading attendance records...</p>
        </div>
      ) : history.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 dark:border-[#33415c] bg-slate-50 dark:bg-[#001845] p-12 text-center">
          <p className="text-slate-600 dark:text-slate-300 font-bold text-lg">No Attendance Records</p>
          <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">Your attendance records will appear here once you attend lectures.</p>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-[#33415c]">
              <thead className="bg-slate-50 dark:bg-[#001845]">
                <tr>
                  <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Subject</th>
                  <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Lecture</th>
                  <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Faculty</th>
                  <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Status</th>
                  <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Join Time (IST)</th>
                  <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Exit Time (IST)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-[#33415c]">
                {history.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-[#001845] transition-colors">
                    <td className="px-6 py-4 text-sm text-slate-900 dark:text-white font-bold">{row.lecture_subject || "N/A"}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{row.lecture_title}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{row.faculty_name || "Unknown"}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${
                        row.status === "present" ? "bg-success/20 text-success dark:text-green-300" :
                        row.status === "late" ? "bg-warning/20 text-warning dark:text-yellow-300" :
                        "bg-error/20 text-error dark:text-red-300"
                      }`}>
                        {row.status === "present" ? "Present" : row.status === "late" ? "Late" : "Absent"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{formatTimeIST(row.joining_time || row.timestamp)}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                      {(row.status === "present" || row.status === "late") ? formatTimeIST(row.end_time_actual) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Summary */}
          <div className="border-t border-slate-200 dark:border-[#33415c] bg-slate-50 dark:bg-[#001845] px-6 py-4 flex gap-6 text-sm flex-wrap">
            <div>
              <span className="text-slate-600 dark:text-slate-400">Total Lectures:</span>
              <span className="ml-2 font-bold text-slate-900 dark:text-white">{history.length}</span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Present:</span>
              <span className="ml-2 font-bold text-success dark:text-green-300">
                {history.filter(h => h.status === 'present').length}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Late:</span>
              <span className="ml-2 font-bold text-warning dark:text-yellow-300">
                {history.filter(h => h.status === 'late').length}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Absent:</span>
              <span className="ml-2 font-bold text-error dark:text-red-300">
                {history.filter(h => h.status === 'absent').length}
              </span>
            </div>
          </div>
        </div>
      )}
    </SidebarLayout>
  );
}
