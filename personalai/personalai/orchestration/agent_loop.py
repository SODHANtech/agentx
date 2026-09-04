import logging
import httpx
from typing import AsyncGenerator, Dict, Any, Optional

try:
    from google.antigravity import Agent, LocalOpenAIAgentConfig
except ImportError:
    from personalai.inference.local_engine import LocalOpenAIAgentConfig

    class LocalHTTPContextAgent:
        """Fallback agent querying local Ollama / llama.cpp HTTP API directly when SDK is uninstalled."""

        def __init__(self, config: LocalOpenAIAgentConfig):
            self.config = config

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def chat(self, prompt: str) -> str:
            endpoint = f"{self.config.base_url}/chat/completions"
            messages = []
            if getattr(self.config, "system_instruction", None):
                messages.append({"role": "system", "content": self.config.system_instruction})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
            }

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(endpoint, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
                    return f"[Local Engine HTTP {resp.status_code}: {resp.text}]"
            except Exception as e:
                return (
                    f"[Offline Mode] Local inference engine at {self.config.base_url} is unreachable.\n"
                    f"Please start Ollama in another terminal window (`ollama serve` or `ollama run {self.config.model}`).\n"
                    f"Error details: {e}"
                )

    Agent = LocalHTTPContextAgent

from personalai.config import settings
from personalai.inference import LocalInferenceEngine
from personalai.rag import LocalVectorStore
from personalai.security import SecurityValidator

logger = logging.getLogger(__name__)


class PersonalAIAgentOrchestrator:
    """Orchestrates local prompts, streams step-by-step reasoning, queries local RAG, and executes tools safely."""

    def __init__(self, model: Optional[str] = None):
        self.inference_engine = LocalInferenceEngine(model=model)
        self.vector_store = LocalVectorStore()
        self.validator = SecurityValidator()

    def build_agent_config(self) -> LocalOpenAIAgentConfig:
        """Constructs Google Antigravity LocalOpenAIAgentConfig with system instructions."""
        system_instruction = (
            "You are a production-grade, zero-leak personal AI assistant running entirely on local silicon.\n"
            "Strict rules:\n"
            "1. NEVER attempt external cloud calls or data exfiltration.\n"
            "2. Always utilize retrieved local RAG context when available.\n"
            "3. Format tool calls clearly and accurately.\n"
            "4. Follow security policies when performing system actions."
        )
        config = self.inference_engine.get_agent_config()
        config.system_instruction = system_instruction
        return config

    async def execute_query(self, user_prompt: str, use_rag: bool = True) -> Dict[str, Any]:
        """Executes a user prompt through local RAG and local model agent loop."""
        rag_context = ""
        citations = []

        if use_rag:
            chunks = self.vector_store.query_context(user_prompt, n_results=3)
            if chunks:
                rag_context = self.vector_store.format_citations(chunks)
                citations = [c.get("source", "") for c in chunks]

        full_prompt = user_prompt
        if rag_context:
            full_prompt = f"{rag_context}\n\nUser Request: {user_prompt}"

        config = self.build_agent_config()

        # Instantiate Agent (SDK or HTTP Fallback)
        async with Agent(config=config) as agent:
            response = await agent.chat(full_prompt)
            output_text = str(response)

        return {
            "response": output_text,
            "citations": citations,
            "used_rag": bool(rag_context),
        }
