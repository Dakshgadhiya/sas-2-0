import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import { NotificationProvider } from "./context/NotificationContext";
import Toast from "./components/Toast";
import StudentSignup from "./pages/StudentSignup";
import StudentLogin from "./pages/StudentLogin";
import StudentDashboard from "./pages/StudentDashboard";
import StudentProfile from "./pages/StudentProfile";
import StudentFacultyList from "./pages/StudentFacultyList";
import StudentLectures from "./pages/StudentLectures";
import JoinLecture from "./pages/JoinLecture";
import AttendanceHistory from "./pages/AttendanceHistory";
import FacultyLogin from "./pages/FacultyLogin";
import FacultySignUp from "./pages/FacultySignUp";
import FacultyDashboard from "./pages/FacultyDashboard";
import FacultyProfile from "./pages/FacultyProfile";
import CreateLecture from "./pages/CreateLecture";
import AttendanceReports from "./pages/AttendanceReports";
import StudentList from "./pages/StudentList";
import MarkAttendance from "./pages/MarkAttendance";
import Lectures from "./pages/Notifications";

function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex flex-col items-center justify-center p-6">
      {/* Header Section */}
      <div className="w-full max-w-4xl text-center mb-16">
        <div className="inline-block mb-6 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
          🎓 Smart Attendance System
        </div>
        <h1 className="text-5xl md:text-6xl font-black text-slate-900 mb-4 leading-tight">
          AI Verified<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-blue-400">
            Lecture Participation
          </span>
        </h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
          Real-time attendance tracking with GPS verification for secure and efficient classroom management
        </p>
      </div>

      {/* Portal Cards Section */}
      <div className="w-full max-w-5xl">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-slate-800">Select Your Portal</h2>
          <p className="text-slate-600 mt-2">Choose your role to get started</p>
        </div>

        {/* Student & Faculty Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Student Portal */}
          <div className="rounded-3xl border border-blue-200 bg-white shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 h-32 flex items-center justify-center">
              <div className="text-6xl">👨‍🎓</div>
            </div>
            <div className="p-8">
              <h3 className="text-2xl font-bold text-slate-900 mb-2">Student Portal</h3>
              <p className="text-slate-600 text-sm mb-6">Track your attendance, join lectures, and view your participation records</p>
              <div className="grid grid-cols-2 gap-3">
                <Link 
                  to="/student/login"
                  className="px-6 py-3 bg-blue-500 text-white font-semibold rounded-xl hover:bg-blue-600 transition-colors text-center text-sm"
                >
                  Login
                </Link>
                <Link 
                  to="/student/signup"
                  className="px-6 py-3 bg-blue-50 text-blue-600 font-semibold rounded-xl hover:bg-blue-100 transition-colors text-center text-sm border border-blue-200"
                >
                  Sign Up
                </Link>
              </div>
            </div>
          </div>

          {/* Faculty Portal */}
          <div className="rounded-3xl border border-purple-200 bg-white shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300">
            <div className="bg-gradient-to-r from-purple-500 to-purple-600 h-32 flex items-center justify-center">
              <div className="text-6xl">👨‍🏫</div>
            </div>
            <div className="p-8">
              <h3 className="text-2xl font-bold text-slate-900 mb-2">Faculty Portal</h3>
              <p className="text-slate-600 text-sm mb-6">Create lectures, manage attendance, and generate detailed participation reports</p>
              <div className="grid grid-cols-2 gap-3">
                <Link 
                  to="/faculty/login"
                  className="px-6 py-3 bg-purple-500 text-white font-semibold rounded-xl hover:bg-purple-600 transition-colors text-center text-sm"
                >
                  Login
                </Link>
                <Link 
                  to="/faculty/signup"
                  className="px-6 py-3 bg-purple-50 text-purple-600 font-semibold rounded-xl hover:bg-purple-100 transition-colors text-center text-sm border border-purple-200"
                >
                  Sign Up
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📍</span>
            </div>
            <h4 className="font-semibold text-slate-800 mb-2">GPS Verified</h4>
            <p className="text-sm text-slate-600">Location-based attendance tracking</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h4 className="font-semibold text-slate-800 mb-2">AI Powered</h4>
            <p className="text-sm text-slate-600">Smart verification system</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h4 className="font-semibold text-slate-800 mb-2">Real-time Reports</h4>
            <p className="text-sm text-slate-600">Instant attendance insights</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-16 text-center text-slate-600 text-sm">
        <p>© 2026 AI Verified LMS. All rights reserved.</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <NotificationProvider>
      <Toast />
      <Routes>
        <Route path="/" element={<Home />} />
      <Route path="/student/signup" element={<StudentSignup />} />
      <Route path="/student/login" element={<StudentLogin />} />
      <Route path="/student/dashboard" element={<StudentDashboard />} />
      <Route path="/student/profile" element={<StudentProfile />} />
      <Route path="/student/faculty" element={<StudentFacultyList />} />
      <Route path="/student/lectures" element={<StudentLectures />} />
      <Route path="/student/attendance" element={<MarkAttendance />} />
      <Route path="/student/notifications" element={<Lectures role="student" />} />
      <Route path="/student/join" element={<JoinLecture />} />
      <Route path="/student/history" element={<AttendanceHistory />} />
      <Route path="/faculty/signup" element={<FacultySignUp />} />
      <Route path="/faculty/login" element={<FacultyLogin />} />
      <Route path="/faculty/dashboard" element={<FacultyDashboard />} />
      <Route path="/faculty/profile" element={<FacultyProfile />} />
      <Route path="/faculty/notifications" element={<Lectures role="faculty" />} />
      <Route path="/faculty/create-lecture" element={<CreateLecture />} />
      <Route path="/faculty/students" element={<StudentList />} />
      <Route path="/faculty/reports" element={<AttendanceReports />} />
      </Routes>
    </NotificationProvider>
  );
}
