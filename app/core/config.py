from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field
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
        "mysql+asyncmy://ai_job_user:change_me@localhost:3306/ai_job_assistant?charset=utf8mb4"
    )
    redis_url: str = "redis://localhost:6379/0"

    deepseek_api_key: SecretStr = SecretStr("")
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_temperature: float = Field(default=0.2, ge=0, le=2)
    deepseek_max_tokens: int = Field(default=2048, gt=0)
    deepseek_timeout_seconds: float = Field(default=60, gt=0)
    deepseek_max_retries: int = Field(default=2, ge=0, le=10)

    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "job_assistant_knowledge"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"
    rag_chunk_size: int = Field(default=800, ge=100, le=10_000)
    rag_chunk_overlap: int = Field(default=120, ge=0, le=2_000)
    rag_top_k: int = Field(default=4, ge=1, le=20)

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
