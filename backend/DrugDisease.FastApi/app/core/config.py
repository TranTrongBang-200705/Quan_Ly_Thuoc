from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DrugDisease FastAPI Backend"
    environment: str = "development"
    database_url: str
    jwt_secret_key: str = "CHANGE_THIS_SECRET_FOR_DEVELOPMENT_ONLY"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    ai_service_base_url: str = "http://localhost:8001"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
