from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Job Assistant"
    app_env: Literal["development", "testing", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    database_url: str = (
        "mysql+asyncmy://ai_job_user:change_me@localhost:3306/"
        "ai_job_assistant?charset=utf8mb4"
    )
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: SecretStr = SecretStr("")

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @computed_field
    @property
    def docs_enabled(self) -> bool:
        return self.app_env != "production" or self.app_debug


@lru_cache
def get_settings() -> Settings:
    return Settings()
