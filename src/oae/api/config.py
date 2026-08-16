import json
import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from typing import Annotated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./oae.db"
    # Kept for backward compatibility with existing deployments. New API keys
    # use per-key salted PBKDF2 and do not depend on this global secret.
    api_key_pepper: str = ""
    cors_origins: Annotated[list[str], NoDecode] = ["*"]
    allowed_hosts: Annotated[list[str], NoDecode] = ["*"]
    max_job_seconds: int = 300

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_list_setting(cls, value):
        if value is None:
            return ["*"]
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ["*"]
            if value.startswith("["):
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError("Expected a JSON list")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        raise TypeError("Expected a list or string")

    @property
    def sqlite_path(self) -> Path:
        configured = self.database_url.removeprefix("sqlite:///")
        # Vercel's function filesystem is read-only except for /tmp. This
        # keeps the single-instance beta operational when no external DB is
        # configured. Durable multi-instance persistence still requires an
        # external database.
        if os.getenv("VERCEL") and self.database_url == "sqlite:///./oae.db":
            return Path("/tmp/oae.db")
        return Path(configured)


settings = Settings()
