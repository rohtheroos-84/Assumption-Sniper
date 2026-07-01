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
    openrouter_primary_model: str = "openai/gpt-4o-mini"
    openrouter_reasoning_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_fallback_model: str = "openai/gpt-4.1-mini"
    openrouter_fast_model: str = "openai/gpt-4o-mini"
    openrouter_max_tokens: int = Field(1200, ge=32, le=8192)
    log_level: str = "INFO"
    log_json: bool = False
    # auth / api key
    jwt_secret: str = Field(...)
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = Field(60, ge=1)
    # request limits
    max_request_size_bytes: int = Field(65536, ge=1024)  # 64KB default
    run_creation_per_hour: int = Field(10, ge=1)
    read_requests_per_minute: int = Field(60, ge=1)
    ip_requests_per_minute: int = Field(120, ge=1)
    run_burst_per_minute: int = Field(5, ge=1)
    max_concurrent_runs_per_user: int = Field(2, ge=1)
    max_queue_depth: int = Field(50, ge=1)
    queue_task_max_retries: int = Field(2, ge=0, le=5)
    default_page_size: int = Field(50, ge=1, le=200)
    max_page_size: int = Field(200, ge=1, le=500)
    ai_cache_ttl_seconds: int = Field(60 * 60 * 24 * 7, ge=60)
    ai_batch_size: int = Field(8, ge=1, le=32)
    openrouter_circuit_failure_threshold: int = Field(5, ge=1)
    openrouter_circuit_cooldown_seconds: int = Field(60, ge=5)
    sse_poll_interval_seconds: float = Field(1.0, ge=0.1, le=10.0)
    sse_use_redis_pubsub: bool = True
    db_pool_size: int = Field(5, ge=1, le=50)
    db_max_overflow: int = Field(10, ge=0, le=100)
    max_input_text_length: int = Field(50000, ge=256, le=200000)
    data_retention_days_raw: int = Field(30, ge=1)
    data_retention_days_summaries: int = Field(365, ge=1)
    data_retention_days_metrics: int = Field(730, ge=1)
    account_deletion_grace_days: int = Field(7, ge=1)
    # observability
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    trace_ttl_seconds: int = Field(86400, ge=60)
    slo_api_latency_p95_ms: float = Field(500.0, ge=1)
    slo_error_rate_percent: float = Field(1.0, ge=0.01, le=100.0)
    slo_pipeline_success_percent: float = Field(95.0, ge=1, le=100.0)
    budget_alert_usd_per_hour: float = Field(10.0, ge=0.01)
    # launch / beta
    beta_enabled: bool = False
    beta_invite_codes: str = Field(default="founder-beta,pm-beta")
    routing_profile: str = Field(default="balanced", pattern="^(cost|balanced|quality)$")
    demo_rate_limit_per_minute: int = Field(20, ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
