import React, { useState } from "react";
import { setToken, apiFetch } from "../services/api";
import { Link, useNavigate } from "react-router-dom";
import { useNotification } from "../hooks/useNotification";

export default function FacultyLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { showSuccess, showError } = useNotification();

  async function handleLogin(e) {
    e.preventDefault();
    
    if (!email || !password) {
      showError("Invalid input. Please check your details");
      return;
    }

    setLoading(true);
    try {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      
      if (res.ok) {
        setToken(data.token);
        showSuccess("Login successful!");
        setTimeout(() => navigate("/faculty/dashboard"), 500);
      } else {
        if (data.error?.includes("Email already")) {
          showError("Email already registered. Please login");
        } else {
          showError(data.error || "Login failed. Please try again");
        }
      }
    } catch (err) {
      showError("Something went wrong. Please try again");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f8fafc] via-[#f0f4f9] to-[#f8fafc] dark:from-[#001845] dark:via-[#002855] dark:to-[#001845] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#0466c8] to-[#0353a4] px-8 py-8">
            <h1 className="text-3xl font-bold text-white mb-2">Faculty Login</h1>
            <p className="text-slate-100">Manage your lectures and attendance</p>
          </div>

          {/* Form */}
          <form className="p-8 space-y-4" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Email Address</label>
              <input
                type="email"
                placeholder="your.email@example.com"
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Password</label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0466c8] focus:border-transparent transition-all"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] text-white font-semibold py-3 hover:from-[#034ba6] hover:to-[#023582] transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-md hover:shadow-lg mt-6"
            >
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>

          {/* Footer */}
          <div className="px-8 py-6 bg-slate-50 dark:bg-[#001845] border-t border-slate-200 dark:border-[#33415c]">
            <p className="text-sm text-slate-600 dark:text-slate-400 text-center">
              Don't have an account?{" "}
              <Link to="/faculty/signup" className="text-[#0466c8] dark:text-[#60a5fa] font-semibold hover:text-[#034ba6] dark:hover:text-[#93c5fd]">
                Sign up here
              </Link>
            </p>
          </div>

          {/* Navigation */}
          <div className="px-8 py-4 flex gap-3">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="flex-1 px-4 py-2 text-[#0466c8] dark:text-[#60a5fa] border border-slate-300 dark:border-[#33415c] rounded-lg hover:bg-slate-50 dark:hover:bg-[#002855] transition-colors text-sm font-medium"
            >
              Back
            </button>
            <Link 
              to="/"
              className="flex-1 px-4 py-2 text-center text-[#0466c8] dark:text-[#60a5fa] border border-slate-300 dark:border-[#33415c] rounded-lg hover:bg-slate-50 dark:hover:bg-[#002855] transition-colors text-sm font-medium"
            >
              Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
