import React from "react";

const actions = [
  { label: "Timetable", icon: "📚", prompt: "Show my class schedule and timetable for today." },
  { label: "Placement", icon: "💼", prompt: "Check my eligibility for upcoming placement drives." },
  { label: "Events", icon: "🎉", prompt: "List all upcoming workshops and campus hackathons." },
  { label: "Policies", icon: "📖", prompt: "Summarize the college attendance and exam regulations." },
  { label: "Attendance", icon: "📊", prompt: "Calculate my attendance eligibility for Semester V." },
];

export default function QuickActions({ onSelectAction }) {
  return (
    <div className="flex flex-wrap justify-center gap-3 my-6 max-w-xl">
      {actions.map((act) => (
        <button
          key={act.label}
          type="button"
          onClick={() => {
            if (typeof onSelectAction === "function") {
              onSelectAction(act.prompt);
            }
          }}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 rounded-xl text-xs font-semibold text-slate-200 transition-all hover:scale-105 active:scale-95 cursor-pointer shadow-sm"
        >
          <span>{act.icon}</span>
          <span>{act.label}</span>
        </button>
      ))}
    </div>
  );
}