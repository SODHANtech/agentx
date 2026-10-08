import os
from typing import List, Union
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Environment
    ENV: str = "development"

    # API credentials
    GROQ_API_KEY: str

    # Security
    JWT_SECRET_KEY: str = "super_secret_campus_os_jwt_key_2026_hackathon"

    # Database connection string
    DATABASE_URL: str = "sqlite:///backend/database/campus.db"

    # LLM Settings
    LLM_MODEL: str = "openai/gpt-oss-120b"

    # Server CORS allowed origins (accepts list or comma-separated string)
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173"

    # Server Port
    BACKEND_PORT: int = 8000

    # Auto-load from .env if present
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [orig.strip() for orig in self.ALLOWED_ORIGINS.split(",") if orig.strip()]
        return self.ALLOWED_ORIGINS

    @model_validator(mode="after")
    def validate_security(self) -> 'Settings':
        if self.ENV == "production" and self.JWT_SECRET_KEY == "super_secret_campus_os_jwt_key_2026_hackathon":
            raise ValueError("Insecure JWT_SECRET_KEY cannot be used in a production environment.")
        return self

settings = Settings()
