"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "ComplianceAgent"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    enable_experimental: bool = Field(
        default=True,
        description="Enable experimental/stub service routes. Disable in production to reduce attack surface.",
    )

    # Security
    secret_key: str = Field(default="change-me-in-production-use-secrets-manager")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "complianceagent"
    postgres_password: str = "complianceagent"
    postgres_db: str = "complianceagent"

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field
    @property
    def database_url_sync(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None

    @computed_field
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Elasticsearch
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_user: str | None = None
    elasticsearch_password: str | None = None

    @computed_field
    @property
    def elasticsearch_url(self) -> str:
        if self.elasticsearch_user and self.elasticsearch_password:
            return f"http://{self.elasticsearch_user}:{self.elasticsearch_password}@{self.elasticsearch_host}:{self.elasticsearch_port}"
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"

    # S3 / MinIO
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_regulations: str = "regulations"
    s3_bucket_evidence: str = "compliance-evidence"
    s3_region: str = "us-east-1"

    # Celery
    celery_broker_url: str | None = None

    @computed_field
    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    # GitHub Copilot SDK
    copilot_api_key: str | None = None
    copilot_default_model: str = "claude-sonnet-4-20250514"
    copilot_timeout_seconds: int = 120
    copilot_max_retries: int = 3
    copilot_retry_min_wait: int = 4
    copilot_retry_max_wait: int = 60

    # Database Connection Pool
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # 30 minutes
    db_pool_pre_ping: bool = True

    # Monitoring
    monitoring_interval_hours: int = 6
    max_concurrent_crawlers: int = 5

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_in_debug: bool = False  # Enable rate limiting even in debug mode

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
