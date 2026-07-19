"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Supports two modes:
    - Component vars (POSTGRES_HOST, REDIS_HOST, etc.) -> URLs are computed
    - Direct URL overrides (DATABASE_URL, REDIS_URL) -> takes precedence when set

    Production validators enforce non-default secrets and required API keys.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -- Application -----------------------------------------------------------
    app_name: str = "ComplianceAgent"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    enable_experimental: bool = Field(
        default=False,
        description="Enable experimental/stub service routes. Set to true in development via .env.",
    )

    # -- Security --------------------------------------------------------------
    secret_key: str = Field(default="change-me-in-production-use-secrets-manager")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # -- Database --------------------------------------------------------------
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "complianceagent"
    postgres_password: str = "complianceagent"
    postgres_db: str = "complianceagent"
    postgres_sslmode: str = Field(
        default="prefer",
        description="PostgreSQL sslmode. Use 'require' in production.",
    )

    # Direct override -- ECS/Secrets Manager injects this fully-formed
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")

    @computed_field  # type: ignore[prop-decorator]  # mypy limitation: stacked decorators on @property (python/mypy#14461)
    @property
    def database_url(self) -> str:
        """Async database URL. Prefers DATABASE_URL env override if set."""
        if self.database_url_override:
            url = self.database_url_override
            # Ensure asyncpg driver
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        ssl_param = f"?sslmode={self.postgres_sslmode}" if self.postgres_sslmode != "prefer" else ""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )

    @computed_field  # type: ignore[prop-decorator]  # mypy limitation: stacked decorators on @property (python/mypy#14461)
    @property
    def database_url_sync(self) -> str:
        """Sync database URL (for Alembic migrations)."""
        if self.database_url_override:
            url = self.database_url_override
            # Ensure psycopg2/sync driver
            if "+asyncpg" in url:
                url = url.replace("+asyncpg", "")
            elif url.startswith("postgresql+"):
                url = "postgresql://" + url.split("://", 1)[1]
            return url
        ssl_param = f"?sslmode={self.postgres_sslmode}" if self.postgres_sslmode != "prefer" else ""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}{ssl_param}"
        )

    # -- Redis -----------------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_tls: bool = Field(default=False, description="Use TLS (rediss://) for Redis connections.")

    # Direct override -- ECS/Secrets Manager injects this fully-formed
    redis_url_override: str | None = Field(default=None, alias="REDIS_URL")

    @computed_field  # type: ignore[prop-decorator]  # mypy limitation: stacked decorators on @property (python/mypy#14461)
    @property
    def redis_url(self) -> str:
        """Redis URL. Prefers REDIS_URL env override if set."""
        if self.redis_url_override:
            return self.redis_url_override
        scheme = "rediss" if self.redis_tls else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{scheme}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # -- Elasticsearch / OpenSearch --------------------------------------------
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_user: str | None = None
    elasticsearch_password: str | None = None
    elasticsearch_use_ssl: bool = Field(default=False, description="Use HTTPS for ES connections.")

    @computed_field  # type: ignore[prop-decorator]  # mypy limitation: stacked decorators on @property (python/mypy#14461)
    @property
    def elasticsearch_url(self) -> str:
        scheme = "https" if self.elasticsearch_use_ssl else "http"
        if self.elasticsearch_user and self.elasticsearch_password:
            return (
                f"{scheme}://{self.elasticsearch_user}:{self.elasticsearch_password}"
                f"@{self.elasticsearch_host}:{self.elasticsearch_port}"
            )
        return f"{scheme}://{self.elasticsearch_host}:{self.elasticsearch_port}"

    # -- HIPAA Encryption (PHI Storage) ----------------------------------------
    kms_key_id: str = Field(default="", description="AWS KMS key ID for envelope encryption of PHI")
    hipaa_encryption_enabled: bool = False
    phi_storage_bucket: str = ""

    # -- S3 / MinIO ------------------------------------------------------------
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_regulations: str = "regulations"
    s3_bucket_evidence: str = "compliance-evidence"
    s3_region: str = "us-east-1"

    # -- AWS -------------------------------------------------------------------
    aws_region: str = "us-east-1"

    # -- Celery ----------------------------------------------------------------
    celery_broker_url: str | None = None

    @computed_field  # type: ignore[prop-decorator]  # mypy limitation: stacked decorators on @property (python/mypy#14461)
    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    # -- GitHub Copilot SDK ----------------------------------------------------
    copilot_api_key: str | None = None
    copilot_default_model: str = "claude-sonnet-4-20250514"
    copilot_timeout_seconds: int = 120
    copilot_max_retries: int = 3
    copilot_retry_min_wait: int = 4
    copilot_retry_max_wait: int = 60

    # -- GitHub App Integration ------------------------------------------------
    github_app_id: str = ""
    github_app_private_key: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_webhook_secret: str = ""

    # -- Stripe Billing --------------------------------------------------------
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # -- Object storage for avatars --------------------------------------------
    avatar_bucket: str = "avatars"

    # -- Email / SMTP ----------------------------------------------------------
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_tls: bool | None = Field(
        default=None,
        description="Alias for smtp_use_tls (used in .env.production.example).",
    )
    smtp_from_email: str = "noreply@complianceagent.io"
    email_api_endpoint: str = ""
    email_api_key: str = ""

    # -- Sentry ----------------------------------------------------------------
    sentry_dsn: str = ""
    sentry_environment: str = ""
    sentry_traces_sample_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sentry performance traces sample rate (0.0-1.0).",
    )

    # -- URLs & Routing --------------------------------------------------------
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Backend's own public base URL (for webhooks, emails, etc.).",
    )
    next_public_api_url: str = "http://localhost:8000/api/v1"
    next_public_app_url: str = "http://localhost:3000"
    auth_cookie_domain: str | None = None

    # -- CORS & Allowed Hosts --------------------------------------------------
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"],
        description=(
            "Allowed CORS origins. Override via CORS_ORIGINS env var as a "
            "JSON array, e.g. '[\"https://app.example.com\"]'."
        ),
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Comma-separated or JSON list of allowed Host headers.",
    )

    # -- Proxy Trust -----------------------------------------------------------
    forwarded_allow_ips: str = Field(
        default="127.0.0.1",
        description="IPs allowed to set X-Forwarded-* headers. Use '*' behind trusted LB.",
    )
    trusted_proxies: int = Field(
        default=0,
        description="Number of trusted proxy hops (for X-Forwarded-For depth).",
    )

    # -- Feature Flags ---------------------------------------------------------
    feature_github_app: bool = False
    feature_stripe_billing: bool = False
    feature_elasticsearch: bool = False
    feature_email_notifications: bool = False
    feature_multi_tenancy: bool = False

    # -- Database Connection Pool ----------------------------------------------
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # 30 minutes
    db_pool_pre_ping: bool = True

    # -- Monitoring ------------------------------------------------------------
    monitoring_interval_hours: int = 6
    max_concurrent_crawlers: int = 5

    # -- Rate Limiting ---------------------------------------------------------
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_in_debug: bool = False  # Enable rate limiting even in debug mode

    # ==========================================================================
    # Validators
    # ==========================================================================

    @model_validator(mode="after")
    def _resolve_smtp_tls_alias(self) -> Settings:
        """Allow SMTP_TLS env var as alias for smtp_use_tls."""
        if self.smtp_tls is not None:
            object.__setattr__(self, "smtp_use_tls", self.smtp_tls)
        return self

    @model_validator(mode="after")
    def _resolve_sentry_environment(self) -> Settings:
        """Default sentry_environment to environment if not explicitly set."""
        if not self.sentry_environment:
            object.__setattr__(self, "sentry_environment", self.environment)
        return self

    @model_validator(mode="after")
    def _validate_cors_origins_in_production(self) -> Settings:
        _dev_origins = {"http://localhost:3000", "http://localhost:8000"}
        if self.environment == "production" and set(self.cors_origins) == _dev_origins:
            import warnings

            warnings.warn(
                "CORS_ORIGINS still contains only localhost defaults in production. "
                "Set CORS_ORIGINS to your actual frontend domain(s).",
                stacklevel=1,
            )
        return self

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> Settings:
        """Fail fast if critical secrets are missing/default in production/staging."""
        if self.environment not in ("production", "staging"):
            return self

        _default_secret = "change-me-in-production-use-secrets-manager"
        if self.secret_key == _default_secret:
            msg = (
                f"SECRET_KEY must be changed from the default value "
                f"when ENVIRONMENT={self.environment!r}. "
                f'Generate with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
            raise ValueError(msg)

        if self.postgres_password == "complianceagent" and not self.database_url_override:
            msg = (
                "POSTGRES_PASSWORD is still the development default. "
                "Set a strong password or provide DATABASE_URL directly."
            )
            raise ValueError(msg)

        if not self.next_public_app_url.startswith("https://"):
            raise ValueError("NEXT_PUBLIC_APP_URL must use HTTPS in deployed environments.")
        if not self.next_public_api_url.startswith("https://"):
            raise ValueError("NEXT_PUBLIC_API_URL must use HTTPS in deployed environments.")
        if "*" in self.cors_origins or any(
            not origin.startswith("https://") for origin in self.cors_origins
        ):
            raise ValueError(
                "CORS_ORIGINS must contain only explicit HTTPS origins in deployed environments."
            )
        if "*" in self.allowed_hosts:
            raise ValueError("ALLOWED_HOSTS must not contain '*' in deployed environments.")
        if not self.smtp_host and not self.email_api_endpoint:
            raise ValueError("Configure SMTP_HOST or EMAIL_API_ENDPOINT for transactional email.")
        api_host = urlparse(self.next_public_api_url).hostname
        app_host = urlparse(self.next_public_app_url).hostname
        if api_host != app_host and not self.auth_cookie_domain:
            raise ValueError(
                "AUTH_COOKIE_DOMAIN is required when the API and frontend use different hostnames."
            )
        if self.stripe_api_key and not self.stripe_webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET is required when STRIPE_API_KEY is configured.")
        if self.github_app_id and (
            not self.github_app_private_key or not self.github_webhook_secret
        ):
            raise ValueError(
                "GITHUB_APP_PRIVATE_KEY and GITHUB_WEBHOOK_SECRET are required "
                "when GITHUB_APP_ID is configured."
            )

        return self

    @model_validator(mode="after")
    def _validate_production_tls(self) -> Settings:
        """Warn if production DB/Redis connections are not using TLS."""
        if self.environment != "production":
            return self

        import warnings

        if self.postgres_sslmode in ("disable", "prefer") and not self.database_url_override:
            warnings.warn(
                "POSTGRES_SSLMODE should be 'require' or stricter in production. "
                "Set POSTGRES_SSLMODE=require.",
                stacklevel=1,
            )

        if not self.redis_tls and not self.redis_url_override:
            warnings.warn(
                "REDIS_TLS is false in production. Set REDIS_TLS=true for "
                "encrypted connections to ElastiCache.",
                stacklevel=1,
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
