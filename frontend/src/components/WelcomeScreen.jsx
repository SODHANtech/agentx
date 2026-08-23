import React from "react";
import { Sparkles, CheckCircle2, ShieldCheck, Zap } from "lucide-react";

export default function WelcomeScreen() {
  return (
    <div className="flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-4">
      {/* Central Icon */}
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 mb-4 animate-bounce-slow">
        <Sparkles className="text-white" size={32} />
      </div>

      {/* Main Heading */}
      <h1 className="text-3xl font-extrabold text-white tracking-tight">
        Smart Campus AI
      </h1>
      <p className="text-sm text-slate-400 mt-2 max-w-md">
        Your autonomous multi-agent assistant for schedules, placement eligibility, policies, and event registration.
      </p>

      {/* Active Capabilities Grid */}
      <div className="grid grid-cols-3 gap-3 w-full mt-6 text-left">
        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl flex items-start gap-2.5">
          <ShieldCheck className="text-emerald-400 shrink-0 mt-0.5" size={18} />
          <div>
            <h4 className="text-xs font-bold text-slate-200">RAG Policy Verification</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">Instant handbook lookup</p>
          </div>
        </div>

        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl flex items-start gap-2.5">
          <Zap className="text-amber-400 shrink-0 mt-0.5" size={18} />
          <div>
            <h4 className="text-xs font-bold text-slate-200">Placement Screening</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">Automated CGPA evaluation</p>
          </div>
        </div>

        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl flex items-start gap-2.5">
          <CheckCircle2 className="text-cyan-400 shrink-0 mt-0.5" size={18} />
          <div>
            <h4 className="text-xs font-bold text-slate-200">Auto Event Sync</h4>
            <p className="text-[11px] text-slate-400 mt-0.5">1-Click calendar booking</p>
          </div>
        </div>
      </div>
    </div>
  );
}