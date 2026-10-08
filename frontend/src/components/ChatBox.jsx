import { useState, useEffect, useRef } from "react";
import WelcomeScreen from "./WelcomeScreen";
import QuickActions from "./QuickActions";
import ChatInput from "./ChatInput";
import Message from "./Message";
import TypingIndicator from "./TypingIndicator";

import { askAI, analyzeResume } from "../services/api";

function ChatBox({ runWorkflow, initialPrompt }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, typing]);

  useEffect(() => {
    if (initialPrompt) {
      executeMessageFlow(initialPrompt);
    }
  }, [initialPrompt]);

  async function executeMessageFlow(textToSend, file = null) {
    const text = textToSend || input;

    if (!text.trim() && !file) return;

    const displayMessage = file
      ? `📎 ${file.name}\n${text || "Analyze this resume."}`
      : text;

    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: displayMessage,
      },
    ]);

    setInput("");
    setTyping(true);

    try {
      let response;

      if (file) {
        response = await analyzeResume(file);
      } else {
        // Call backend API with real-time SSE streaming or fallback
        if (runWorkflow) {
          response = await runWorkflow(text);
        } else {
          response = await askAI(text);
        }
      }

      // Extract readable response string
      const botText =
        typeof response === "string"
          ? response
          : (response?.sources && response.sources.length > 0)
            ? JSON.stringify(response)
            : response?.response || response?.message || JSON.stringify(response);

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: botText,
        },
      ]);
    } catch (error) {
      console.error("ChatBox Error:", error);

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: "❌ Unable to connect to the backend.",
        },
      ]);
    } finally {
      setTyping(false);
    }
  }

  function handleSend(textParam, fileParam) {
    executeMessageFlow(textParam || input, fileParam);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <>
            <WelcomeScreen />

            <QuickActions
              onSelectAction={(prompt) => executeMessageFlow(prompt)}
            />
          </>
        ) : (
          <>
            {messages.map((msg, index) => (
              <Message
                key={index}
                sender={msg.sender}
                text={msg.text}
              />
            ))}

            {typing && <TypingIndicator />}

            <div ref={messagesEndRef}></div>
          </>
        )}
      </div>

      <ChatInput
        input={input}
        setInput={setInput}
        handleSend={handleSend}
      />
    </div>
  );
}

export default ChatBox;