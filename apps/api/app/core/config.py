from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_env: Literal["development", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = Field(8000, ge=1, le=65535)
    database_url: PostgresDsn
    redis_url: RedisDsn
    openrouter_api_key: str = Field(min_length=1)
    openrouter_base_url: HttpUrl = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: int = Field(60, ge=1, le=300)
    openrouter_max_retries: int = Field(2, ge=0, le=5)
    log_level: str = "INFO"
    log_json: bool = False
    # request limits
    max_request_size_bytes: int = Field(65536, ge=1024)  # 64KB default
    run_creation_per_hour: int = Field(10, ge=1)
    read_requests_per_minute: int = Field(60, ge=1)
    ip_requests_per_minute: int = Field(120, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
