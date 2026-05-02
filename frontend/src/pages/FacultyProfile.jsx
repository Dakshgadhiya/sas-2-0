import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
import { SEMESTER_SUBJECTS, DEPARTMENT } from "../constants/subjects";

export default function FacultyProfile() {
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    faculty_id: "",
    department: DEPARTMENT,
    subjects: []
  });
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadProfile() {
      const res = await apiFetch("/api/faculty/profile");
      if (res.ok) {
        const data = await res.json();
        setProfile({ ...data.profile, department: DEPARTMENT });
      }
      setLoading(false);
    }
    loadProfile();
  }, []);

  function addSubject() {
    setProfile({
      ...profile,
      subjects: [...profile.subjects, { semester: "1", subject: SEMESTER_SUBJECTS["1"][0] }]
    });
  }

  function removeSubject(index) {
    if (profile.subjects.length > 1) {
      setProfile({
        ...profile,
        subjects: profile.subjects.filter((_, i) => i !== index)
      });
    }
  }

  function updateSubject(index, field, value) {
    const updated = [...profile.subjects];
    updated[index][field] = value;
    // If semester changed, reset subject to first of new semester
    if (field === "semester") {
      updated[index].subject = SEMESTER_SUBJECTS[value][0];
    }
    setProfile({ ...profile, subjects: updated });
  }

  function getValidSemesters() {
    // Return all semesters (allow duplicates for same semester)
    return ["1", "2", "3", "4", "5", "6"];
  }

  function getSubjectsForSemester(semester) {
    return SEMESTER_SUBJECTS[semester] || [];
  }

  async function handleSave() {
    setMessage("");
    const res = await apiFetch("/api/faculty/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile)
    });

    if (res.ok) {
      setMessage("Profile updated successfully!");
      setEditMode(false);
      setTimeout(() => setMessage(""), 3000);
    } else {
      const data = await res.json();
      setMessage(`Error: ${data.error || "Failed to update profile"}`);
    }
  }

  if (loading) {
    return (
      <SidebarLayout role="faculty">
        <div className="text-neutral dark:text-slate-400">Loading profile...</div>
      </SidebarLayout>
    );
  }

  return (
    <SidebarLayout role="faculty">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] mb-6 uppercase tracking-wide">Faculty Profile</h1>

        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          {message && (
            <div className={`mb-4 p-3 rounded-lg text-sm ${
              message.includes("successfully") 
                ? "bg-success/10 text-success dark:text-green-300 border border-success/30" 
                : "bg-error/10 text-error dark:text-red-300 border border-error/30"
            }`}>
              {message}
            </div>
          )}

          <div className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Faculty ID
              </label>
              <div className="text-slate-900 dark:text-white">{profile.faculty_id || "N/A"}</div>
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Name
              </label>
              {editMode ? (
                <input
                  type="text"
                  className="w-full rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001233] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                />
              ) : (
                <div className="text-slate-900 dark:text-white">{profile.name || "N/A"}</div>
              )}
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Email
              </label>
              {editMode ? (
                <input
                  type="email"
                  className="w-full rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001233] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                />
              ) : (
                <div className="text-slate-900 dark:text-white">{profile.email || "N/A"}</div>
              )}
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Department
              </label>
              <div className="rounded-lg bg-slate-100 dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white font-medium">
                Information Technology
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Teaching Assignments
              </label>
              {editMode ? (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {profile.subjects.length > 0 ? (
                    profile.subjects.map((subj, idx) => (
                      <div key={idx} className="flex gap-2 items-center">
                        <select
                          className="flex-1 rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001233] px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] text-sm transition-all"
                          value={subj.semester}
                          onChange={(e) => updateSubject(idx, "semester", e.target.value)}
                        >
                          {getValidSemesters().map(sem => (
                            <option key={sem} value={sem}>Semester {sem}</option>
                          ))}
                        </select>
                        <select
                          className="flex-1 rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001233] px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] text-sm transition-all"
                          value={subj.subject}
                          onChange={(e) => updateSubject(idx, "subject", e.target.value)}
                        >
                          {getSubjectsForSemester(subj.semester).map(s => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                        {profile.subjects.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeSubject(idx)}
                            className="px-3 py-2 rounded-lg bg-slate-200 dark:bg-[#33415c] text-slate-900 dark:text-white hover:bg-slate-300 dark:hover:bg-[#4a5270] transition-colors border border-slate-300 dark:border-[#33415c] font-bold"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-neutral dark:text-slate-400 text-sm">No teaching assignments</div>
                  )}
                  <button
                    type="button"
                    onClick={addSubject}
                    className="w-full py-2 px-3 rounded-lg border border-dashed border-slate-300 dark:border-[#33415c] text-slate-900 dark:text-white hover:bg-slate-100 dark:hover:bg-[#001233] transition-colors text-sm font-bold uppercase tracking-wide"
                  >
                    + Add Another Semester
                  </button>
                </div>
              ) : (
                <div className="text-slate-900 dark:text-white">
                  {profile.subjects && profile.subjects.length > 0
                    ? profile.subjects.map((s, i) => (
                        <div key={i}>
                          Semester {s.semester}: {s.subject}
                        </div>
                      ))
                    : "N/A"}
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-4">
              {editMode ? (
                <>
                  <button
                    onClick={handleSave}
                    className="rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white px-6 py-2 font-bold transition-all uppercase tracking-wide"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => setEditMode(false)}
                    className="rounded-lg bg-slate-200 dark:bg-[#33415c] text-slate-900 dark:text-white px-6 py-2 font-bold hover:bg-slate-300 dark:hover:bg-[#4a5270] transition-colors uppercase tracking-wide"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditMode(true)}
                  className="rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white px-6 py-2 font-bold transition-all uppercase tracking-wide"
                >
                  Change Details
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
