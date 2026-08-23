function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-slate-800 rounded-2xl px-5 py-3">
        <span className="animate-pulse">
          Smart Campus AI is typing...
        </span>
      </div>
    </div>
  );
}

export default TypingIndicator;