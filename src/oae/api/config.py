import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from typing import Annotated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./oae.db"
    api_key_pepper: str = "change-me-in-production"
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

    @field_validator("api_key_pepper")
    @classmethod
    def production_secret_must_change(cls, value: str, info):
        if info.data.get("app_env") == "production" and value == "change-me-in-production":
            raise ValueError("API_KEY_PEPPER must be configured in production")
        return value

    @property
    def sqlite_path(self) -> Path:
        return Path(self.database_url.removeprefix("sqlite:///"))


settings = Settings()
