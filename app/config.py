from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from pydantic import field_validator
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

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            return v

        # Normalize driver scheme
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        try:
            parsed = urlparse(v)
            query_params = dict(parse_qsl(parsed.query))
            sanitized_query = {}

            # asyncpg accepts 'ssl' instead of 'sslmode'
            ssl_val = query_params.pop("ssl", None) or query_params.pop("sslmode", None)
            if ssl_val and ssl_val.lower() in ("require", "prefer", "allow", "disable"):
                sanitized_query["ssl"] = ssl_val.lower()
            elif ssl_val and ssl_val.lower() in ("true", "1"):
                sanitized_query["ssl"] = "require"

            allowed_params = {
                "ssl",
                "timeout",
                "command_timeout",
                "statement_cache_size",
                "max_cached_statement_lifetime",
                "max_cacheable_statement_size",
                "server_settings",
            }
            for k, val in query_params.items():
                if k in allowed_params:
                    sanitized_query[k] = val

            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                urlencode(sanitized_query),
                parsed.fragment,
            ))
        except Exception:
            return v



settings = Settings()

