from functools import lru_cache
import secrets

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/ai_research_assistant.db"
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    access_token_expire_minutes: int = Field(default=60, gt=0)
    max_upload_size_mb: int = Field(default=10, gt=0)
    ai_base_url: str | None = None
    ai_api_key: SecretStr | None = None
    ai_chat_model: str = "gpt-4o-mini"
    ai_embedding_model: str = "text-embedding-3-small"
    ai_timeout_seconds: int = Field(default=60, gt=0)
    frontend_origin: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
