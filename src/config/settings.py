from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Clinic Booking API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Authentication (Level 2)
    API_KEY: str = "test-api-key"

    # PostgreSQL Database URL (SQLAlchemy 2.0 with psycopg)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/clinic_db"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
