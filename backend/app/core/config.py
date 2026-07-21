from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    APP_NAME: str = "AIOps Platform"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    RATE_LIMIT_ENABLED: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    EMAIL_ENABLED: bool = False
    EMAIL_FROM: str = "noreply@aiops.local"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True

    # Auth rate limits (slowapi format)
    AUTH_RATE_LIMIT: str = "10/minute"

    # File uploads (Module 06)
    UPLOAD_DIR: str = "uploads"

    # AI (Module 07) — optional; stub responses when unset
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    AI_ENABLED: bool = False

    # Background jobs
    RETENTION_JOB_ENABLED: bool = True
    RETENTION_JOB_INTERVAL_HOURS: int = 6

    # Stripe billing (optional — demo upgrade when unset)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_PROFESSIONAL: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""

    # First-run admin (optional — only used when the database has zero users)
    BOOTSTRAP_ADMIN_EMAIL: str = ""
    BOOTSTRAP_ADMIN_PASSWORD: str = ""
    BOOTSTRAP_ADMIN_FIRST_NAME: str = "Admin"
    BOOTSTRAP_ADMIN_LAST_NAME: str = "User"
    BOOTSTRAP_ORG_NAME: str = "AIOps Organization"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_not_empty(cls, value: str) -> str:
        if not value or len(value) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters")
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def ai_available(self) -> bool:
        return bool(self.AI_ENABLED and self.OPENAI_API_KEY)

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST)

    @property
    def stripe_configured(self) -> bool:
        return bool(self.STRIPE_SECRET_KEY)

    def stripe_price_for_plan(self, plan: str) -> str:
        mapping = {
            "starter": self.STRIPE_PRICE_STARTER,
            "professional": self.STRIPE_PRICE_PROFESSIONAL,
            "enterprise": self.STRIPE_PRICE_ENTERPRISE,
        }
        return mapping.get(plan, "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
