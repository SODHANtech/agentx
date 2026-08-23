import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import ChatBox from "../components/ChatBox";
import StatsCards from "../components/StatsCards";
import AgentTimeline from "../components/AgentTimeline";
import { useWorkflow } from "../hooks/useWorkflow";

function Dashboard() {
  const { agents, runWorkflow, resetAgents } = useWorkflow();
  const location = useLocation();
  const [selectedPrompt, setSelectedPrompt] = useState("");

  // Reset agents whenever user navigates back to Dashboard
  useEffect(() => {
    if (typeof resetAgents === "function") {
      resetAgents();
    }
  }, [location.key]);

  // Get initial prompt if navigated from Events page
  const initialPrompt = location.state?.prefill || selectedPrompt;

  const handlePillClick = (prompt) => {
    setSelectedPrompt(prompt);
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      {/* Left Sidebar */}
      <Sidebar />

      <div className="flex flex-1 flex-col">
        {/* Top Navbar */}
        <Navbar />

        <div className="flex flex-1 overflow-hidden">
          {/* Main Chat Area */}
          <div className="flex-[3] border-r border-slate-800 flex flex-col">
            
            {/* Top Stats Cards */}
            <StatsCards agents={agents} />

            {/* Quick Access Action Pills (Single Row Alignment Fix) */}
            <div className="flex flex-wrap justify-center items-center gap-3 px-6 py-3 border-b border-slate-800/60 bg-slate-950/50">
              <button
                onClick={() => handlePillClick("Show my timetable for today")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-full text-xs font-medium text-slate-300 transition"
              >
                <span>📊</span> Timetable
              </button>

              <button
                onClick={() => handlePillClick("Check my placement eligibility")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-full text-xs font-medium text-slate-300 transition"
              >
                <span>💼</span> Placement
              </button>

              <button
                onClick={() => handlePillClick("List upcoming campus events")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-full text-xs font-medium text-slate-300 transition"
              >
                <span>🎉</span> Events
              </button>

              <button
                onClick={() => handlePillClick("What is the attendance policy?")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-full text-xs font-medium text-slate-300 transition"
              >
                <span>📖</span> Policies
              </button>

              <button
                onClick={() => handlePillClick("Show my current attendance status")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-full text-xs font-medium text-slate-300 transition"
              >
                <span>📈</span> Attendance
              </button>
            </div>

            <div className="flex-1 overflow-hidden">
              <ChatBox 
                key={location.key + selectedPrompt} 
                runWorkflow={runWorkflow} 
                initialPrompt={initialPrompt} 
              />
            </div>
          </div>

          {/* Right Agent Panel */}
          <div className="w-80 bg-slate-900 p-5 overflow-y-auto">
            <h2 className="text-xl font-bold mb-5 text-slate-100">
              AI Agents
            </h2>

            <AgentTimeline agents={agents} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;