import React from "react";

export default function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-10 text-center">
      <div className="mx-auto mb-4 h-20 w-20 rounded-full bg-blue-50 flex items-center justify-center">
        <div className="h-10 w-10 rounded-full bg-blue-100" />
      </div>
      <div className="text-lg font-bold text-slate-800">{title}</div>
      <div className="text-sm text-slate-500 mt-2">{description}</div>
      {actionLabel && (
        <button
          onClick={onAction}
          className="mt-6 rounded-xl bg-primary text-white px-4 py-2"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
