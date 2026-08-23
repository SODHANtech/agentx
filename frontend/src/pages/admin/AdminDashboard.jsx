import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { getHealth } from "../../services/api";
import { Users, GraduationCap, ShieldAlert, Cpu, Database, Server } from "lucide-react";

export default function AdminDashboard() {
  const [healthData, setHealthData] = useState({
    backend: "offline",
    database: "disconnected",
    uptime: 0,
    totalUsers: 0,
    students: 0,
    admins: 0
  });
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    try {
      const data = await getHealth();
      setHealthData(data);
      setError(null);
    } catch (err) {
      console.error("Health fetch failed:", err);
      setHealthData(prev => ({
        ...prev,
        backend: "offline",
        database: "disconnected"
      }));
      setError("Failed to fetch backend system status.");
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds) => {
    if (!seconds) return "0s";
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    let result = "";
    if (hrs > 0) result += `${hrs}h `;
    if (mins > 0) result += `${mins}m `;
    result += `${secs}s`;
    return result;
  };

  const currentDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const currentTime = new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  const [timeStr, setTimeStr] = useState(currentTime);
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeStr(new Date().toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Navbar />
        
        <div className="p-8 overflow-auto flex-1">
          {/* Welcome Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 text-right text-xs text-slate-400">
              <div>{currentDate}</div>
              <div className="font-mono text-cyan-400 font-semibold mt-1">{timeStr}</div>
            </div>
            <h1 className="text-3xl font-bold mb-2">Welcome, Admin</h1>
            <p className="text-slate-400 max-w-xl">
              System Operations dashboard. Monitor platform usage, database connections, and AI scheduling components in real time.
            </p>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 text-red-200 mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="p-3 bg-cyan-950 text-cyan-400 rounded-lg">
                <Users size={24} />
              </div>
              <div>
                <div className="text-xs text-slate-400 font-semibold">Total Users</div>
                <div className="text-2xl font-bold mt-1">{healthData.totalUsers}</div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="p-3 bg-purple-950 text-purple-400 rounded-lg">
                <GraduationCap size={24} />
              </div>
              <div>
                <div className="text-xs text-slate-400 font-semibold">Students</div>
                <div className="text-2xl font-bold mt-1">{healthData.students}</div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="p-3 bg-indigo-950 text-indigo-400 rounded-lg">
                <ShieldAlert size={24} />
              </div>
              <div>
                <div className="text-xs text-slate-400 font-semibold">Admins</div>
                <div className="text-2xl font-bold mt-1">{healthData.admins}</div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="p-3 bg-emerald-950 text-emerald-400 rounded-lg">
                <Server size={24} />
              </div>
              <div>
                <div className="text-xs text-slate-400 font-semibold">API Gateway</div>
                <div className={`text-sm font-bold mt-2 uppercase ${healthData.backend === "online" ? "text-emerald-400" : "text-red-400"}`}>
                  {healthData.backend === "online" ? "Connected" : "Disconnected"}
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
              <div className="p-3 bg-blue-950 text-blue-400 rounded-lg">
                <Database size={24} />
              </div>
              <div>
                <div className="text-xs text-slate-400 font-semibold">Database (SQL)</div>
                <div className={`text-sm font-bold mt-2 uppercase ${healthData.database === "connected" ? "text-blue-400" : "text-red-400"}`}>
                  {healthData.database === "connected" ? "Connected" : "Disconnected"}
                </div>
              </div>
            </div>
          </div>

          {/* System Status Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Cpu className="text-cyan-400" size={20} />
                Infrastructure Health Status
              </h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2.5 border-b border-slate-800">
                  <span className="text-sm text-slate-400">Backend API Gateway</span>
                  <span className={`text-xs px-2.5 py-1 rounded font-semibold ${healthData.backend === "online" ? "bg-emerald-950 text-emerald-400" : "bg-red-950 text-red-400"}`}>
                    {healthData.backend === "online" ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>

                <div className="flex justify-between items-center py-2.5 border-b border-slate-800">
                  <span className="text-sm text-slate-400">Primary Database (SQLite)</span>
                  <span className={`text-xs px-2.5 py-1 rounded font-semibold ${healthData.database === "connected" ? "bg-blue-950 text-blue-400" : "bg-red-950 text-red-400"}`}>
                    {healthData.database === "connected" ? "CONNECTED" : "DISCONNECTED"}
                  </span>
                </div>

                <div className="flex justify-between items-center py-2.5 border-b border-slate-800">
                  <span className="text-sm text-slate-400">Legacy Cache Database (MongoDB)</span>
                  <span className="text-xs px-2.5 py-1 rounded font-semibold bg-slate-950 text-slate-500">
                    DISCONNECTED
                  </span>
                </div>

                <div className="flex justify-between items-center py-2.5">
                  <span className="text-sm text-slate-400">API Server Uptime</span>
                  <span className="text-sm font-mono text-cyan-400 font-semibold">
                    {formatUptime(healthData.uptime)}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
              <div>
                <h2 className="text-xl font-bold mb-4">Operations Notes</h2>
                <ul className="list-disc list-inside text-sm text-slate-400 space-y-2">
                  <li>User counts are synced live from SQLite.</li>
                  <li>Uptime registers relative start-up of FastAPI process state.</li>
                  <li>MongoDB panel is intentionally disabled as CampusOS is refactored to use SQLite as a single source of truth.</li>
                </ul>
              </div>
              <div className="text-xs text-slate-500 mt-6 italic">
                CampusOS AI Operations Panel v1.0.0
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
