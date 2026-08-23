import React, { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import { getNotifications } from "../services/api";

export default function Notifications() {

  const [notifications, setNotifications] = useState([]);

  useEffect(() => {

    async function loadNotifications() {

      try {

        const data = await getNotifications();

        setNotifications(data);

      } catch (err) {

        console.error(err);

      }

    }

    loadNotifications();

  }, []);

  return (

    <div className="flex h-screen bg-slate-950 text-white">

      <Sidebar />

      <div className="flex flex-1 flex-col">

        <Navbar />

        <div className="p-8 overflow-auto">

          <h1 className="text-3xl font-bold mb-2">

            Notifications & Reminders

          </h1>

          <p className="text-slate-400 mb-8">

            AI-generated reminders and pending tasks.

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

                    <h2 className="text-lg font-semibold">

                      🔔 Reminder

                    </h2>

                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        item.status === "Pending"
                          ? "bg-yellow-500/20 text-yellow-400"
                          : "bg-green-500/20 text-green-400"
                      }`}
                    >

                      {item.status}

                    </span>

                  </div>

                  <p className="mt-4 text-slate-300">

                    {item.query}

                  </p>

                  <p className="mt-3 text-xs text-slate-500">

                    Created At: {item.created_at}

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