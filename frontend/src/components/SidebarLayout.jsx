import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "./Sidebar";
import { apiFetch } from "../services/api";

export default function SidebarLayout({ children, role = "student" }) {
  const [authorized, setAuthorized] = useState(false);
  const [checkingAccess, setCheckingAccess] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function checkRole() {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate(`/${role}/login`);
        return;
      }

      try {
        const res = await apiFetch("/api/auth/me");
        if (!res.ok) {
          if (res.status === 401 || res.status === 403) {
            navigate(`/${role}/login`);
          }
          return;
        }

        const data = await res.json();
        const userRole = (data.user?.role || "").toLowerCase();
        if (userRole !== role) {
          navigate(`/${role}/login`);
          return;
        }

        setAuthorized(true);
      } catch (error) {
        console.error("Auth verification failed:", error);
        navigate(`/${role}/login`);
      } finally {
        setCheckingAccess(false);
      }
    }
    checkRole();
  }, [role, navigate]);

  if (!authorized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-500 mb-2">
            {checkingAccess ? "🔄 Checking access..." : "⏳ Waiting for login..."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex">
      <Sidebar role={role} />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
