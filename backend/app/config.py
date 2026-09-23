"""
app/config.py
-------------
Centralised application settings loaded from environment variables / .env file.
Uses pydantic-settings v2 for validation and type coercion.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    app_env: str = "development"
    secret_key: str = "dev-secret-change-in-production-must-be-32-chars-min"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    database_url: str = "sqlite:///./credishield.db"

    # ---------------------------------------------------------------------------
    # CORS – comma-separated list of allowed origins stored as a single string
    # so it can be set via a single env var.
    # ---------------------------------------------------------------------------
    cors_origins: str = "http://localhost:5173"

    # ---------------------------------------------------------------------------
    # Rate limiting (slowapi format, e.g. "10/minute")
    # ---------------------------------------------------------------------------
    rate_limit: str = "10/minute"

    # ---------------------------------------------------------------------------
    # ML artefact paths (relative to the backend/ directory)
    # ---------------------------------------------------------------------------
    model_path: str = "../ml/artifacts/model_v1.joblib"
    model_meta_path: str = "../ml/artifacts/model_v1_meta.json"
    policy_path: str = "./policy/thresholds.json"

    # pydantic-settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------------------------------------------------------------------------
    # Computed helpers
    # ---------------------------------------------------------------------------
    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a Python list, split on commas."""
        return [o.strip() for o in self.cors_origins.split(",")]


# Single application-wide settings instance imported everywhere
settings = Settings()
