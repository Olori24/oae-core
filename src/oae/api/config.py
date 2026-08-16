from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./oae.db"
    api_key_pepper: str = "change-me-in-production"
    cors_origins: list[str] = ["*"]
    allowed_hosts: list[str] = ["*"]
    max_job_seconds: int = 300

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
