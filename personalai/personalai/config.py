from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Local Inference Settings
    ollama_host: str = Field(default="127.0.0.1", description="Host for local LLM inference engine")
    ollama_port: int = Field(default=11434, description="Port for local LLM inference engine")
    ollama_model: str = Field(default="llama3.1:8b", description="Local model tag")

    # Storage & Backup Paths
    local_cache_dir: Path = Field(
        default=Path.home() / ".cache" / "local-ai",
        description="Local SSD cache directory for models, adapters, and vectors",
    )
    gdrive_remote_name: str = Field(default="gdrive:ai-node", description="rclone remote path for cold storage")

    # RAG Settings
    embedding_model_name: str = Field(default="BAAI/bge-small-en-v1.5", description="Local embedding model name")
    chroma_persist_dir: Path = Field(
        default=Path.home() / ".cache" / "local-ai" / "chroma",
        description="Directory for persistent ChromaDB storage",
    )

    # Cross-Platform Mesh Settings
    mesh_host: str = Field(default="0.0.0.0", description="Local host IP for event broker (0.0.0.0 to bind all interfaces)")
    mesh_port: int = Field(default=8765, description="WebSocket event broker port")
    mobile_device_ip: str = Field(default="100.64.0.2", description="Mobile node IP on Tailscale VPN mesh")
    mobile_adb_port: int = Field(default=5555, description="Wireless ADB TCP port")

    # Security & Permission Controls
    require_confirmation_for_destruction: bool = Field(
        default=True,
        description="Whether destructive actions (e.g. file deletion) require manual authorization confirmation",
    )
    is_ai_enabled: bool = Field(
        default=True,
        description="Master permission toggle for local AI engine execution",
    )
    is_phone_bridge_allowed: bool = Field(
        default=False,
        description="Master permission lock for cross-platform mobile device intent dispatching",
    )
    active_theme: str = Field(
        default="dark",
        description="Active GUI visual theme: 'dark' or 'light'",
    )

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}/v1"

    def ensure_directories(self) -> None:
        """Ensures all necessary local storage directories exist."""
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        (self.local_cache_dir / "base-models").mkdir(parents=True, exist_ok=True)
        (self.local_cache_dir / "adapters").mkdir(parents=True, exist_ok=True)
        (self.local_cache_dir / "knowledge").mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
