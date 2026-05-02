import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";
import { DEPARTMENT } from "../constants/subjects";

export default function StudentProfile() {
  const [profile, setProfile] = useState({
    name: "",
    email: "",
    roll_number: "",
    department: DEPARTMENT,
    semester: ""
  });
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadProfile() {
      const res = await apiFetch("/api/student/profile");
      if (res.ok) {
        const data = await res.json();
        setProfile({ ...data.profile, department: DEPARTMENT });
      }
      setLoading(false);
    }
    loadProfile();
  }, []);

  async function handleSave() {
    setMessage("");
    // Only send name and email for updating (locked fields are not sent)
    const res = await apiFetch("/api/student/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: profile.name,
        email: profile.email
      })
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
      <SidebarLayout role="student">
        <div className="text-neutral dark:text-slate-400">Loading profile...</div>
      </SidebarLayout>
    );
  }

  return (
    <SidebarLayout role="student">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-[#0466c8] dark:text-[#60a5fa] mb-6 uppercase tracking-wide">Student Profile</h1>

        <div className="rounded-2xl border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          {message && (
            <div className={`mb-4 p-3 rounded-lg text-sm ${
              message.includes("successfully")
                ? "bg-success/10 dark:bg-success/20 text-success dark:text-success border border-success/30" 
                : "bg-error/10 dark:bg-error/20 text-error dark:text-error border border-error/30"
            }`}>
              {message}
            </div>
          )}

          <div className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Enrollment Number
              </label>
              <div className="text-neutral dark:text-slate-400 text-sm italic">
                {profile.roll_number || "N/A"}
                <span className="ml-2 text-slate-400 dark:text-slate-500">(Locked)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Name
              </label>
              {editMode ? (
                <input
                  type="text"
                  className="w-full rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001233] px-4 py-2 text-slate-900 dark:text-white focus:ring-2 focus:ring-[#0466c8]"
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
                  className="w-full rounded-lg border border-slate-300 dark:border-[#33415c] bg-white dark:bg-[#001233] px-4 py-2 text-slate-900 dark:text-white focus:ring-2 focus:ring-[#0466c8]"
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
              <div className="text-slate-900 dark:text-white font-medium bg-slate-100 dark:bg-[#33415c] px-3 py-2 rounded-lg border border-slate-300 dark:border-[#33415c]">
                {DEPARTMENT}
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">
                Semester
              </label>
              <div className="text-neutral dark:text-slate-400 text-sm italic">
                {profile.semester ? `Semester ${profile.semester}` : "N/A"}
                <span className="ml-2 text-slate-400 dark:text-slate-500">(Locked)</span>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              {editMode ? (
                <>
                  <button
                    onClick={handleSave}
                    className="rounded-lg bg-[#0466c8] hover:bg-[#034ba6] text-white px-6 py-2 font-bold transition-colors uppercase tracking-wide"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={() => setEditMode(false)}
                    className="rounded-lg bg-slate-200 dark:bg-[#33415c] text-slate-900 dark:text-white px-6 py-2 font-bold transition-colors uppercase tracking-wide hover:bg-slate-300 dark:hover:bg-[#445566]"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditMode(true)}
                  className="rounded-lg bg-[#0466c8] hover:bg-[#034ba6] text-white px-6 py-2 font-bold transition-colors uppercase tracking-wide"
                >
                  Edit Profile
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
