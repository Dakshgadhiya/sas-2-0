import React, { useEffect, useMemo, useState } from "react";
import SidebarLayout from "../components/SidebarLayout";
import MetricCard from "../components/MetricCard";
import { apiFetch } from "../services/api";
import { useNotification } from "../hooks/useNotification";
import { getShortSubjectForm } from "../constants/subjects";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

export default function StudentDashboard() {
  const [stats, setStats] = useState({ total_lectures: 0, lectures_attended: 0, attendance_percentage: 0 });
  const [history, setHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [studentSemester, setStudentSemester] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showError, showInfo } = useNotification();

  async function loadAllData() {
    try {
      // Get student profile to know their semester
      const profile = await apiFetch("/api/student/profile");
      if (profile.ok) {
        const data = await profile.json();
        setStudentSemester(data.profile?.semester || "1");
      }
      
      const res = await apiFetch("/api/attendance/stats");
      if (res.ok) setStats(await res.json());
      
      const hist = await apiFetch("/api/attendance/history");
      if (hist.ok) {
        const data = await hist.json();
        if (!data.history || data.history.length === 0) {
          showInfo("No attendance data available");
        }
        setHistory(data.history || []);
      }
      
      const sess = await apiFetch("/api/lectures/sessions");
      if (sess.ok) {
        const data = await sess.json();
        if (!data.sessions || data.sessions.length === 0) {
          showInfo("No lectures found for selected semester");
        }
        setSessions(data.sessions || []);
      }
    } catch (err) {
      showError("Something went wrong. Please try again");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAllData();
  }, []);

  const remainingTo75 = useMemo(() => {
    const { total_lectures, lectures_attended } = stats;
    if (total_lectures === 0) return 0;
    const target = Math.ceil(0.75 * total_lectures);
    return Math.max(0, target - lectures_attended);
  }, [stats]);

  const getAttendanceColor = (attended, total) => {
    if (total === 0) return '#9CA3AF';
    const percentage = (attended / total) * 100;
    if (percentage >= 75) return '#10B981'; // green
    if (percentage >= 50) return '#F59E0B'; // amber
    if (percentage >= 25) return '#EF6347'; // coral
    return '#EF4444'; // red
  };

  // Get all subjects from sessions for student's semester only
  const subjectsFromSessions = {};
  const semesterSessions = studentSemester 
    ? sessions.filter(s => String(s.semester) === String(studentSemester))
    : sessions;
  semesterSessions.forEach(session => {
    const subject = session.lecture_subject || 'Unknown';
    if (!subjectsFromSessions[subject]) {
      subjectsFromSessions[subject] = 0;
    }
    subjectsFromSessions[subject]++;
  });

  // Count attendance for each subject from history
  const historyBySubject = {};
  Object.keys(subjectsFromSessions).forEach(subject => {
    historyBySubject[subject] = { present: 0, total: subjectsFromSessions[subject] };
  });

  history.forEach(item => {
    const subject = item.lecture_subject || 'Unknown';
    if (!historyBySubject[subject]) {
      historyBySubject[subject] = { present: 0, total: subjectsFromSessions[subject] || 0 };
    }
    if (item.status === 'present' || item.status === 'late') {
      historyBySubject[subject].present++;
    }
  });

  const barData = Object.entries(historyBySubject).map(([subject]) => {
    const data = historyBySubject[subject];
    const color = getAttendanceColor(data.present, data.total);
    return {
      name: getShortSubjectForm(subject),
      attended: data.present,
      total: data.total,
      ratio: `${data.present}/${data.total}`,
      fill: color
    };
  });

  const attendancePercentage = stats.total_lectures === 0 ? 0 : Math.round((stats.lectures_attended / stats.total_lectures) * 100);
  
  const getPieColors = () => {
    if (attendancePercentage >= 75) return ['#10B981', '#E5E7EB']; // green
    if (attendancePercentage >= 50) return ['#F59E0B', '#E5E7EB']; // amber
    if (attendancePercentage >= 25) return ['#EF6347', '#E5E7EB']; // coral
    return ['#EF4444', '#E5E7EB']; // red
  };

  const pieData = [
    { name: "Attended", value: stats.lectures_attended },
    { name: "Missed", value: Math.max(0, stats.total_lectures - stats.lectures_attended) }
  ];
  
  const pieColors = getPieColors();

  const now = new Date();
  const upcoming = sessions
    .filter((s) => {
      const startTime = new Date(s.start_time);
      const endTime = new Date(s.end_time);
      return startTime >= now && endTime >= now && s.status !== "closed";
    })
    .slice(0, 5);

  const past = sessions
    .filter((s) => {
      const endTime = new Date(s.end_time);
      return endTime < now || s.status === "closed";
    })
    .sort((a, b) => new Date(b.end_time) - new Date(a.end_time));

  return (
    <SidebarLayout role="student">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa]">STUDENT DASHBOARD</h1>
        <p className="text-neutral dark:text-slate-400 mt-2">Track your lecture participation and attendance performance</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard label="Total Lectures" value={stats.total_lectures} />
        <MetricCard label="Lectures Attended" value={stats.lectures_attended} />
        <MetricCard label="Needed for 75%" value={remainingTo75} />
      </div>

      {/* Attendance Alert */}
      {stats.total_lectures > 0 && stats.attendance_percentage < 75 && (
        <div className="mb-8 rounded-lg border-l-4 border-warning bg-warning/10 dark:bg-warning/20 p-4 flex items-start gap-3">
          <div>
            <p className="font-bold text-warning dark:text-yellow-300">Attendance Below 75%</p>
            <p className="text-sm text-warning/80 dark:text-yellow-200 mt-1">
              You need to attend {remainingTo75} more lecture(s) to reach the 75% attendance requirement.
            </p>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          <h2 className="text-lg font-bold text-[#0466c8] dark:text-[#60a5fa] mb-6 uppercase tracking-wide">Overall Attendance</h2>
          <div className="relative h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" innerRadius={60} outerRadius={90} paddingAngle={4}>
                  <Cell fill={pieColors[0]} />
                  <Cell fill={pieColors[1]} />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <div className="text-3xl font-bold text-[#0466c8] dark:text-[#60a5fa]">{attendancePercentage}%</div>
                <div className="text-xs text-neutral dark:text-slate-400 mt-1">Attendance Rate</div>
              </div>
            </div>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="rounded-lg border border-slate-200 dark:border-[#33415c] bg-white dark:bg-[#002855] shadow-sm p-6">
          <h2 className="text-lg font-bold text-[#0466c8] dark:text-[#60a5fa] mb-6 uppercase tracking-wide">Subject-wise Attendance</h2>
          
          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 mb-6 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{backgroundColor: '#10B981'}}></div>
              <span className="text-slate-700">75%+ (Good)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{backgroundColor: '#F59E0B'}}></div>
              <span className="text-slate-700">50-74% (Fair)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{backgroundColor: '#EF6347'}}></div>
              <span className="text-slate-700">25-49% (Poor)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{backgroundColor: '#EF4444'}}></div>
              <span className="text-slate-700">Below 25% (Critical)</span>
            </div>
          </div>

          {/* Chart */}
          <div className="h-64">
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData}>
                  <XAxis dataKey="name" />
                  <YAxis hide />
                  <Tooltip formatter={(value, name, props) => {
                    if (name === 'attended') {
                      return `${props.payload.ratio} lectures`;
                    }
                    return value;
                  }} />
                  <Bar dataKey="attended" radius={[6, 6, 0, 0]}>
                    {barData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No subject data available
              </div>
            )}
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
