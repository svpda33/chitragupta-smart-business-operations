"""Application settings loaded from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./instance/chitragupta.db"
    default_currency: str = "INR"
    high_overdue_threshold_paise: int = 5000000
    cors_origins: list[str] = ["http://127.0.0.1:5180", "http://localhost:5180"]

    # Gemini Finance Copilot settings
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    ai_request_timeout_seconds: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def clean_api_key(cls, value):
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed or trimmed.lower() in {"your_gemini_api_key_here", "replace_me", "changeme"}:
                return None
            return trimmed
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
