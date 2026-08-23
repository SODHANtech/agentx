import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { getClusters, triggerClustering, broadcastResolution } from "../services/api";

export default function AdminRadar() {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [error, setError] = useState(null);

  const loadClusters = async () => {
    try {
      setError(null);
      const data = await getClusters();
      setClusters(data);
    } catch (err) {
      console.error("Failed to load clusters:", err);
      setError("Failed to fetch complaint clusters. Please make sure you are logged in as an Admin.");
    }
  };

  useEffect(() => {
    loadClusters();
  }, []);

  const handleRunClustering = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await triggerClustering();
      alert(res.message || "Semantic clustering completed successfully!");
      await loadClusters();
    } catch (err) {
      console.error("Clustering failed:", err);
      setError(err.response?.data?.detail || "Failed to trigger semantic clustering.");
    } finally {
      setLoading(false);
    }
  };

  const handleBroadcast = async (clusterId) => {
    setActionLoadingId(clusterId);
    setError(null);
    try {
      const res = await broadcastResolution(clusterId);
      alert(res.message || "Resolution broadcasted successfully!");
      await loadClusters();
    } catch (err) {
      console.error("Broadcast failed:", err);
      setError(err.response?.data?.detail || "Failed to broadcast resolution.");
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Navbar />
        <div className="p-8 overflow-auto">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">Complaint Radar</h1>
              <p className="text-slate-400">Semantic clustering and resolution of student grievances.</p>
            </div>
            <button
              onClick={handleRunClustering}
              disabled={loading}
              className={`px-5 py-3 rounded-lg font-medium text-white transition ${
                loading ? "bg-cyan-700 cursor-not-allowed" : "bg-cyan-600 hover:bg-cyan-500"
              }`}
            >
              {loading ? "Analyzing Complaints..." : "Run Semantic Clustering"}
            </button>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 text-red-200 mb-6">
              {error}
            </div>
          )}

          <div className="space-y-6">
            {clusters.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
                No active systemic issue clusters detected. Try running semantic clustering if new grievances have been submitted.
              </div>
            ) : (
              clusters.map((cluster) => (
                <div
                  key={cluster.id}
                  className={`bg-slate-900 border rounded-xl p-6 transition ${
                    cluster.status === "Broadcasted" ? "border-slate-800/80" : "border-slate-800 hover:border-cyan-500/55"
                  }`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <span className="text-xs text-cyan-400 font-semibold tracking-wider uppercase bg-cyan-950 px-2 py-1 rounded">
                        Cluster #{cluster.id}
                      </span>
                      <h2 className="text-xl font-bold mt-2 text-white">{cluster.title}</h2>
                    </div>
                    <span
                      className={`text-xs px-2.5 py-1 rounded font-medium ${
                        cluster.status === "Broadcasted"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-yellow-500/20 text-yellow-400"
                      }`}
                    >
                      {cluster.status}
                    </span>
                  </div>

                  <div className="bg-slate-950 border border-slate-800/50 rounded-lg p-4 mb-4">
                    <h3 className="text-sm font-semibold text-slate-300 mb-1">AI Action Brief</h3>
                    <p className="text-sm text-slate-400">{cluster.brief}</p>
                  </div>

                  <div className="mb-4">
                    <h4 className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-2">
                      Grouped Student Grievances
                    </h4>
                    <div className="space-y-2">
                      {cluster.complaints?.map((comp) => (
                        <div key={comp.id} className="text-xs bg-slate-950/60 p-3 rounded border border-slate-850 flex justify-between items-center">
                          <div>
                            <span className="font-semibold text-slate-300">[{comp.department}] </span>
                            <span className="text-slate-400">{comp.description}</span>
                          </div>
                          <span className="text-slate-500 italic">{comp.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {cluster.status !== "Broadcasted" && (
                    <button
                      onClick={() => handleBroadcast(cluster.id)}
                      disabled={actionLoadingId === cluster.id}
                      className={`px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                        actionLoadingId === cluster.id ? "bg-green-800 cursor-not-allowed" : "bg-green-600 hover:bg-green-500 text-white"
                      }`}
                    >
                      {actionLoadingId === cluster.id ? "Broadcasting..." : "Broadcast Resolution"}
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
