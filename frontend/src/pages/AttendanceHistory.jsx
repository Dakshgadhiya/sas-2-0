import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";
import { formatTimeIST, normalizeTimestamp } from "../utils/time";

function formatDateDDMMYYYY(dateStr) {
  if (!dateStr) return "N/A";
  try {
    const [year, month, day] = dateStr.split("-");
    return `${day}-${month}-${year}`;
  } catch (e) {
    return dateStr;
  }
}

function formatDateTime(dateStr, timeStr) {
  if (!dateStr || !timeStr) return "N/A";
  try {
    const [year, month, day] = dateStr.split("-");
    const [hours, minutes] = timeStr.split(":");
    const date = new Date(year, month - 1, day, hours, minutes);
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  } catch (e) {
    return `${formatDateDDMMYYYY(dateStr)} ${timeStr}`;
  }
}

function calculateDuration(joinTime, exitTime) {
  if (!joinTime || !exitTime) return "N/A";
  try {
    const join = new Date(`2000-01-01T${joinTime}`);
    const exit = new Date(`2000-01-01T${exitTime}`);
    const diffMs = exit - join;
    const diffMins = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  } catch (e) {
    return "N/A";
  }
}

export default function AttendanceHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubject, setSelectedSubject] = useState("all");
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

  // Extract unique subjects for filtering
  const uniqueSubjects = [...new Set(history.map(h => h.lecture_subject).filter(Boolean))].sort();

  const getLectureEndMs = (row) => {
    try {
      const date = row.lecture_date;
      const time = row.end_time_actual || row.end_time;
      if (!date || !time) return null;

      const normalized = normalizeTimestamp(`${date}T${time}`);
      const ms = Date.parse(normalized);
      return Number.isNaN(ms) ? null : ms;
    } catch (e) {
      return null;
    }
  };

  // Filter history based on selected subject and only include completed lectures
  const completedHistory = history.filter(h => {
    const ms = getLectureEndMs(h);
    return ms !== null && ms < Date.now();
  });

  const filteredHistory = selectedSubject === "all"
    ? completedHistory
    : completedHistory.filter(h => h.lecture_subject === selectedSubject);

  // Calculate per-subject statistics
  const calculateStats = (data) => {
    const total = data.length;
    const present = data.filter(h => h.status === 'present').length;
    const late = data.filter(h => h.status === 'late').length;
    const absent = data.filter(h => h.status === 'absent').length;
    const attended = present + late;
    const percentage = total > 0 ? Math.round((attended / total) * 100) : 0;
    return { total, present, late, absent, attended, percentage };
  };

  const stats = calculateStats(filteredHistory);
  const overallStats = calculateStats(history);

  const getAttendanceColor = (percentage) => {
    if (percentage >= 75) return 'text-green-600 dark:text-green-400';
    if (percentage >= 50) return 'text-yellow-600 dark:text-yellow-400';
    if (percentage >= 25) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getAttendanceStatus = (percentage) => {
    if (percentage >= 75) return 'Good';
    if (percentage >= 50) return 'Warning';
    if (percentage >= 25) return 'Low';
    return 'Critical';
  };

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

      {/* Subject Filter */}
      {uniqueSubjects.length > 0 && (
        <div className="mb-6 flex items-center gap-4">
          <label className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wide">
            Filter by Subject:
          </label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="px-4 py-2 rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001845] text-slate-900 dark:text-white font-medium focus:outline-none focus:ring-2 focus:ring-[#0466c8]"
          >
            <option value="all">All Subjects ({history.length})</option>
            {uniqueSubjects.map(subject => (
              <option key={subject} value={subject}>
                {subject} ({history.filter(h => h.lecture_subject === subject).length})
              </option>
            ))}
          </select>
        </div>
      )}

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
        <div className="space-y-6">
          {/* Per-Subject Statistics */}
          {selectedSubject !== "all" && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-4">
                <p className="text-xs text-slate-600 dark:text-slate-400 uppercase font-bold tracking-wide">Total Lectures</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stats.total}</p>
              </div>
              <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-4">
                <p className="text-xs text-slate-600 dark:text-slate-400 uppercase font-bold tracking-wide">Attended</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">{stats.attended}</p>
              </div>
              <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-4">
                <p className="text-xs text-slate-600 dark:text-slate-400 uppercase font-bold tracking-wide">Absent</p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{stats.absent}</p>
              </div>
              <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-4">
                <p className="text-xs text-slate-600 dark:text-slate-400 uppercase font-bold tracking-wide">Attendance %</p>
                <p className={`text-2xl font-bold mt-1 ${getAttendanceColor(stats.percentage)}`}>{stats.percentage}%</p>
              </div>
            </div>
          )}

          <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 dark:divide-[#33415c]">
                <thead className="bg-slate-50 dark:bg-[#001845]">
                  <tr>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Date & Time</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Subject</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Lecture</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Faculty</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Status</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Join Time</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Exit Time</th>
                    <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-6 py-4 uppercase tracking-wide">Duration</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-[#33415c]">
                  {filteredHistory.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-[#001845] transition-colors">
                    <td className="px-6 py-4 text-sm">
                      <div className="text-slate-900 dark:text-white font-bold">{formatDateDDMMYYYY(row.lecture_date)}</div>
                      <div className="text-slate-600 dark:text-slate-300 text-xs">
                        {formatTimeIST(row.start_time)} - {formatTimeIST(row.end_time)}
                      </div>
                    </td>
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
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300 font-mono">
                      {(row.status === "present" || row.status === "late") ? formatTimeIST(row.joining_time || row.timestamp) : "—"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300 font-mono">
                      {(row.status === "present" || row.status === "late") ? formatTimeIST(row.end_time_actual) : "—"}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300 font-mono">
                      {(row.status === "present" || row.status === "late") ? 
                        calculateDuration(row.joining_time || row.timestamp, row.end_time_actual) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
              </table>
            </div>
          </div>
          
          {/* Summary */}
          <div className="border-t border-slate-200 dark:border-[#33415c] bg-slate-50 dark:bg-[#001845] px-6 py-4 flex gap-6 text-sm flex-wrap">
            <div>
              <span className="text-slate-600 dark:text-slate-400">Total Lectures:</span>
              <span className="ml-2 font-bold text-slate-900 dark:text-white">{stats.total}</span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Present:</span>
              <span className="ml-2 font-bold text-success dark:text-green-300">
                {stats.present}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Late:</span>
              <span className="ml-2 font-bold text-warning dark:text-yellow-300">
                {stats.late}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Absent:</span>
              <span className="ml-2 font-bold text-error dark:text-red-300">
                {stats.absent}
              </span>
            </div>
            {selectedSubject !== "all" && (
              <div>
                <span className="text-slate-600 dark:text-slate-400">Attendance %:</span>
                <span className={`ml-2 font-bold ${getAttendanceColor(stats.percentage)}`}>
                  {stats.percentage}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </SidebarLayout>
  );
}
