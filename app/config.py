from functools import lru_cache
import secrets

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/ai_research_assistant.db"
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    access_token_expire_minutes: int = Field(default=60, gt=0)
    max_upload_size_mb: int = Field(default=10, gt=0)
    frontend_origin: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
