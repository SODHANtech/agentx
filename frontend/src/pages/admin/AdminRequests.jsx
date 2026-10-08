import React, { useEffect, useState } from "react";
import Sidebar from "../../components/Sidebar";
import Navbar from "../../components/Navbar";
import { getAdminRequests, getAdminRequestById, updateAdminRequest } from "../../services/api";
import { ClipboardList, Clock, CheckCircle2, XCircle, ArrowRight, User } from "lucide-react";

export default function AdminRequests() {
  const [requests, setRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states for status update
  const [status, setStatus] = useState("Under Review");
  const [note, setNote] = useState("");
  const [updating, setUpdating] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState("All");

  useEffect(() => {
    loadRequests();
  }, []);

  async function loadRequests() {
    setLoading(true);
    try {
      const data = await getAdminRequests();
      setRequests(data || []);
      setError(null);
    } catch (err) {
      console.error("Failed to load requests:", err);
      setError("Failed to fetch requests list from server.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectRequest(reqId) {
    try {
      const data = await getAdminRequestById(reqId);
      setSelectedRequest(data);
      setStatus(data.status);
      setNote("");
    } catch (err) {
      console.error("Failed to load request details:", err);
      alert("Failed to load request details.");
    }
  }

  async function handleUpdateSubmit(e) {
    e.preventDefault();
    if (!selectedRequest) return;

    setUpdating(true);
    try {
      await updateAdminRequest(selectedRequest.id, { status, note });
      alert(`Request #${selectedRequest.id} updated to ${status}`);
      // Reload lists
      await loadRequests();
      // Reload current details to update history view
      await handleSelectRequest(selectedRequest.id);
    } catch (err) {
      console.error("Failed to update request:", err);
      alert("Failed to update request status.");
    } finally {
      setUpdating(false);
    }
  }

  const getStatusIcon = (statusStr) => {
    switch (statusStr) {
      case "Approved":
      case "Completed":
        return <CheckCircle2 size={16} className="text-emerald-400" />;
      case "Rejected":
        return <XCircle size={16} className="text-red-400" />;
      case "Under Review":
        return <Clock size={16} className="text-amber-400" />;
      default:
        return <Clock size={16} className="text-slate-400" />;
    }
  };

  const getStatusClass = (statusStr) => {
    switch (statusStr) {
      case "Approved":
      case "Completed":
        return "bg-emerald-950/80 text-emerald-400 border border-emerald-800/50";
      case "Rejected":
        return "bg-red-950/80 text-red-400 border border-red-800/50";
      case "Under Review":
        return "bg-amber-950/80 text-amber-400 border border-amber-800/50";
      default:
        return "bg-slate-900 text-slate-400 border border-slate-800";
    }
  };

  // Filter logic
  const filteredRequests = requests.filter((r) => {
    const statusMatch = statusFilter === "All" || r.status === statusFilter;
    const typeMatch = typeFilter === "All" || r.type === typeFilter;
    return statusMatch && typeMatch;
  });

  const requestTypes = ["All", ...new Set(requests.map((r) => r.type))];

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Navbar />
        <div className="flex-1 p-8 overflow-auto">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <ClipboardList className="text-cyan-400" />
                Requests Dashboard
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Manage, review, and issue credentials, leaves, or academic doubts.
              </p>
            </div>
            <button
              onClick={loadRequests}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-lg text-sm font-semibold transition"
            >
              Refresh
            </button>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-500/50 text-red-200 p-4 rounded-xl mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Filters Bar */}
          <div className="flex flex-wrap gap-4 mb-6 bg-slate-900/50 p-4 border border-slate-800/80 rounded-xl">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500"
              >
                <option value="All">All Statuses</option>
                <option value="Pending">Pending</option>
                <option value="Under Review">Under Review</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
                <option value="Completed">Completed</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Request Type</label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-cyan-500"
              >
                {requestTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Grid Content */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">
            {/* Requests List */}
            <div className="xl:col-span-2 space-y-4">
              {loading ? (
                <div className="text-center py-10 text-slate-500">Loading requests...</div>
              ) : filteredRequests.length === 0 ? (
                <div className="text-center py-10 text-slate-500 border border-dashed border-slate-800 rounded-xl">
                  No matching student requests found.
                </div>
              ) : (
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-left">
                      <thead>
                        <tr className="border-b border-slate-850 bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase">
                          <th className="px-6 py-4">Student</th>
                          <th className="px-6 py-4">Type</th>
                          <th className="px-6 py-4">Submitted At</th>
                          <th className="px-6 py-4">Status</th>
                          <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-850">
                        {filteredRequests.map((req) => (
                          <tr
                            key={req.id}
                            className={`hover:bg-slate-850/50 transition cursor-pointer ${
                              selectedRequest?.id === req.id ? "bg-cyan-950/20" : ""
                            }`}
                            onClick={() => handleSelectRequest(req.id)}
                          >
                            <td className="px-6 py-4">
                              <div className="font-semibold text-slate-200">{req.student_name}</div>
                              <div className="text-xs text-slate-500">{req.department}</div>
                            </td>
                            <td className="px-6 py-4 font-medium text-slate-300">{req.type}</td>
                            <td className="px-6 py-4 text-xs text-slate-400">
                              {new Date(req.created_at).toLocaleString()}
                            </td>
                            <td className="px-6 py-4">
                              <span
                                className={`flex items-center gap-1.5 w-fit text-xs px-2.5 py-1 rounded-full font-semibold ${getStatusClass(
                                  req.status
                                )}`}
                              >
                                {getStatusIcon(req.status)}
                                {req.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <button className="text-xs font-bold text-cyan-400 hover:text-cyan-300 transition">
                                View Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Request Detail Panel */}
            <div className="xl:col-span-1">
              {selectedRequest ? (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                  {/* Student Details Header */}
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                        Request ID: #{selectedRequest.id}
                      </span>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${getStatusClass(
                          selectedRequest.status
                        )}`}
                      >
                        {selectedRequest.status}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-slate-100">{selectedRequest.type}</h2>
                    <p className="text-slate-400 text-xs mt-1">
                      Submitted on {new Date(selectedRequest.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="border-t border-slate-850 pt-4 space-y-3">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <User size={14} className="text-cyan-400" />
                      Student Profile
                    </h3>
                    <div className="bg-slate-950 p-3 rounded-lg text-sm space-y-1.5">
                      <p>
                        <strong className="text-slate-400 text-xs">Name:</strong>{" "}
                        <span className="text-slate-300 font-semibold">{selectedRequest.student_name}</span>
                      </p>
                      <p>
                        <strong className="text-slate-400 text-xs">Roll Number:</strong>{" "}
                        <span className="text-slate-300 font-semibold font-mono">{selectedRequest.roll_number || "N/A"}</span>
                      </p>
                      <p>
                        <strong className="text-slate-400 text-xs">Department:</strong>{" "}
                        <span className="text-slate-300 font-semibold">{selectedRequest.department || "N/A"}</span>
                      </p>
                    </div>
                  </div>

                  {/* Details Description */}
                  <div className="space-y-2">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Request Details</h3>
                    <p className="bg-slate-950 p-3 rounded-lg text-sm text-slate-300 whitespace-pre-wrap">
                      {selectedRequest.details}
                    </p>
                  </div>

                  {/* Workflow Form */}
                  <form onSubmit={handleUpdateSubmit} className="space-y-4 pt-2 border-t border-slate-850">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Update Status</h3>
                    <div className="space-y-3">
                      <div>
                        <select
                          value={status}
                          onChange={(e) => setStatus(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                        >
                          <option value="Pending">Pending</option>
                          <option value="Under Review">Under Review</option>
                          <option value="Approved">Approved</option>
                          <option value="Rejected">Rejected</option>
                          <option value="Completed">Completed</option>
                        </select>
                      </div>

                      <div>
                        <textarea
                          rows="3"
                          placeholder="Provide context or decision notes..."
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 placeholder-slate-600"
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={updating}
                        className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white text-sm font-semibold rounded-lg transition"
                      >
                        {updating ? "Updating..." : "Commit Update"}
                      </button>
                    </div>
                  </form>

                  {/* History Logs */}
                  {selectedRequest.history && selectedRequest.history.length > 0 && (
                    <div className="space-y-3 pt-4 border-t border-slate-850">
                      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Audit / History Log</h3>
                      <div className="space-y-3.5 relative pl-4 border-l border-slate-800">
                        {selectedRequest.history.map((hist, idx) => (
                          <div key={hist.id || idx} className="relative text-xs">
                            <span className="absolute -left-6 top-1.5 w-3 h-3 rounded-full bg-slate-800 border-2 border-slate-950 flex items-center justify-center"></span>
                            <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                              <span className="text-slate-400">{hist.previous_status || "Created"}</span>
                              <ArrowRight size={10} className="text-slate-500" />
                              <span className="text-cyan-400">{hist.new_status}</span>
                            </div>
                            <p className="text-slate-400 mt-1">{hist.note || "No comments entered."}</p>
                            <span className="text-[10px] text-slate-500 block mt-1">
                              By {hist.changed_by_name} • {new Date(hist.timestamp).toLocaleString()}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-slate-900/30 border border-dashed border-slate-800 rounded-xl p-8 text-center text-slate-500 text-sm">
                  Select a request from the left panel to review details, view audit trails, and commit status updates.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
