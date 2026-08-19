from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_port: int = 8000
    domain: str = "localhost:8000"
    debug_mode: bool = False  # was True — enable deliberately per-environment via .env

    # Auth
    api_key: str = "change-me"  # override in .env; required on all write + debug endpoints

    # Database (Postgres — source of truth)
    database_url: str = "postgresql+asyncpg://shortener:shortener@localhost:5432/shortener"

    # Redis (hot-path cache)
    redis_url: str = "redis://localhost:6379/0"

    # Rate limiting
    api_quota: int = 10
    rate_limit_window_seconds: int = 1800  # 30 minutes

    # URL shortening
    default_expiry_hours: int = 24
    short_code_length: int = 6


settings = Settings()
