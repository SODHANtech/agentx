import logging
import re
import httpx
from typing import Dict, Any, List, Optional
from personalai.config import settings

logger = logging.getLogger(__name__)


class ModelRouter:
    """Dynamic multi-model router pipeline that inspects prompt domain, complexity, and intent
    and selects the optimal local model (Qwen Coder, DeepSeek R1, Hermes 3, Llama Vision, or Llama 3.1).
    """

    CODING_KEYWORDS = [
        r"\bcode\b", r"\bscript\b", r"\bdef\b", r"\bclass\b", r"\bfunction\b", r"\bpython\b",
        r"\bjava\b", r"\bcpp\b", r"\bc\+\+\b", r"\brust\b", r"\bsql\b", r"\bhtml\b", r"\bcss\b",
        r"\brefactor\b", r"\bdebug\b", r"\bbug\b", r"\btraceback\b", r"\bsyntax\b", r"\bapi\b",
        r"\bgit\b", r"\bimport\b", r"\bjson\b", r"\bregex\b"
    ]

    REASONING_KEYWORDS = [
        r"\bsolve\b", r"\bmath\b", r"\balgorithm\b", r"\bproof\b", r"\blogic\b", r"\bcalculate\b",
        r"\bequation\b", r"\bstep[- ]by[- ]step\b", r"\bdeduce\b", r"\btheorem\b", r"\bprobablity\b"
    ]

    TOOL_KEYWORDS = [
        r"\bdelete\b", r"\bingest\b", r"\bopen_url\b", r"\blaunch\b", r"\bmute\b", r"\bunmute\b",
        r"\bvibrate\b", r"\bset_volume\b", r"\brun_cmd\b", r"\bfile_write\b", r"\bsync\b"
    ]

    VISION_KEYWORDS = [
        r"\b(photo|image|picture)\s+of\b", r"\bdescribe\s+(the\s+)?(image|photo|picture|screenshot|diagram|chart)\b",
        r"\banalyze\s+(the\s+)?(image|photo|picture|screenshot)\b", r"\blook\s+at\s+this\s+(image|photo|picture|screenshot)\b",
        r"\bocr\b", r"\bread\s+text\s+from\s+(image|picture|photo)\b", r"\bscreenshot\b"
    ]


    def classify_intent(self, prompt: str, has_image: bool = False, requires_tools: bool = False) -> str:
        """Classifies prompt intent domain into CODING, REASONING, TOOL_CALLING, VISION, or GENERAL."""
        if has_image:
            return "VISION"

        if requires_tools:
            return "TOOL_CALLING"

        prompt_lower = prompt.lower()

        # Check Coding
        if any(re.search(kw, prompt_lower) for kw in self.CODING_KEYWORDS):
            return "CODING"

        # Check Reasoning
        if any(re.search(kw, prompt_lower) for kw in self.REASONING_KEYWORDS):
            return "REASONING"

        # Check Tool Calling
        if any(re.search(kw, prompt_lower) for kw in self.TOOL_KEYWORDS):
            return "TOOL_CALLING"

        # Check Vision text indicators
        if any(re.search(kw, prompt_lower) for kw in self.VISION_KEYWORDS):
            return "VISION"

        return "GENERAL"

    def get_installed_ollama_models(self) -> List[str]:
        """Queries local Ollama tags API to retrieve list of currently pulled models."""
        try:
            url = f"http://{settings.ollama_host}:{settings.ollama_port}/api/tags"
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                models_data = resp.json().get("models", [])
                return [m.get("name", "") for m in models_data]
        except Exception as e:
            logger.warning(f"Could not fetch installed Ollama models: {e}")
        return [settings.ollama_model]

    def select_model(self, prompt: str, has_image: bool = False, requires_tools: bool = False) -> Dict[str, Any]:
        """Determines intent and selects optimal target model with automatic fallback to general_model if unpulled."""
        if not settings.enable_auto_routing:
            return {
                "intent": "MANUAL",
                "model": settings.ollama_model,
                "fallback_used": False,
            }

        intent = self.classify_intent(prompt, has_image=has_image, requires_tools=requires_tools)
        installed_models = self.get_installed_ollama_models()

        intent_model_map = {
            "CODING": settings.coding_model,
            "REASONING": settings.reasoning_model,
            "TOOL_CALLING": settings.tool_calling_model,
            "VISION": settings.vision_model,
            "GENERAL": settings.general_model,
        }

        target_model = intent_model_map.get(intent, settings.general_model)
        fallback_used = False
        selected_model = target_model

        # Fallback check: If target model tag is not installed locally, fallback to general_model
        if installed_models and not any(target_model in m for m in installed_models):
            selected_model = settings.general_model
            fallback_used = True
            logger.info(f"Target model '{target_model}' for intent '{intent}' not installed. Falling back to '{selected_model}'.")

        return {
            "intent": intent,
            "target_model": target_model,
            "model": selected_model,
            "fallback_used": fallback_used,
        }
