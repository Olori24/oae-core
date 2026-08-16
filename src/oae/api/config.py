import json
import os
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./oae.db"
    # Kept for backward compatibility. New API keys use per-key salted PBKDF2.
    api_key_pepper: str = ""
    cors_origins: Annotated[list[str], NoDecode] = ["*"]
    allowed_hosts: Annotated[list[str], NoDecode] = ["*"]
    max_job_seconds: int = 300

    @field_validator("app_env", "database_url", "api_key_pepper", mode="before")
    @classmethod
    def empty_string_to_default(cls, value, info):
        if value == "":
            defaults = {
                "app_env": "development",
                "database_url": "sqlite:///./oae.db",
                "api_key_pepper": "",
            }
            return defaults[info.field_name]
        return value

    @field_validator("max_job_seconds", mode="before")
    @classmethod
    def parse_job_seconds(cls, value):
        if value is None or value == "":
            return 300
        return value

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
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.strip("[]").split(",") if item.strip()]
        raise TypeError("Expected a list or string")

    @property
    def sqlite_path(self) -> Path:
        configured = self.database_url.removeprefix("sqlite:///")
        if os.getenv("VERCEL") and self.database_url == "sqlite:///./oae.db":
            return Path("/tmp/oae.db")
        return Path(configured)


settings = Settings()
