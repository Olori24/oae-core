from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./oae.db"
    api_key_pepper: str = "change-me-in-production"
    cors_origins: list[str] = ["*"]
    max_job_seconds: int = 300

    @property
    def sqlite_path(self) -> Path:
        return Path(self.database_url.removeprefix("sqlite:///"))


settings = Settings()
