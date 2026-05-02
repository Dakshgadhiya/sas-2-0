import React, { useEffect, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import { apiFetch } from "../services/api";

export default function StudentFacultyList() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadFaculty() {
      setLoading(true);
      const res = await apiFetch("/api/faculty/list");
      if (res.ok) {
        const data = await res.json();
        setFaculty(data.faculty || []);
      }
      setLoading(false);
    }
    loadFaculty();
  }, []);

  return (
    <SidebarLayout role="student">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Faculty Members</h1>
          <p className="text-neutral dark:text-slate-400">View all faculty members and their details.</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-neutral dark:text-slate-400">Loading faculty details...</div>
      ) : faculty.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] p-8 text-center text-neutral dark:text-slate-400">
          No faculty members found.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {faculty.map((member) => (
            <div
              key={member.id}
              className="rounded-2xl border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-bold text-[#0466c8] dark:text-[#60a5fa] text-lg uppercase tracking-wide">{member.name}</h3>
                  <p className="text-neutral dark:text-slate-400 text-sm">{member.email}</p>
                </div>
              </div>
              
              {member.department && (
                <div className="mb-3 pb-3 border-b border-slate-200 dark:border-[#33415c]">
                  <span className="text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Department</span>
                  <p className="text-slate-900 dark:text-white font-medium">{member.department}</p>
                </div>
              )}
              
              {member.teaching_assignments && member.teaching_assignments.length > 0 && (
                <div>
                  <span className="text-xs font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Teaching</span>
                  <div className="mt-2 space-y-2">
                    {member.teaching_assignments.map((assign, idx) => (
                      <div key={idx} className="flex items-start gap-2 bg-slate-50 dark:bg-[#001845] rounded-lg p-2">
                        <div className="text-xs font-bold text-white bg-[#0466c8] dark:bg-[#0353a4] px-2 py-1 rounded">
                          Sem {assign.semester}
                        </div>
                        <p className="text-sm text-slate-900 dark:text-white flex-1">{assign.subject}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </SidebarLayout>
  );
}
