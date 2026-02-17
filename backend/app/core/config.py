"""
Application configuration loaded from environment variables.

Usage:
    from app.core.config import settings
    print(settings.GROQ_API_KEY)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object – values are read from the .env file
    located two levels up from this file (i.e. the project root)."""

    GROQ_API_KEY: str
    PINECONE_API_KEY: str
    PINECONE_ENV: str
    PINECONE_INDEX_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Global singleton – import this wherever you need config values.
settings = Settings()
