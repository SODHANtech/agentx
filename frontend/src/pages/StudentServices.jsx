import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { getAllServices, submitGrievance } from "../services/api";

export default function StudentServices() {
  const [activeTab, setActiveTab] = useState("all");
  const [services, setServices] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedService, setSelectedService] = useState(null);

  // Form states for modal actions
  const [actionInput, setActionInput] = useState("");
  const [actionResult, setActionResult] = useState(null);

  // Grievance states
  const [grievanceCategory, setGrievanceCategory] = useState("General");
  const [grievanceDesc, setGrievanceDesc] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadServices();
  }, []);

  async function loadServices() {
    try {
      const data = await getAllServices();
      setServices(data || []);
    } catch (err) {
      console.error("Failed to load services:", err);
    }
  }

  function handleCardClick(service) {
    setSelectedService(service);
    setActionInput("");
    setActionResult(null);
  }

  function handleModalAction() {
    if (!actionInput.trim()) return;

    if (selectedService.service === "Library") {
      setActionResult({
        type: "success",
        message: `Book "${actionInput}" is Available in Section B-4. Reserved for 24 hours!`,
      });
    } else if (selectedService.service === "Hostel") {
      setActionResult({
        type: "success",
        message: `Application submitted for Room Request: ${actionInput}`,
      });
    } else {
      setActionResult({
        type: "success",
        message: `Request regarding "${actionInput}" registered with ${selectedService.office}.`,
      });
    }
  }

  async function handleGrievanceSubmit(e) {
    e.preventDefault();
    if (!grievanceDesc.trim()) return;

    setIsSubmitting(true);
    try {
      const result = await submitGrievance(grievanceCategory, grievanceDesc);
      alert(result.message);
      setGrievanceDesc("");
    } catch (err) {
      console.error("Grievance submission failed:", err);
      alert("Failed to submit grievance.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const filteredServices = services.filter((s) => {
    const query = searchTerm.toLowerCase();
    return (
      s.service?.toLowerCase().includes(query) ||
      s.office?.toLowerCase().includes(query) ||
      s.description?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Navbar />

        <div className="p-8 overflow-auto">
          <h1 className="text-3xl font-bold mb-2">Student Services</h1>
          <p className="text-slate-400 mb-8">
            Campus utilities, timing details, office locations, and grievance ticketing.
          </p>

          {/* Navigation Tabs */}
          <div className="flex gap-4 mb-8 border-b border-slate-800 pb-4">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeTab === "all"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-900 text-slate-400 hover:text-white"
              }`}
            >
              Campus Services
            </button>
            <button
              onClick={() => setActiveTab("grievance")}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeTab === "grievance"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-900 text-slate-400 hover:text-white"
              }`}
            >
              Submit Grievance
            </button>
          </div>

          {/* Services Tab View */}
          {activeTab === "all" && (
            <div>
              <div className="mb-6">
                <input
                  type="text"
                  placeholder="Search service, office, or keyword..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full md:w-1/2 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Dynamic Clickable Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredServices.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleCardClick(item)}
                    className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-blue-500 hover:scale-[1.01] cursor-pointer transition"
                  >
                    <div>
                      <div className="flex justify-between items-start">
                        <h2 className="text-xl font-bold text-blue-400">
                          {item.service}
                        </h2>
                        <span className="text-xs bg-blue-950 text-blue-400 px-2 py-1 rounded">
                          Click to manage
                        </span>
                      </div>
                      <p className="mt-3 text-slate-300 text-sm leading-relaxed">
                        {item.description}
                      </p>
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-400 space-y-1">
                      <p>🏢 <span className="font-medium text-slate-200">{item.office}</span></p>
                      <p>⏰ {item.timing}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Grievance Submission View */}
          {activeTab === "grievance" && (
            <form
              onSubmit={handleGrievanceSubmit}
              className="max-w-xl bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4"
            >
              <h2 className="text-xl font-bold mb-4">File a Campus Grievance</h2>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">
                  Category
                </label>
                <select
                  value={grievanceCategory}
                  onChange={(e) => setGrievanceCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="Hostel">Hostel</option>
                  <option value="Library">Library</option>
                  <option value="Transport">Transport</option>
                  <option value="Accounts">Accounts / Fees</option>
                  <option value="General">General / Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">
                  Description
                </label>
                <textarea
                  rows="4"
                  value={grievanceDesc}
                  onChange={(e) => setGrievanceDesc(e.target.value)}
                  placeholder="Describe your issue or query in detail..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition"
              >
                {isSubmitting ? "Submitting..." : "Submit Grievance Ticket"}
              </button>
            </form>
          )}

          {/* Interactive Modal View */}
          {selectedService && (
            <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
              <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 relative space-y-4">
                <button
                  onClick={() => setSelectedService(null)}
                  className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl"
                >
                  ✕
                </button>

                <h2 className="text-2xl font-bold text-blue-400">
                  {selectedService.service} Actions
                </h2>
                <p className="text-slate-300 text-sm">{selectedService.description}</p>

                <div className="bg-slate-950 p-4 rounded-lg text-sm space-y-1 text-slate-400">
                  <p>📍 <strong>Office:</strong> {selectedService.office}</p>
                  <p>⏰ <strong>Timings:</strong> {selectedService.timing}</p>
                </div>

                {/* Specific Actions for Library */}
                {selectedService.service === "Library" && (
                  <div className="space-y-3 pt-2">
                    <label className="block text-sm font-medium text-slate-300">
                      Search Book Availability or Request Issue
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Enter book title or author..."
                        value={actionInput}
                        onChange={(e) => setActionInput(e.target.value)}
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                      />
                      <button
                        onClick={handleModalAction}
                        className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg font-medium"
                      >
                        Search
                      </button>
                    </div>
                  </div>
                )}

                {/* Generic Actions for Other Services */}
                {selectedService.service !== "Library" && (
                  <div className="space-y-3 pt-2">
                    <label className="block text-sm font-medium text-slate-300">
                      Submit Quick Request / Query
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Describe what you need..."
                        value={actionInput}
                        onChange={(e) => setActionInput(e.target.value)}
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-blue-500"
                      />
                      <button
                        onClick={handleModalAction}
                        className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg font-medium"
                      >
                        Submit
                      </button>
                    </div>
                  </div>
                )}

                {/* Response Feedback */}
                {actionResult && (
                  <div className="p-3 bg-emerald-950/60 border border-emerald-500/50 text-emerald-300 text-sm rounded-lg mt-3">
                    {actionResult.message}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}