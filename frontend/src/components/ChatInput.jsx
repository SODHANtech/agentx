import React, { useState, useRef, useEffect } from "react";
import { Paperclip, Mic, MicOff, Send, X, FileText } from "lucide-react";

export default function ChatInput({ input, setInput, handleSend }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [tooltip, setTooltip] = useState("");

  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize Speech Recognition on Mount
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
        showTooltip("🎤 Voice Processing Agent listening...");
      };

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((result) => result[0].transcript)
          .join("");

        setInput(transcript);
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
        showTooltip("⚠️ Voice input error / microphone access denied");
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, [setInput]);

  const showTooltip = (msg) => {
    setTooltip(msg);
    setTimeout(() => setTooltip(""), 3000);
  };

  // Toggle Speech Recognition
  const toggleListening = () => {
    if (!recognitionRef.current) {
      showTooltip("⚠️ Speech recognition is not supported in this browser");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
      } catch (err) {
        recognitionRef.current.stop();
        setIsListening(false);
      }
    }
  };

  // File Picker Handlers
  const handlePaperclipClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      showTooltip(`📎 Attached: ${file.name}`);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Submit Handler
  const onSubmit = () => {
    if (!input.trim() && !selectedFile) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    handleSend(input, selectedFile);
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="p-4 border-t border-slate-800 bg-slate-950 relative">
      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".pdf,.txt,.doc,.docx,.png,.jpg"
      />

      {/* Visual Toast Notification */}
      {tooltip && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-3 py-1 bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-xs font-semibold rounded-lg shadow-lg animate-fade-in z-10">
          {tooltip}
        </div>
      )}

      {/* Selected File Badge */}
      {selectedFile && (
        <div className="mb-2.5 inline-flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-cyan-500/40 rounded-xl text-xs text-cyan-300 shadow-sm">
          <FileText size={14} className="text-cyan-400" />
          <span className="font-medium truncate max-w-xs">{selectedFile.name}</span>
          <span className="text-[10px] text-slate-400">
            ({(selectedFile.size / 1024).toFixed(1)} KB)
          </span>
          <button
            type="button"
            onClick={handleRemoveFile}
            className="p-0.5 hover:bg-slate-700 rounded-md text-slate-400 hover:text-red-400 transition-colors ml-1"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Input Field Container */}
      <div
        className={`flex items-center gap-3 bg-slate-900 border rounded-2xl px-4 py-3 transition-all ${
          isListening
            ? "border-red-500/80 shadow-[0_0_15px_rgba(239,68,68,0.25)]"
            : "border-slate-800 focus-within:border-cyan-500/50"
        }`}
      >
        {/* Paperclip Button */}
        <button
          type="button"
          onClick={handlePaperclipClick}
          className="text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer shrink-0"
          title="Attach Document for RAG Indexing"
        >
          <Paperclip size={20} />
        </button>

        {/* Text Input */}
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            isListening
              ? "🔴 Listening... Speak your prompt..."
              : selectedFile
              ? `Ask a question about ${selectedFile.name}...`
              : "Ask Smart Campus AI..."
          }
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
        />

        {/* Voice Input Button */}
        <button
          type="button"
          onClick={toggleListening}
          className={`p-1.5 rounded-lg transition-all cursor-pointer shrink-0 ${
            isListening
              ? "bg-red-500/20 text-red-400 animate-pulse border border-red-500/40"
              : "text-slate-400 hover:text-cyan-400"
          }`}
          title={isListening ? "Stop Voice Input" : "Start Voice Input"}
        >
          {isListening ? <MicOff size={20} /> : <Mic size={20} />}
        </button>

        {/* Send Button */}
        <button
          type="button"
          onClick={onSubmit}
          className="p-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl transition-all shadow-md active:scale-95 cursor-pointer shrink-0"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}