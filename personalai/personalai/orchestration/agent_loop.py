import logging
import httpx
import re
import json
import websockets
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
                async with httpx.AsyncClient(timeout=120.0) as client:
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
                    f"Please verify Ollama is running (`ollama serve` or `ollama run {self.config.model}`).\n"
                    f"Error details: {e}"
                )


    Agent = LocalHTTPContextAgent

from personalai.config import settings
from personalai.inference import LocalInferenceEngine
from personalai.rag import LocalVectorStore
from personalai.security import SecurityValidator
from personalai.orchestration.model_router import ModelRouter

logger = logging.getLogger(__name__)


class PersonalAIAgentOrchestrator:
    """Orchestrates local prompts, streams step-by-step reasoning, queries local RAG, and executes tools safely."""

    def __init__(self, model: Optional[str] = None):
        self.inference_engine = LocalInferenceEngine(model=model)
        self.vector_store = LocalVectorStore()
        self.validator = SecurityValidator()
        self.router = ModelRouter()

    def build_agent_config(self, target_model: Optional[str] = None) -> LocalOpenAIAgentConfig:
        """Constructs Google Antigravity LocalOpenAIAgentConfig with system instructions."""
        system_instruction = (
            "You are a production-grade, zero-leak personal AI assistant running entirely on local silicon.\n"
            "Strict rules:\n"
            "1. NEVER attempt external cloud calls or data exfiltration.\n"
            "2. Always utilize retrieved local RAG context when available.\n"
            "3. Format tool calls clearly and accurately.\n"
            "4. Follow security policies when performing system actions."
        )
        engine = LocalInferenceEngine(model=target_model or settings.ollama_model)
        config = engine.get_agent_config()
        config.system_instruction = system_instruction
        return config

    async def _dispatch_phone_payload(self, payload: Dict[str, Any]) -> str:
        """Dispatches an action payload over local P2P Mesh Broker (port 8765) to connected Termux mobile node."""
        if not settings.is_phone_bridge_allowed:
            return (
                "[SECURITY LOCK] Action Blocked: P2P Phone Bridge Permission is currently LOCKED in Security Controls.\n\n"
                "Please click [ Phone Bridge: LOCKED ] in the Desktop GUI sidebar or Settings modal to allow phone actions."
            )

        try:
            client_host = "127.0.0.1" if settings.mesh_host in ("0.0.0.0", "") else settings.mesh_host
            url = f"ws://{client_host}:{settings.mesh_port}"
            async with websockets.connect(url, open_timeout=3.0) as ws:


                await ws.send(json.dumps(payload))
                action = payload.get("action")
                target = payload.get("url") or payload.get("volume") or "device"
                return (
                    f"[PHONE DISPATCH] Phone Intent Dispatched & Executed!\n"
                    f"- Action: `{action}`\n"
                    f"- Target: `{target}`\n"
                    f"- Status: Sent to connected Termux mobile node via local P2P Mesh Network."
                )
        except Exception as e:
            return (
                f"[CONNECTION WARNING] Phone Bridge is ALLOWED, but could not connect to local Mesh Broker on port {settings.mesh_port}.\n"
                f"Make sure `python -m personalai.cli mesh-start` is running on your laptop! (Error: {e})"
            )


    async def execute_query(self, user_prompt: str, use_rag: bool = True, override_model: Optional[str] = None) -> Dict[str, Any]:
        """Executes a user prompt through local RAG, dynamic model routing, and local model agent loop."""
        prompt_lower = user_prompt.lower()

        # 0. Check for Phone Action Intents (URL / Volume / Vibration)
        url_match = re.search(r"https?://[^\s\"\']+", user_prompt)
        is_phone_target = "phone" in prompt_lower or "mobile" in prompt_lower or "android" in prompt_lower

        if is_phone_target:
            if url_match or "open" in prompt_lower or "youtube" in prompt_lower or "video" in prompt_lower:
                target_url = url_match.group(0) if url_match else "https://youtube.com"
                payload = {"action": "OPEN_URL", "url": target_url}
                dispatch_res = await self._dispatch_phone_payload(payload)
                return {
                    "response": dispatch_res,
                    "citations": [],
                    "used_rag": False,
                    "routing": {"intent": "TOOL_CALLING", "model": settings.tool_calling_model},
                    "used_model": "PhoneBridgeDispatch",
                }

            elif "volume" in prompt_lower or "mute" in prompt_lower or "vibrate" in prompt_lower:
                vol_match = re.search(r"\b(\d{1,2})\b", user_prompt)
                vol_val = int(vol_match.group(1)) if vol_match else 10
                action_type = "MUTE" if "mute" in prompt_lower else ("VIBRATE" if "vibrate" in prompt_lower else "SET_VOLUME")
                payload = {"action": action_type, "volume": vol_val}
                dispatch_res = await self._dispatch_phone_payload(payload)
                return {
                    "response": dispatch_res,
                    "citations": [],
                    "used_rag": False,
                    "routing": {"intent": "TOOL_CALLING", "model": settings.tool_calling_model},
                    "used_model": "PhoneBridgeDispatch",
                }

        # 1. Dynamic Model Routing
        if override_model:
            routing_res = {"intent": "OVERRIDE", "model": override_model, "fallback_used": False}
        else:
            routing_res = self.router.select_model(user_prompt)

        selected_model = routing_res["model"]
        logger.info(f"Model Router selected model '{selected_model}' for intent '{routing_res['intent']}'.")

        # 2. Local RAG Retrieval
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

        config = self.build_agent_config(target_model=selected_model)

        # 3. Agent Chat Execution
        async with Agent(config=config) as agent:
            response = await agent.chat(full_prompt)
            output_text = str(response)

        return {
            "response": output_text,
            "citations": citations,
            "used_rag": bool(rag_context),
            "routing": routing_res,
            "used_model": selected_model,
        }

