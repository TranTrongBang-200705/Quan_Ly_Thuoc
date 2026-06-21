from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DrugDisease FastAPI Backend"
    environment: str = "development"
    database_url: str | None = None
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_server: str | None = None
    db_server_fallbacks: str = ""
    db_name: str = "DataThuoc"
    db_trusted_connection: str = "yes"
    db_encrypt: str = "no"
    db_trust_server_certificate: str = "yes"
    db_connection_timeout: int = 5
    db_username: str | None = None
    db_password: str | None = None
    jwt_secret_key: str = "CHANGE_THIS_SECRET_FOR_DEVELOPMENT_ONLY"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    ai_service_base_url: str = "http://localhost:8001"
    ai_service_url: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def db_server_list(self) -> list[str]:
        servers: list[str] = []

        for server in [self.db_server, *self.db_server_fallbacks.split(",")]:
            server = (server or "").strip()

            if server and server not in servers:
                servers.append(server)

        return servers

    def build_odbc_connection_string(self, server: str) -> str:
        username = (self.db_username or "").strip()
        password = (self.db_password or "").strip()
        parts = [
            f"Driver={{{self.db_driver.strip()}}}",
            f"Server={server}",
            f"Database={self.db_name.strip()}",
        ]

        if username:
            parts.extend([f"UID={username}", f"PWD={password}"])
        else:
            parts.append(f"Trusted_Connection={self.db_trusted_connection.strip()}")

        parts.extend([
            f"Encrypt={self.db_encrypt.strip()}",
            f"TrustServerCertificate={self.db_trust_server_certificate.strip()}",
        ])

        if self.db_connection_timeout > 0:
            parts.append(f"Connection Timeout={self.db_connection_timeout}")

        return ";".join(parts) + ";"

    def build_sqlalchemy_url(self, server: str) -> str:
        odbc_connect = quote_plus(self.build_odbc_connection_string(server))
        return f"mssql+pyodbc:///?odbc_connect={odbc_connect}"

    @property
    def sqlalchemy_database_urls(self) -> list[tuple[str, str]]:
        urls = [(server, self.build_sqlalchemy_url(server)) for server in self.db_server_list]

        if urls:
            return urls

        if self.database_url:
            return [("DATABASE_URL", self.database_url)]

        raise ValueError("Missing SQL Server configuration. Set DB_SERVER and DB_NAME in .env.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
