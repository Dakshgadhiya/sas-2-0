import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { setToken, apiFetch } from "../services/api";
import { DEPARTMENT } from "../constants/subjects";

async function safeParseJson(res) {
  const text = await res.text();
  try {
    return { ok: res.ok, status: res.status, data: JSON.parse(text) };
  } catch {
    return { ok: res.ok, status: res.status, data: { error: text || "Invalid server response" } };
  }
}

export default function StudentSignup() {
  const [form, setForm] = useState({
    name: "",
    enrollment_number: "",
    email: "",
    password: "",
    semester: "1",
    department: DEPARTMENT
  });
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");

    setIsSubmitting(true);
    try {
      const res = await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ ...form, role: "student" })
      });
      const reg = await safeParseJson(res);
      if (!reg.ok) {
        setMessage(reg.data.error || "Registration failed.");
        setIsSubmitting(false);
        return;
      }

      setToken(reg.data.token);
      setMessage("Student registration completed successfully.");
      setForm({ name: "", enrollment_number: "", email: "", password: "", semester: "1", department: DEPARTMENT });
      
      // Redirect to student dashboard after successful registration
      setTimeout(() => {
        navigate("/student/dashboard");
      }, 1000);
    } catch (err) {
      console.error(err);
      setMessage("Cannot reach backend. Please check your internet connection.");
    }
    setIsSubmitting(false);
  }

  return (
    <div className="min-h-screen bg-white dark:bg-[#001845] flex items-center justify-center p-8">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-8">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa] uppercase tracking-wide">Student Signup</h1>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          {[
            ["name", "Full Name"],
            ["enrollment_number", "Enrollment Number"],
            ["email", "Email"],
            ["password", "Password"]
          ].map(([key, label]) => (
            <input
              key={key}
              type={key === "password" ? "password" : "text"}
              placeholder={label}
              className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          ))}
          
          <div>
            <label className="block text-sm font-bold text-[#0466c8] dark:text-[#60a5fa] mb-2 uppercase tracking-wide">Semester</label>
            <select
              className="w-full rounded-lg bg-white dark:bg-[#001233] border border-slate-300 dark:border-[#33415c] px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0466c8] transition-all"
              value={form.semester}
              onChange={(e) => setForm({ ...form, semester: e.target.value })}
            >
              <option value="1">Semester 1</option>
              <option value="2">Semester 2</option>
              <option value="3">Semester 3</option>
              <option value="4">Semester 4</option>
              <option value="5">Semester 5</option>
              <option value="6">Semester 6</option>
            </select>
          </div>

          <button
            className="w-full rounded-lg bg-gradient-to-r from-[#0466c8] to-[#0353a4] hover:from-[#034ba6] hover:to-[#023582] text-white font-bold py-3 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-md hover:shadow-lg uppercase tracking-wide"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Submitting..." : "Create Account"}
          </button>
        </form>
        <div className="flex items-center justify-between mt-4 text-sm text-neutral dark:text-slate-400">
          <button
            type="button"
            className="text-[#0466c8] dark:text-[#60a5fa] underline hover:text-[#034ba6] dark:hover:text-[#93c5fd]"
            onClick={() => navigate(-1)}
          >
            Back
          </button>
          <Link className="text-[#0466c8] dark:text-[#60a5fa] underline hover:text-[#034ba6] dark:hover:text-[#93c5fd]" to="/student/login">Already have an account? Login</Link>
        </div>
        {message && <div className={`text-sm mt-4 p-3 rounded-lg ${message.includes("successfully") ? "bg-success/10 text-success dark:text-green-300" : "bg-error/10 text-error dark:text-red-300"}`}>{message}</div>}
      </div>
    </div>
  );
}
