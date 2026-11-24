"""Application Configuration and Secure Environment Parsing.

Loads settings from environment variables with strong typing via Pydantic Settings.
Strictly parses key pools into aliased identifiers (key_1, key_2, ...) to prevent
raw API keys from ever leaking to clients or logs.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeyConfig:
    """Represents an internal mapped API key with a safe alias."""

    def __init__(self, key_id: str, secret_key: str):
        self.key_id = key_id
        self.secret_key = secret_key

    def __repr__(self) -> str:
        # Prevent secret exposure in debug dumps
        return f"<KeyConfig key_id='{self.key_id}' secret_key='[REDACTED]'>"


class Settings(BaseSettings):
    """Central configuration validated through environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Raw comma-separated key pool from environment
    LLM_API_KEYS: str = Field(
        default="",
        description="Comma-separated pool of at least 2 LLM API keys.",
    )

    # Active LLM model identifier (default to Google Gemini 2.0 Flash)
    LLM_MODEL: str = Field(
        default="gemini/gemini-2.0-flash",
        description="Target model identifier supported by LiteLLM.",
    )

    # SQLite Database connection string
    DATABASE_URL: str = Field(
        default="sqlite:///./data/app.db",
        description="Database URL for SQLite persistence.",
    )

    # Comma-separated list of allowed origins for CORS
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Permitted CORS origins.",
    )

    # Switch for failover simulation hook (X-Simulate-Failure)
    ENABLE_FAILURE_SIMULATION: bool = Field(
        default=True,
        description="Whether to honor X-Simulate-Failure request header.",
    )

    # Host and port for Uvicorn
    HOST: str = Field(default="0.0.0.0", description="Bind host address.")
    PORT: int = Field(default=8000, description="Bind port.")

    # Application metadata
    APP_NAME: str = "RelayAI LLM Gateway"
    APP_VERSION: str = "1.0.0"

    @property
    def key_pool(self) -> List[KeyConfig]:
        """Parses comma-separated LLM_API_KEYS into ordered KeyConfig instances.

        Returns an ordered list of keys aliased as key_1, key_2, ..., key_N.
        """
        raw_keys = [k.strip() for k in self.LLM_API_KEYS.split(",") if k.strip()]
        return [KeyConfig(key_id=f"key_{i+1}", secret_key=k) for i, k in enumerate(raw_keys)]

    @property
    def cors_origins(self) -> List[str]:
        """Parses ALLOWED_ORIGINS into a clean list of allowed domain strings."""
        if not self.ALLOWED_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def keys_configured_count(self) -> int:
        """Returns the total number of distinct keys loaded in the pool."""
        return len(self.key_pool)


# Singleton instance for dependency injection across application
settings = Settings()

