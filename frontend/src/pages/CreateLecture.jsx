import React, { useState, useEffect } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";
import { SEMESTER_SUBJECTS } from "../constants/subjects";

export default function CreateLecture() {
  const defaultForm = {
    lecture_title: "",
    subject: "",
    semester: "1",
    date: "",
    start_time: "",
    end_time: "",
    latitude: "",
    longitude: "",
    radius: ""
  };
  const [form, setForm] = useState(defaultForm);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState("");
  const [teachingAssignments, setTeachingAssignments] = useState([]);
  const [loadingAssignments, setLoadingAssignments] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const { showSuccess, showError, showInfo, showWarning } = useNotification();

  useEffect(() => {
    // Fetch faculty's teaching assignments on mount
    async function loadAssignments() {
      const res = await apiFetch("/api/faculty/profile");
      if (res.ok) {
        const data = await res.json();
        const assignments = data.profile?.subjects || [];
        setTeachingAssignments(assignments);
        
        // Set initial semester and subject from first assignment
        if (assignments.length > 0) {
          setForm(prev => ({
            ...prev,
            semester: assignments[0].semester,
            subject: assignments[0].subject
          }));
        }
      }
      setLoadingAssignments(false);
    }
    
    loadAssignments();
    // Auto-fetch location on component mount
    fetchLocation();
  }, []);

  function fetchLocation() {
    setLocationLoading(true);
    setLocationError("");
    
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setForm(prev => ({
            ...prev,
            latitude: latitude.toFixed(5),
            longitude: longitude.toFixed(5),
            radius: "50"  // Default 50 meters
          }));
          showSuccess("Location fetched successfully");
          setLocationLoading(false);
        },
        (error) => {
          setLocationError(`Location error: ${error.message}`);
          showError(`Location error: ${error.message}`);
          setLocationLoading(false);
        }
      );
    } else {
      const msg = "Geolocation not supported by this browser";
      setLocationError(msg);
      showError(msg);
      setLocationLoading(false);
    }
  }

  // Get unique semesters from teaching assignments
  function getTeachingSemesters() {
    const semesters = [...new Set(teachingAssignments.map(a => a.semester))];
    return semesters.sort();
  }

  // Get subjects for current semester from teaching assignments
  function getTeachingSubjectsForSemester(semester) {
    const subjects = teachingAssignments
      .filter(a => a.semester === semester)
      .map(a => a.subject);
    return [...new Set(subjects)]; // Remove duplicates
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    // Dynamic field validation
    const requiredFields = [
      { key: 'lecture_title', label: 'Title' },
      { key: 'subject', label: 'Subject' },
      { key: 'date', label: 'Date' },
      { key: 'start_time', label: 'Start Time' },
      { key: 'end_time', label: 'End Time' }
    ];
    
    const missingFields = requiredFields.filter(field => !form[field.key]);
    
    if (missingFields.length > 0) {
      if (missingFields.length === requiredFields.length) {
        // All fields missing
        showError("All fields (Title, Subject, Date, Start Time, End Time) are required");
      } else if (missingFields.length === 1) {
        // One field missing
        showError(`${missingFields[0].label} is required`);
      } else {
        // Multiple fields missing
        const fieldNames = missingFields.map(f => f.label).join(", ");
        showError(`(${fieldNames}) are required`);
      }
      return;
    }

    // Validate time format (accepts both HH:MM and HH:MM:SS)
    const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$/;
    if (!timeRegex.test(form.start_time)) {
      showError("Start time format is invalid. Please use HH:MM or HH:MM:SS format");
      return;
    }
    if (!timeRegex.test(form.end_time)) {
      showError("End time format is invalid. Please use HH:MM or HH:MM:SS format");
      return;
    }

    // Normalize time to HH:MM:SS format
    const normalizeTime = (timeStr) => {
      const parts = timeStr.split(":");
      if (parts.length === 2) {
        // HH:MM -> HH:MM:00
        return `${parts[0]}:${parts[1]}:00`;
      }
      // Already HH:MM:SS
      return timeStr;
    };

    // Compare times - end must be after start
    const [startHour, startMin, startSec] = form.start_time.split(":").map(Number);
    const [endHour, endMin, endSec] = form.end_time.split(":").map(Number);
    const startSeconds = startHour * 3600 + startMin * 60 + (startSec || 0);
    const endSeconds = endHour * 3600 + endMin * 60 + (endSec || 0);
    
    if (endSeconds <= startSeconds) {
      showError("End time must be after start time");
      return;
    }

    setSubmitLoading(true);
    try {
      // Use normalized time format for ISO string
      const normalizedStart = normalizeTime(form.start_time);
      const normalizedEnd = normalizeTime(form.end_time);
      
      // Convert user-entered IST date+time into UTC ISO strings
      const [y, m, d] = form.date.split("-").map(Number);
      const [sh, smin, ss] = normalizedStart.split(":").map(Number);
      const [eh, emin, es] = normalizedEnd.split(":").map(Number);

      // IST offset is +05:30 -> 5.5 hours in milliseconds
      const IST_OFFSET_MS = (5 * 60 + 30) * 60 * 1000;

      // Build UTC ms by interpreting the components as local IST and subtracting IST offset
      const startMs = Date.UTC(y, m - 1, d, sh, smin, ss) - IST_OFFSET_MS;
      const endMs = Date.UTC(y, m - 1, d, eh, emin, es) - IST_OFFSET_MS;

      const start = new Date(startMs).toISOString();
      const end = new Date(endMs).toISOString();
      
      const payload = {
        lecture_title: form.lecture_title,
        subject: form.subject,
        semester: form.semester,
        date: form.date,
        start_time: start,
        end_time: end
      };
      
      // Add location fields if provided
      if (form.latitude) payload.latitude = parseFloat(form.latitude);
      if (form.longitude) payload.longitude = parseFloat(form.longitude);
      if (form.radius) payload.radius = parseInt(form.radius, 10);
      
      const res = await apiFetch("/api/lectures/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      if (res.ok) {
        showSuccess("Lecture scheduled successfully");
        setForm(defaultForm);
        setTimeout(() => fetchLocation(), 500);
      } else {
        // Provide a clearer message when faculty is not authorized for the selected semester
        if (res.status === 403 && data.error && data.error.toLowerCase().includes('not authorized to teach semester')) {
          showError(`${data.error} Please add this semester to your teaching assignments in your profile before creating lectures.`);
        } else {
          showError(data.error || "Failed to create lecture. Try again");
        }
      }
    } catch (err) {
      console.error("Create lecture failed", err);
      showError(err.message || "Something went wrong. Please try again");
    } finally {
      setSubmitLoading(false);
    }
  }

  if (loadingAssignments) {
    return (
      <SidebarLayout role="faculty">
        <div className="p-6 bg-white dark:bg-[#002855] rounded-lg text-neutral dark:text-slate-400 text-center">Loading your teaching assignments...</div>
      </SidebarLayout>
    );
  }

  if (teachingAssignments.length === 0) {
    return (
      <SidebarLayout role="faculty">
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-6 text-slate-900 dark:text-white">
          <p className="font-bold mb-2 uppercase tracking-wide">No Teaching Assignments</p>
          <p className="text-sm">You have no teaching assignments. Please add subjects in your profile before creating lectures.</p>
        </div>
      </SidebarLayout>
    );
  }

  const teachingSemesters = getTeachingSemesters();
  const teachingSubjects = getTeachingSubjectsForSemester(form.semester);

  return (
    <SidebarLayout role="faculty">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Create Lecture Session</h1>
        <p className="text-neutral dark:text-slate-400 mb-8">Schedule a new lecture for your students</p>
        
        <form className="space-y-6 bg-white dark:bg-[#002855] rounded-lg border border-slate-200 dark:border-[#33415c] p-8 shadow-sm">
          {/* Lecture Title */}
          <div>
            <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Lecture Title</label>
            <input
              type="text"
              placeholder="e.g., Data Structures - Lecture 5"
              className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
              value={form.lecture_title}
              onChange={(e) => setForm({ ...form, lecture_title: e.target.value })}
              disabled={submitLoading}
            />
          </div>

          {/* Semester & Subject */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Semester</label>
              <select
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={form.semester}
                onChange={(e) => {
                  const subjects = getTeachingSubjectsForSemester(e.target.value);
                  setForm({ ...form, semester: e.target.value, subject: subjects[0] || "" });
                }}
                disabled={submitLoading}
              >
                {teachingSemesters.map(sem => (
                  <option key={sem} value={sem}>Semester {sem}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Subject</label>
              <select
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                disabled={submitLoading}
              >
                {teachingSubjects.map(subj => (
                  <option key={subj} value={subj}>{subj}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Date</label>
              <input
                type="date"
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                disabled={submitLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Start Time</label>
              <input
                type="time"
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                disabled={submitLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">End Time</label>
              <input
                type="time"
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                disabled={submitLoading}
              />
            </div>
          </div>

          {/* Location Section */}
          <div className="p-6 bg-slate-100 dark:bg-[#001845] border border-slate-200 dark:border-[#33415c] rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center uppercase tracking-wide">
                Location Details (GPS Verified)
              </h3>
              <button
                type="button"
                onClick={fetchLocation}
                disabled={locationLoading || submitLoading}
                className="text-xs px-3 py-2 bg-[#0466c8] hover:bg-[#034ba6] text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-bold uppercase tracking-wide"
              >
                {locationLoading ? "Fetching..." : "Refresh Location"}
              </button>
            </div>

            {locationError && (
              <div className="text-xs text-error dark:text-red-300 bg-error/10 dark:bg-error/20 border border-error/30 rounded-lg p-3 mb-4">
                {locationError}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-900 dark:text-white mb-2 uppercase tracking-wide">Latitude</label>
                <input
                  type="number"
                  step="0.00001"
                  className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] cursor-not-allowed"
                  value={form.latitude}
                  readOnly
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-900 dark:text-white mb-2 uppercase tracking-wide">Longitude</label>
                <input
                  type="number"
                  step="0.00001"
                  className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] cursor-not-allowed"
                  value={form.longitude}
                  readOnly
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-900 dark:text-white mb-2 uppercase tracking-wide">Radius (meters)</label>
                <input
                  type="number"
                  placeholder="50"
                  className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-3 py-2 text-sm text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
                  value={form.radius}
                  onChange={(e) => setForm({ ...form, radius: e.target.value })}
                  disabled={submitLoading}
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <button 
              type="submit"
              onClick={handleSubmit}
              disabled={submitLoading}
              className="flex-1 rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white font-bold py-3 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-md hover:shadow-lg uppercase tracking-wide"
            >
              {submitLoading ? "Creating..." : "Create Lecture Session"}
            </button>
          </div>
        </form>
      </div>
    </SidebarLayout>
  );
}
