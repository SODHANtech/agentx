import { useState } from "react";
import { askAI } from "../services/api";

export const useWorkflow = () => {
  const [agents, setAgents] = useState([]);

  const resetAgents = () => {
    setAgents([]);
  };

  /**
   * Accepts either a user prompt string OR a direct response response.
   * Fetches data from FastAPI backend /ask if given a string query.
   */
  const runWorkflow = async (input) => {
    resetAgents();
    let responseData = null;

    // 1. If input is a query string, call backend
    if (typeof input === "string") {
      try {
        responseData = await askAI(input);
      } catch (error) {
        console.error("API call failed in useWorkflow:", error);
        throw new Error("Unable to connect to the backend.");
      }
    } else {
      responseData = input;
    }

    if (!responseData) {
      throw new Error("Empty response from server.");
    }

    // 2. Set agents using the real-time trace returned by the backend
    const traceSteps = responseData.agent_steps || [];
    if (traceSteps.length > 0) {
      setAgents(traceSteps);
    } else {
      // Fallback log
      setAgents([
        {
          id: "supervisor",
          name: "Supervisor Agent",
          status: "completed",
          detail: "Processed general conversation query."
        }
      ]);
    }

    // 3. Return normalized response text to ChatBox
    return (
      responseData.response ||
      responseData.message ||
      JSON.stringify(responseData)
    );
  };

  return {
    agents,
    runWorkflow,
    resetAgents,
  };
};