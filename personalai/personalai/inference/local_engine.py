import logging
import httpx
from typing import Dict, Any, Optional

try:
    from google.antigravity import LocalOpenAIAgentConfig
except ImportError:
    class LocalOpenAIAgentConfig:
        def __init__(self, model: str, base_url: str, system_instruction: Optional[str] = None):
            self.model = model
            self.base_url = base_url
            self.system_instruction = system_instruction

from personalai.config import settings

logger = logging.getLogger(__name__)


class LocalInferenceEngine:
    """Manages connection and configuration for on-device LLM inference via Ollama / llama.cpp."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, model: Optional[str] = None):
        self.host = host or settings.ollama_host
        self.port = port or settings.ollama_port
        self.model = model or settings.ollama_model
        self.base_url = f"http://{self.host}:{self.port}/v1"

    def check_health(self) -> bool:
        """Verifies local inference server availability on 127.0.0.1."""
        try:
            response = httpx.get(f"http://{self.host}:{self.port}/api/tags", timeout=2.0)
            if response.status_code == 200:
                logger.info(f"Local inference engine active at {self.host}:{self.port}")
                return True
        except Exception as e:
            logger.warning(f"Local inference server offline at {self.host}:{self.port}: {e}")
        return False

    def get_agent_config(self) -> LocalOpenAIAgentConfig:
        """Generates a Google Antigravity LocalOpenAIAgentConfig targeting local server."""
        return LocalOpenAIAgentConfig(
            model=self.model,
            base_url=self.base_url,
        )

    def get_env_security_flags(self) -> Dict[str, str]:
        """Returns standard environment flags to enforce zero external telemetry."""
        return {
            "OLLAMA_ORIGINS": "",
            "OLLAMA_HOST": "127.0.0.1",
            "ANONYMIZED_TELEMETRY": "False",
            "DO_NOT_TRACK": "1",
        }
