import json
import os
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = ""
    # Kept for backward compatibility. New API keys use per-key salted PBKDF2.
    api_key_pepper: str = ""
    api_control_rate_limit_per_minute: int = 60
    cors_origins: Annotated[list[str], NoDecode] = ["*"]
    allowed_hosts: Annotated[list[str], NoDecode] = ["*"]
    max_job_seconds: int = 300
    sentry_dsn: str = ""
    workspace_root: str = "./data/oae-workspaces"
    workspace_retention_days: int = 30
    workspace_quota_bytes: int = 1024 * 1024 * 1024
    workspace_quota_count: int = 20
    workspace_file_max_bytes: int = 100 * 1024 * 1024
    postgres_pool_min_size: int = 2
    postgres_pool_max_size: int = 10
    postgres_pool_timeout_seconds: float = 5.0
    postgres_pool_max_lifetime_seconds: float = 1800.0
    durable_jobs_enabled: bool = False
    worker_authorization_enforcement_enabled: bool = False
    durable_job_lease_seconds: int = 60
    durable_job_max_attempts: int = 3
    durable_job_retry_max_seconds: int = 300
    realtime_events_enabled: bool = False
    outbox_relay_lease_seconds: int = 30
    outbox_relay_batch_size: int = 50
    outbox_relay_retry_max_seconds: int = 300
    sse_poll_seconds: float = 1.0
    sse_heartbeat_seconds: int = 15
    sse_max_connection_seconds: int = 300
    sse_replay_limit: int = 200
    open_weight_model_enabled: bool = False
    open_weight_model_endpoint: str = ""
    open_weight_model_allowed_models: Annotated[list[str], NoDecode] = []
    open_weight_model_timeout_seconds: int = 30
    open_weight_model_max_prompt_chars: int = 12_000
    open_weight_model_max_output_tokens: int = 1_024
    open_weight_model_max_response_chars: int = 16_000

    @field_validator("app_env", "database_url", "api_key_pepper", mode="before")
    @classmethod
    def empty_string_to_default(cls, value, info):
        if value == "":
            defaults = {
                "app_env": "development",
                "database_url": "",
                "api_key_pepper": "",
            }
            return defaults[info.field_name]
        return value

    @field_validator(
        "max_job_seconds",
        "api_control_rate_limit_per_minute",
        "postgres_pool_min_size",
        "postgres_pool_max_size",
        "postgres_pool_timeout_seconds",
        "postgres_pool_max_lifetime_seconds",
        "durable_job_lease_seconds",
        "durable_job_max_attempts",
        "durable_job_retry_max_seconds",
        "outbox_relay_lease_seconds",
        "outbox_relay_batch_size",
        "outbox_relay_retry_max_seconds",
        "sse_heartbeat_seconds",
        "sse_max_connection_seconds",
        "sse_replay_limit",
        "open_weight_model_timeout_seconds",
        "open_weight_model_max_prompt_chars",
        "open_weight_model_max_output_tokens",
        "open_weight_model_max_response_chars",
        mode="before",
    )
    @classmethod
    def parse_job_seconds(cls, value, info):
        if value is None or value == "":
            defaults = {
                "max_job_seconds": 300,
                "api_control_rate_limit_per_minute": 60,
                "postgres_pool_min_size": 2,
                "postgres_pool_max_size": 10,
                "postgres_pool_timeout_seconds": 5.0,
                "postgres_pool_max_lifetime_seconds": 1800.0,
                "durable_job_lease_seconds": 60,
                "durable_job_max_attempts": 3,
                "durable_job_retry_max_seconds": 300,
                "outbox_relay_lease_seconds": 30,
                "outbox_relay_batch_size": 50,
                "outbox_relay_retry_max_seconds": 300,
                "sse_heartbeat_seconds": 15,
                "sse_max_connection_seconds": 300,
                "sse_replay_limit": 200,
                "open_weight_model_timeout_seconds": 30,
                "open_weight_model_max_prompt_chars": 12_000,
                "open_weight_model_max_output_tokens": 1_024,
                "open_weight_model_max_response_chars": 16_000,
            }
            return defaults[info.field_name]
        return value

    @field_validator("cors_origins", "allowed_hosts", "open_weight_model_allowed_models", mode="before")
    @classmethod
    def parse_list_setting(cls, value, info):
        default = [] if info.field_name == "open_weight_model_allowed_models" else ["*"]
        if value is None:
            return default
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            if value.startswith("["):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.strip("[]").split(",") if item.strip()]
        raise TypeError("Expected a list or string")

    @field_validator("postgres_pool_min_size", "postgres_pool_max_size")
    @classmethod
    def validate_pool_sizes(cls, value, info):
        if value < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return value

    @field_validator("postgres_pool_timeout_seconds", "postgres_pool_max_lifetime_seconds")
    @classmethod
    def validate_pool_durations(cls, value, info):
        if value <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return value

    @property
    def resolved_database_url(self) -> str:
        """Resolve the production database from explicit and integration env names."""
        if self.database_url:
            return self.database_url

        for name in (
            "OAE_DB_DATABASE_URL",
            "OAE_DB_URL",
            "OAE_DB_POSTGRES_URL",
            "OAE_DB",
            "OAE_DB_URL_NON_POOLING",
            "POSTGRES_URL",
            "POSTGRES_PRISMA_URL",
            "POSTGRES_URL_NON_POOLING",
        ):
            value = os.getenv(name, "").strip()
            if value:
                return value

        if self.app_env == "production" or os.getenv("VERCEL"):
            return ""
        return "sqlite:///./oae.db"

    @property
    def database_backend(self) -> str:
        url = self.resolved_database_url.lower()
        if url.startswith(("postgres://", "postgresql://")):
            return "postgres"
        if url.startswith("sqlite:///"):
            return "sqlite"
        return "unknown"

    @property
    def sqlite_path(self) -> Path:
        configured = self.resolved_database_url.removeprefix("sqlite:///")
        return Path(configured)


settings = Settings()
