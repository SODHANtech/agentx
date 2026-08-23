import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

import {
  getEvents,
  registerEvent,
  cancelEvent,
  getRegisteredEvents,
} from "../services/api";

export default function Events() {
  const [events, setEvents] = useState([]);
  const [registered, setRegistered] = useState([]);
  const [loadingMap, setLoadingMap] = useState({});

  useEffect(() => {
    loadEvents();
    loadRegistrations();
  }, []);

  async function loadEvents() {
    try {
      const data = await getEvents();
      setEvents(data || []);
    } catch (err) {
      console.error("Failed to load events:", err);
    }
  }

  async function loadRegistrations() {
    try {
      const data = await getRegisteredEvents();
      const registeredEvents =
        data?.registered_events?.map((r) => r.event) || [];
      setRegistered(registeredEvents);
    } catch (err) {
      console.error("Failed to load registrations:", err);
    }
  }

  async function handleRegister(eventTitle) {
    setLoadingMap((prev) => ({ ...prev, [eventTitle]: "register" }));

    try {
      const result = await registerEvent(eventTitle);
      alert(result.message);

      if (
        result.success ||
        result.message?.includes("Successfully") ||
        result.message?.includes("already")
      ) {
        setRegistered((prev) =>
          prev.includes(eventTitle) ? prev : [...prev, eventTitle]
        );
        await loadRegistrations();
      }
    } catch (err) {
      console.error("Registration failed:", err);
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Registration failed. Please try again.";
      alert(errorMessage);
    } finally {
      setLoadingMap((prev) => ({ ...prev, [eventTitle]: false }));
    }
  }

  async function handleCancel(eventTitle) {
    const confirmCancel = window.confirm(
      `Are you sure you want to cancel your registration for "${eventTitle}"?`
    );
    if (!confirmCancel) return;

    setLoadingMap((prev) => ({ ...prev, [eventTitle]: "cancel" }));

    try {
      const result = await cancelEvent(eventTitle);
      alert(result.message);

      if (
        result.success ||
        result.message?.includes("cancelled") ||
        result.message?.includes("successfully")
      ) {
        setRegistered((prev) => prev.filter((item) => item !== eventTitle));
        await loadRegistrations();
      }
    } catch (err) {
      console.error("Cancellation failed:", err);
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Cancellation failed. Please try again.";
      alert(errorMessage);
    } finally {
      setLoadingMap((prev) => ({ ...prev, [eventTitle]: false }));
    }
  }

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Navbar />

        <div className="p-8 overflow-auto">
          <h1 className="text-3xl font-bold mb-2">Campus Events</h1>

          <p className="text-slate-400 mb-8">
            Upcoming workshops, hackathons and seminars.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((evt, index) => {
              const isRegistered = registered.includes(evt.title);
              const currentLoadingState = loadingMap[evt.title];

              return (
                <div
                  key={evt.id || index}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition"
                >
                  <div>
                    <h2 className="text-xl font-bold">{evt.title}</h2>

                    <p className="mt-3">📅 {evt.date}</p>
                    <p>⏰ {evt.time}</p>
                    <p>📍 {evt.venue}</p>
                  </div>

                  {/* Actions */}
                  {isRegistered ? (
                    <div className="mt-6 flex flex-col gap-2">
                      <div className="flex gap-2">
                        <button
                          disabled
                          className="flex-1 py-2 rounded-lg font-medium bg-green-600/80 text-white cursor-not-allowed text-center"
                        >
                          Registered ✓
                        </button>

                        <button
                          disabled={!!currentLoadingState}
                          onClick={() => handleCancel(evt.title)}
                          className={`px-3 py-2 rounded-lg font-medium transition ${
                            currentLoadingState === "cancel"
                              ? "bg-red-900/50 text-red-300 cursor-wait"
                              : "bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30"
                          }`}
                        >
                          {currentLoadingState === "cancel"
                            ? "Cancelling..."
                            : "Cancel"}
                        </button>
                      </div>

                      {/* Export Calendar Link */}
                      <a
                        href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/events/export/${encodeURIComponent(
                          evt.title
                        )}`}
                        download
                        className="w-full py-1.5 text-center text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition border border-slate-700 block"
                      >
                        📅 Export to Calendar (.ics)
                      </a>
                    </div>
                  ) : (
                    <button
                      disabled={!!currentLoadingState}
                      onClick={() => handleRegister(evt.title)}
                      className={`mt-6 py-2 rounded-lg font-medium transition ${
                        currentLoadingState === "register"
                          ? "bg-blue-600/50 cursor-wait opacity-80"
                          : "bg-blue-600 hover:bg-blue-500 text-white"
                      }`}
                    >
                      {currentLoadingState === "register"
                        ? "Registering..."
                        : "Register via AI"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}