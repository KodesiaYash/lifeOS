"""
Application configuration via Pydantic Settings.
All config is loaded from environment variables or .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "ai-life-os"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://lifeos:lifeos@localhost:5432/lifeos"

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Object Storage ---
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "lifeos"

    # --- LLM / AI ---
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # --- Auth ---
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # --- Encryption ---
    ENCRYPTION_KEY: str = "change-me-to-a-32-byte-base64-key"

    # --- Scheduling ---
    SCHEDULER_ENABLED: bool = True
    WORKER_ENABLED: bool = True

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
