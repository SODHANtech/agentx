function Message({ sender, text }) {
  const isUser = sender === "user";

  let data = null;

  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }

  // Ensure JSON contains at least one of the structured agent response keys
  const hasStructuredKeys = data && (
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
          <p>{text}</p>
        )}
      </div>
    </div>
  );
}

export default Message;