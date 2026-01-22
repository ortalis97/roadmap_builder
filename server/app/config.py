"""Application configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    port: int = 8000
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Database
    mongodb_uri: str = ""

    # Firebase Auth - supports either file path or JSON string
    google_application_credentials: str = ""  # Path to service account JSON file
    google_application_credentials_json: str = ""  # Service account JSON as string

    # AI
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
