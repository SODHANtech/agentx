function AgentTimeline({ agents }) {
  return (
    <div className="space-y-4">
      {agents.map((agent) => {
        return (
          <div
            key={agent.id}
            className="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-cyan-500/40 transition-all duration-300"
          >
            {/* Header */}
            <div className="flex justify-between items-center">
              <h2 className="font-semibold text-slate-100">
                {agent.name}
              </h2>

              {agent.status === "waiting" && (
                <span className="text-gray-400 text-xs font-semibold">
                  ⏳ Waiting
                </span>
              )}

              {agent.status === "running" && (
                <span className="text-yellow-400 text-xs font-semibold animate-pulse">
                  ⚡ Running
                </span>
              )}

              {agent.status === "completed" && (
                <span className="text-green-400 text-xs font-semibold">
                  ✅ Completed
                </span>
              )}
            </div>

            {/* Progress Bar */}
            <div className="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden">

              {agent.status === "waiting" && (
                <div className="h-full w-0 bg-gray-500"></div>
              )}

              {agent.status === "running" && (
                <div className="h-full w-2/3 bg-yellow-400 animate-pulse transition-all duration-700"></div>
              )}

              {agent.status === "completed" && (
                <div className="h-full w-full bg-green-500 transition-all duration-700"></div>
              )}

            </div>

            {/* Detail */}
            <p className="mt-3 text-sm text-slate-300">
              {agent.detail}
            </p>
          </div>
        );
      })}
    </div>
  );
}

export default AgentTimeline;