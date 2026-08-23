import React, { useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import {
  draftEmail,
  sendNotification,
  createAnnouncement,
  bookAppointment,
} from "../services/api";

export default function Communications() {
  const [activeTab, setActiveTab] = useState("draft");
  const [output, setOutput] = useState(null);

  // Form states
  const [emailForm, setEmailForm] = useState({ recipient: "", subject: "", purpose: "" });
  const [notifForm, setNotifForm] = useState({ title: "", message: "", audience: "All Students" });
  const [annForm, setAnnForm] = useState({ title: "", content: "", category: "General" });
  const [aptForm, setAptForm] = useState({ officer: "Academic Advisor", date: "", timeSlot: "10:00 AM", reason: "" });

  const getRoleFromToken = () => {
    const token = localStorage.getItem("access_token");
    if (!token) return null;
    try {
      const payloadBase64 = token.split(".")[1];
      const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")));
      return decodedPayload.role;
    } catch (e) {
      console.error("Error parsing token:", e);
      return null;
    }
  };

  const role = getRoleFromToken();

  async function handleDraftEmail(e) {
    e.preventDefault();
    try {
      const res = await draftEmail(emailForm.recipient, emailForm.subject, emailForm.purpose);
      setOutput(res.body);
    } catch (err) {
      console.error("Draft email failed:", err);
      alert(err.response?.data?.detail || "Failed to generate draft email.");
    }
  }

  async function handleSendNotif(e) {
    e.preventDefault();
    try {
      const res = await sendNotification(notifForm.title, notifForm.message, notifForm.audience);
      alert(res.message || "Notification sent successfully!");
    } catch (err) {
      console.error("Send notification failed:", err);
      alert(err.response?.data?.detail || "Failed to broadcast notification.");
    }
  }

  async function handleCreateAnn(e) {
    e.preventDefault();
    try {
      const res = await createAnnouncement(annForm.title, annForm.content, annForm.category);
      alert(res.message || "Announcement published successfully!");
    } catch (err) {
      console.error("Create announcement failed:", err);
      alert(err.response?.data?.detail || "Failed to publish announcement.");
    }
  }

  async function handleBookApt(e) {
    e.preventDefault();
    try {
      const res = await bookAppointment(aptForm.officer, aptForm.date, aptForm.timeSlot, aptForm.reason);
      alert(res.message || "Appointment booked successfully!");
    } catch (err) {
      console.error("Book appointment failed:", err);
      alert(err.response?.data?.detail || "Failed to confirm appointment.");
    }
  }

  const tabs = [
    { key: "draft", label: "Draft Email" },
    { key: "notify", label: "Send Notification" },
    { key: "announcement", label: "Create Announcement" },
    { key: "appointment", label: "Book Appointment" },
  ].filter((tab) => {
    if (role === "Student" && (tab.key === "notify" || tab.key === "announcement")) {
      return false;
    }
    return true;
  });

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <div className="p-8 overflow-auto">
          <h1 className="text-3xl font-bold mb-2">Communication & Scheduling Center</h1>
          <p className="text-slate-400 mb-8">Draft emails, broadcast notifications, publish announcements, and book appointments.</p>

          {/* Navigation Tabs */}
          <div className="flex gap-4 mb-8 border-b border-slate-800 pb-4">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => { setActiveTab(tab.key); setOutput(null); }}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  activeTab === tab.key ? "bg-blue-600 text-white" : "bg-slate-900 text-slate-400 hover:text-white"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* 1. Draft Email Form */}
          {activeTab === "draft" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
              <form onSubmit={handleDraftEmail} className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
                <h2 className="text-xl font-bold">Generate Draft Email</h2>
                <input
                  type="text"
                  placeholder="Recipient Name/Email"
                  value={emailForm.recipient}
                  onChange={(e) => setEmailForm({ ...emailForm, recipient: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                  required
                />
                <input
                  type="text"
                  placeholder="Subject"
                  value={emailForm.subject}
                  onChange={(e) => setEmailForm({ ...emailForm, subject: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                  required
                />
                <textarea
                  placeholder="Purpose of Email"
                  value={emailForm.purpose}
                  onChange={(e) => setEmailForm({ ...emailForm, purpose: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                  rows="3"
                  required
                />
                <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-500 font-medium rounded-lg">Draft Email</button>
              </form>

              {output && (
                <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl">
                  <h3 className="text-lg font-bold mb-3 text-blue-400">Generated Draft</h3>
                  <pre className="whitespace-pre-wrap bg-slate-950 p-4 rounded-lg text-sm text-slate-300 font-sans">{output}</pre>
                </div>
              )}
            </div>
          )}

          {/* 2. Send Notification Form */}
          {activeTab === "notify" && (
            <form onSubmit={handleSendNotif} className="max-w-xl bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <h2 className="text-xl font-bold">Send Push Notification</h2>
              <input
                type="text"
                placeholder="Notification Title"
                value={notifForm.title}
                onChange={(e) => setNotifForm({ ...notifForm, title: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                required
              />
              <textarea
                placeholder="Message Content"
                value={notifForm.message}
                onChange={(e) => setNotifForm({ ...notifForm, message: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                rows="3"
                required
              />
              <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-500 font-medium rounded-lg">Broadcast Notification</button>
            </form>
          )}

          {/* 3. Announcement Form */}
          {activeTab === "announcement" && (
            <form onSubmit={handleCreateAnn} className="max-w-xl bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <h2 className="text-xl font-bold">Publish Campus Announcement</h2>
              <input
                type="text"
                placeholder="Announcement Title"
                value={annForm.title}
                onChange={(e) => setAnnForm({ ...annForm, title: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                required
              />
              <textarea
                placeholder="Announcement Details"
                value={annForm.content}
                onChange={(e) => setAnnForm({ ...annForm, content: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                rows="4"
                required
              />
              <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-500 font-medium rounded-lg">Publish Announcement</button>
            </form>
          )}

          {/* 4. Book Appointment Form */}
          {activeTab === "appointment" && (
            <form onSubmit={handleBookApt} className="max-w-xl bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <h2 className="text-xl font-bold">Schedule an Appointment</h2>
              <select
                value={aptForm.officer}
                onChange={(e) => setAptForm({ ...aptForm, officer: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
              >
                <option value="Academic Advisor">Academic Advisor</option>
                <option value="Placement Officer">Placement Officer</option>
                <option value="Hostel Warden">Hostel Warden</option>
                <option value="Dean of Student Affairs">Dean of Student Affairs</option>
              </select>
              <input
                type="date"
                value={aptForm.date}
                onChange={(e) => setAptForm({ ...aptForm, date: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                required
              />
              <textarea
                placeholder="Reason for Appointment"
                value={aptForm.reason}
                onChange={(e) => setAptForm({ ...aptForm, reason: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-white"
                rows="3"
                required
              />
              <button type="submit" className="w-full py-3 bg-blue-600 hover:bg-blue-500 font-medium rounded-lg">Confirm Appointment</button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}