function Message({ sender, text }) {
  const isUser = sender === "user";

  let data = null;

  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }

  // If data has a synthesized response, we prioritize that markdown text
  const displayText = data?.response || text;
  const sources = data?.sources || data?.knowledge?.sources || [];

  // Ensure JSON contains at least one of the structured agent response keys only if no synthesized response exists
  const hasStructuredKeys = data && !data.response && (
    data.academic ||
    data.academic_quiz ||
    data.placement ||
    data.knowledge ||
    data.notification ||
    data.events ||
    data.student_services
  );

  return (
    <div className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-5 py-4 ${
          isUser
            ? "bg-cyan-600 text-white"
            : "bg-slate-800 text-white"
        }`}
      >
        {isUser ? (
          <p>{text}</p>
        ) : (data && hasStructuredKeys) ? (
          <div className="space-y-4">

            {/* Academic */}
            {data.academic && (
              <div>
                <h3 className="font-bold text-cyan-400 mb-2">
                  📚 Today's Classes
                </h3>

                {data.academic.map((cls, i) => (
                  <div
                    key={i}
                    className="bg-slate-700 rounded-lg p-3 mb-2"
                  >
                    <p className="font-semibold">{cls.subject}</p>
                    <p className="text-sm text-slate-300">
                      🕒 {cls.time}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Placement */}
{data.placement && (
  <div>
    <h3 className="font-bold text-green-400 mb-2">
      💼 Placement
    </h3>

    <div className="bg-slate-700 rounded-lg p-3">

      {data.placement.message ? (
        <p className="text-yellow-300">
          {data.placement.message}
        </p>
      ) : (
        <>
          <p>
            <b>Company:</b> {data.placement.company}
          </p>

          <p>
            <b>Status:</b> {data.placement.status}
          </p>
        </>
      )}

    </div>
  </div>
)}

            {/* Knowledge */}
            {data.knowledge && (
              <div>
                <h3 className="font-bold text-yellow-400 mb-2">
                  📖 Knowledge
                </h3>

                <div className="bg-slate-700 rounded-lg p-3">
                  {data.knowledge.answer}
                </div>
              </div>
            )}

            {/* Notification */}
            {data.notification && (
              <div>
                <h3 className="font-bold text-purple-400 mb-2">
                  🔔 Reminder
                </h3>

                <div className="bg-slate-700 rounded-lg p-3">
                  <p>{data.notification.message}</p>

                  {data.notification.reminder && (
                    <>
                      <p className="mt-2">
                        {data.notification.reminder.query}
                      </p>

                      <p className="text-sm text-slate-400">
                        Status: {data.notification.reminder.status}
                      </p>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Events */}
            {data.events && (
              <div>
                <h3 className="font-bold text-pink-400 mb-2">
                  🎉 Events
                </h3>

                {data.events.map((event, i) => (
                  <div
                    key={i}
                    className="bg-slate-700 rounded-lg p-3 mb-2"
                  >
                    <p className="font-semibold">
                      {event.title}
                    </p>

                    <p className="text-sm">
                      📅 {event.date}
                    </p>

                    <p className="text-sm">
                      📍 {event.venue}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Student Services */}
            {data.student_services && (
              <div>
                <h3 className="font-bold text-orange-400 mb-2">
                  🏫 Student Services
                </h3>

                {data.student_services.map((service, i) => (
                  <div
                    key={i}
                    className="bg-slate-700 rounded-lg p-3 mb-2"
                  >
                    <p className="font-semibold">
                      {service.service}
                    </p>

                    <p>{service.description}</p>

                    <p className="text-sm text-slate-300">
                      📍 {service.office}
                    </p>
                  </div>
                ))}
              </div>
            )}

          </div>
        ) : (
          <div className="text-slate-100 text-sm leading-relaxed space-y-1">
            {formatMarkdown(displayText)}
            {sources && sources.length > 0 && (
              <div className="mt-3 pt-2.5 border-t border-slate-700/60 flex flex-wrap gap-1.5 items-center text-xs">
                <span className="text-slate-400 font-medium">Verified Sources:</span>
                {sources.map((s, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 bg-slate-900/90 px-2 py-0.5 rounded text-cyan-300 border border-cyan-800/50 font-mono text-[11px]"
                  >
                    📄 {s.document}{s.page ? ` (p. ${s.page})` : ""}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function parseInline(text) {
  if (typeof text !== "string") return text;
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

function formatMarkdown(content) {
  if (typeof content !== "string") return String(content || "");
  const lines = content.split("\n");
  return lines.map((line, idx) => {
    if (line.startsWith("### ")) {
      return (
        <h4 key={idx} className="font-bold text-cyan-300 mt-2 mb-1">
          {parseInline(line.slice(4))}
        </h4>
      );
    }
    if (line.startsWith("## ")) {
      return (
        <h3 key={idx} className="font-bold text-base text-white mt-3 mb-1">
          {parseInline(line.slice(3))}
        </h3>
      );
    }
    if (line.startsWith("# ")) {
      return (
        <h2 key={idx} className="font-extrabold text-lg text-white mt-3 mb-2">
          {parseInline(line.slice(2))}
        </h2>
      );
    }
    if (
      line.trim().startsWith("- ") ||
      line.trim().startsWith("• ") ||
      line.trim().startsWith("* ")
    ) {
      return (
        <div key={idx} className="flex items-start gap-2 ml-2 my-0.5">
          <span className="text-cyan-400 mt-1">•</span>
          <span>{parseInline(line.trim().replace(/^[-•*]\s+/, ""))}</span>
        </div>
      );
    }
    if (line.trim() === "") {
      return <div key={idx} className="h-1.5" />;
    }
    return (
      <p key={idx} className="leading-relaxed">
        {parseInline(line)}
      </p>
    );
  });
}

export default Message;