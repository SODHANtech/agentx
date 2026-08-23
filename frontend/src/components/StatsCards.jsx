import React, { useEffect, useState } from "react";
import { Bot, FileText, Calendar, Users } from "lucide-react";

import { getDashboard } from "../services/api";

export default function StatsCards({ agents = [] }) {

  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {

    async function loadDashboard() {

      try {

        const data = await getDashboard();

        setDashboard(data);

      } catch (err) {

        console.error(err);

      }

    }

    loadDashboard();

  }, []);

  const runningCount = agents.filter(
    (a) => a.status === "running"
  ).length;

  const completedCount = agents.filter(
    (a) => a.status === "completed"
  ).length;

  let agentValue = "5 Ready";

  let highlight = false;

  if (runningCount > 0) {

    agentValue = `${runningCount} Active`;

    highlight = true;

  } else if (completedCount > 0) {

    agentValue = `${completedCount} Done`;

    highlight = true;

  }

  const stats = [

    {
      id: 1,
      label: "AI Agents",
      value: agentValue,
      icon: <Bot size={26} />,
      highlight,
    },

    {
      id: 2,
      label: "Classes Today",
      value: dashboard
        ? dashboard.today_classes.length
        : "...",
      icon: <Calendar size={26} />,
    },

    {
      id: 3,
      label: "Notifications",
      value: dashboard
        ? dashboard.notifications.length
        : "...",
      icon: <FileText size={26} />,
    },

    {
      id: 4,
      label: "Placement",
      value: dashboard
        ? dashboard.placement.status
        : "...",
      icon: <Users size={26} />,
    },

  ];

  return (

    <div className="grid grid-cols-4 gap-5 p-5">

      {stats.map((item) => (

        <div
          key={item.id}
          className={`p-4 rounded-xl bg-slate-800/60 border flex items-center justify-between transition-all ${
            item.highlight
              ? "border-cyan-500/50 bg-cyan-500/10 animate-pulse"
              : "border-slate-700/50"
          }`}
        >

          <div>

            <p className="text-sm text-slate-400">

              {item.label}

            </p>

            <h2 className="text-2xl font-bold text-white">

              {item.value}

            </h2>

          </div>

          <div className="text-cyan-400">

            {item.icon}

          </div>

        </div>

      ))}

    </div>

  );

}