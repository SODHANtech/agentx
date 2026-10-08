import { useState } from "react";
import { askAI } from "../services/api";

export const useWorkflow = () => {
  const [agents, setAgents] = useState([]);

  const resetAgents = () => {
    setAgents([]);
  };

  /**
   * Accepts either a user prompt string OR a direct response payload.
   * Leverages real-time Server-Sent Events (/ask/stream) to progressively
   * update the AgentTimeline with live status updates, falling back to /ask.
   */
  const runWorkflow = async (input) => {
    resetAgents();

    if (typeof input !== "string") {
      const responseData = input;
      const traceSteps = responseData?.agent_steps || [];
      if (traceSteps.length > 0) {
        setAgents(traceSteps);
      }
      return (
        responseData?.response ||
        responseData?.message ||
        JSON.stringify(responseData)
      );
    }

    // Initialize immediate supervisor step in UI
    setAgents([
      {
        id: "supervisor",
        name: "Supervisor Agent",
        status: "running",
        detail: "Analyzing query intent & routing to specialized agents...",
      },
    ]);

    const token = localStorage.getItem("access_token");
    const baseUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const streamUrl = `${baseUrl}/ask/stream?query=${encodeURIComponent(input)}`;

    try {
      const response = await fetch(streamUrl, {
        headers: {
          Authorization: token ? `Bearer ${token}` : "",
        },
      });

      if (!response.ok) {
        throw new Error(`SSE stream returned status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finalResponse = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          const dataLine = block.split("\n").find((l) => l.startsWith("data:"));
          if (dataLine) {
            try {
              const payload = JSON.parse(dataLine.replace(/^data:\s*/, ""));
              if (payload.agent_steps && payload.agent_steps.length > 0) {
                setAgents([...payload.agent_steps]);
              }
              if (payload.type === "complete") {
                finalResponse = (payload.sources && payload.sources.length > 0) ? payload : payload.response;
              }
            } catch (err) {
              console.warn("SSE chunk parse warning:", err);
            }
          }
        }
      }

      if (finalResponse) {
        return finalResponse;
      }
    } catch (streamError) {
      console.warn("Live stream fallback to standard /ask:", streamError);
    }

    // Graceful fallback to standard /ask if streaming encounters connection issues
    try {
      const responseData = await askAI(input);
      const traceSteps = responseData.agent_steps || [];
      if (traceSteps.length > 0) {
        setAgents(traceSteps);
      } else {
        setAgents([
          {
            id: "supervisor",
            name: "Supervisor Agent",
            status: "completed",
            detail: "Processed campus inquiry.",
          },
        ]);
      }
      return (
        responseData.response ||
        responseData.message ||
        JSON.stringify(responseData)
      );
    } catch (fallbackError) {
      console.error("API call failed in useWorkflow:", fallbackError);
      throw new Error("Unable to connect to the backend.");
    }
  };

  return {
    agents,
    runWorkflow,
    resetAgents,
  };
};