import React from "react";

export default function MetricCard({ label, value, helper }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="text-sm font-medium text-slate-600">{label}</div>
      <div className="text-3xl font-bold text-slate-900 mt-3">{value}</div>
      {helper && <div className="text-xs text-slate-500 mt-2">{helper}</div>}
    </div>
  );
}
