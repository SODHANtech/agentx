import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { getNotifications } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const { user } = useAuth();

  useEffect(() => {
    async function loadNotifications() {
      try {
        const data = await getNotifications();
        setNotifications(data || []);
      } catch (err) {
        console.error(err);
      }
    }
    loadNotifications();
  }, []);

  useEffect(() => {
    if (!user) return;

    const baseApiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const wsUrl = baseApiUrl.replace(/^http/, "ws") + `/ws/notifications/${user.id}`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const notif = JSON.parse(event.data);
        setNotifications((prev) => [notif, ...prev]);
      } catch (err) {
        console.error("Failed to parse websocket message:", err);
      }
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => {
      socket.close();
    };
  }, [user]);

  return (
    <div className="flex h-screen bg-slate-950 text-white">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Navbar />
        <div className="p-8 overflow-auto">
          <h1 className="text-3xl font-bold mb-2">Notifications & Reminders</h1>
          <p className="text-slate-400 mb-8">
            Real-time status updates and campus alerts.
          </p>

          <div className="space-y-4">
            {notifications.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
                No notifications available.
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-cyan-500 transition"
                >
                  <div className="flex justify-between items-center">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                      🔔 {item.title || "Alert"}
                    </h2>
                    <span
                      className={`text-xs px-2.5 py-1 rounded font-semibold ${
                        item.read
                          ? "bg-green-500/20 text-green-400"
                          : "bg-yellow-500/20 text-yellow-400"
                      }`}
                    >
                      {item.read ? "Read" : "Pending"}
                    </span>
                  </div>
                  <p className="mt-4 text-slate-300 text-sm">
                    {item.message}
                  </p>
                  <p className="mt-3 text-[10px] text-slate-500 font-mono">
                    Received: {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}