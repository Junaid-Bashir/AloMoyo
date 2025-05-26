# app/core/config.py

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",          # ignore unexpected env vars
    )

    # Database & auth
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Base URL for links (verification, shares, etc)
    APP_BASE_URL: AnyHttpUrl

    # Email / SMTP
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_TLS: bool
    EMAIL_FROM: str

    # Redis cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASS: str = ""  # leave empty if no password

    # Backwards-compatible lowercase properties
    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY

    @property
    def algorithm(self) -> str:
        return self.ALGORITHM

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES


# Single global settings instance
settings = Settings()
