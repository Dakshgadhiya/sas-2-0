import React, { useEffect, useState, useMemo } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
import { SEMESTER_SUBJECTS } from "../constants/subjects";
import { formatTimeIST } from "../utils/time";

function formatDateDDMMYYYY(dateStr) {
  if (!dateStr) return "N/A";
  try {
    const [year, month, day] = dateStr.split("-");
    return `${day}-${month}-${year}`;
  } catch (e) {
    return dateStr;
  }
}

export default function AttendanceReports() {
  const [sessions, setSessions] = useState([]);
  const [selectedSemester, setSelectedSemester] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [report, setReport] = useState([]);
  const [exportMessage, setExportMessage] = useState("");
  const [teachingSemesters, setTeachingSemesters] = useState([]);
  const [teachingAssignments, setTeachingAssignments] = useState([]);

  useEffect(() => {
    async function load() {
      // Fetch faculty profile to get teaching assignments
      const profile = await apiFetch("/api/faculty/profile");
      if (profile.ok) {
        const data = await profile.json();
        const subjects = data.profile?.subjects || [];
        const semesters = [...new Set(subjects.map(s => s.semester))].sort();
        setTeachingSemesters(semesters);
        setTeachingAssignments(subjects);
      }

      const res = await apiFetch("/api/lectures/sessions");
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    }
    load();
  }, []);

  // Get subjects for selected semester (only faculty's assigned subjects)
  const subjectsForSemester = useMemo(() => {
    if (!selectedSemester) return [];
    return teachingAssignments
      .filter(a => a.semester === selectedSemester)
      .map(a => a.subject);
  }, [selectedSemester, teachingAssignments]);

  // Get sessions for selected semester and subject
  const sessionsForSelection = useMemo(() => {
    return sessions.filter(s => {
      if (selectedSemester && s.semester !== selectedSemester) return false;
      if (selectedSubject && s.lecture_subject !== selectedSubject) return false;
      return true;
    });
  }, [sessions, selectedSemester, selectedSubject]);

  async function loadReport(id) {
    if (!id) return;
    const res = await apiFetch(`/api/attendance/report/${id}`);
    if (res.ok) {
      const data = await res.json();
      setReport(data.report || []);
    }
  }

  function csvEscape(value) {
    if (value === null || value === undefined) return "";
    const str = String(value);
    if (/[",\n]/.test(str)) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  }

  function exportCsv() {
    if (!sessionId || report.length === 0) {
      setExportMessage("Select a session with data to export.");
      return;
    }
    setExportMessage("");
    const selected = sessions.find((s) => String(s.id) === String(sessionId));
    const header = [
      "No.",
      "Enrollment No.",
      "Student Name",
      "Status",
      "Join Time",
      "Exit Time",
      "Duration (mins)"
    ];
    const rows = report.map((row, index) => ([
      index + 1,
      row.roll_number || "",
      row.student_name,
      row.status ? row.status.charAt(0).toUpperCase() + row.status.slice(1) : "-",
      formatTimeIST(row.join_time),
      formatTimeIST(row.exit_time),
      row.duration_minutes || "-"
    ]));
    const csv = [header, ...rows]
      .map((line) => line.map(csvEscape).join(","))
      .join("\n");

    const safeTitle = (selected?.lecture_title || "session")
      .replace(/[^a-z0-9-_]+/gi, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
    const filename = `attendance_report_${safeTitle || "session"}_${sessionId}.csv`;

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  return (
    <SidebarLayout role="faculty">
      <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Attendance Reports</h1>
      <p className="text-neutral dark:text-slate-400 mt-2">Select semester, subject, and session to view attendance details</p>
      
      {/* Step-by-Step Selection */}
      <div className="mt-6 space-y-4 max-w-2xl">
        {/* Step 1: Semester Selection */}
        <div>
          <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Step 1: Select Semester</label>
          <select
            className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
            value={selectedSemester}
            onChange={(e) => {
              setSelectedSemester(e.target.value);
              setSelectedSubject("");
              setSessionId("");
              setReport([]);
            }}
          >
            <option value="">Choose a semester...</option>
            {teachingSemesters.map(sem => (
              <option key={sem} value={sem}>Semester {sem}</option>
            ))}
          </select>
        </div>

        {/* Step 2: Subject Selection */}
        {selectedSemester && (
          <div>
            <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Step 2: Select Subject</label>
            <select
              className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
              value={selectedSubject}
              onChange={(e) => {
                setSelectedSubject(e.target.value);
                setSessionId("");
                setReport([]);
              }}
            >
              <option value="">Choose a subject...</option>
              {subjectsForSemester.map(subj => (
                <option key={subj} value={subj}>{subj}</option>
              ))}
            </select>
          </div>
        )}

        {/* Step 3: Session Selection */}
        {selectedSemester && selectedSubject && (
          <div>
            <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Step 3: Select Session</label>
            <select
              className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
              value={sessionId}
              onChange={(e) => {
                setSessionId(e.target.value);
                loadReport(e.target.value);
              }}
            >
              <option value="">Choose a session...</option>
              {sessionsForSelection.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.lecture_title} - {formatDateDDMMYYYY(s.lecture_date)}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Export Button */}
        {selectedSemester && selectedSubject && sessionId && (
          <button
            className="w-full rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white px-4 py-3 font-bold disabled:opacity-60 transition-all uppercase tracking-wide shadow-md hover:shadow-lg"
            onClick={exportCsv}
            disabled={report.length === 0}
          >
            Export CSV
          </button>
        )}
        {exportMessage && <div className="text-sm text-neutral dark:text-slate-400">{exportMessage}</div>}
      </div>

      {/* Report Table */}
      {report.length > 0 && (
        <div className="mt-8 overflow-x-auto rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-[#33415c]">
            <thead className="bg-slate-50 dark:bg-[#001845]">
              <tr>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">No.</th>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">Enrollment No.</th>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">Student</th>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">Status</th>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">Join Time (IST)</th>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">Exit Time (IST)</th>
                <th className="text-left text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] px-4 py-3 uppercase tracking-wide">Duration (mins)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-[#33415c]">
              {report.map((row, index) => (
                <tr key={`${sessionId}-${row.student_id}`} className="hover:bg-slate-50 dark:hover:bg-[#001845] transition-colors">
                  <td className="px-4 py-3 text-sm text-slate-900 dark:text-white font-bold">{index + 1}</td>
                  <td className="px-4 py-3 text-sm text-slate-900 dark:text-white font-bold">{row.roll_number || "-"}</td>
                  <td className="px-4 py-3 text-sm text-slate-900 dark:text-white">{row.student_name}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      row.status === "present" ? "bg-success/20 text-success dark:text-green-300" :
                      row.status === "late" ? "bg-warning/20 text-warning dark:text-yellow-300" :
                      "bg-error/20 text-error dark:text-red-300"
                    }`}>
                      {row.status ? row.status.charAt(0).toUpperCase() + row.status.slice(1) : "-"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral dark:text-slate-400">
                    {formatTimeIST(row.join_time)}
                  </td>
                  <td className="px-4 py-3 text-sm text-neutral dark:text-slate-400">
                    {formatTimeIST(row.exit_time)}
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-slate-900 dark:text-white">
                    {row.duration_minutes !== null && row.duration_minutes !== undefined ? `${row.duration_minutes} min` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SidebarLayout>
  );
}
