"""Tests for app.core.config Settings — production contract coherence."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError


# Clear settings cache between tests
@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _make_env(**overrides: str) -> dict[str, str]:
    """Build a minimal valid development env dict."""
    base = {
        "ENVIRONMENT": "development",
        "SECRET_KEY": "test-secret-key-not-default",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
        "POSTGRES_DB": "testdb",
        "REDIS_HOST": "localhost",
    }
    base.update(overrides)
    if base["ENVIRONMENT"] in {"staging", "production"}:
        base.setdefault("NEXT_PUBLIC_APP_URL", "https://app.example.com")
        base.setdefault("NEXT_PUBLIC_API_URL", "https://api.example.com/api/v1")
        base.setdefault("CORS_ORIGINS", '["https://app.example.com"]')
        base.setdefault("ALLOWED_HOSTS", '["api.example.com","app.example.com"]')
        base.setdefault("SMTP_HOST", "smtp.example.com")
        base.setdefault("AUTH_COOKIE_DOMAIN", ".example.com")
    return base


class TestDatabaseURL:
    """DATABASE_URL computed and override behavior."""

    def test_computed_from_components(self):
        env = _make_env()
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.database_url == "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
            assert s.database_url_sync == "postgresql://testuser:testpass@localhost:5432/testdb"

    def test_sslmode_appended(self):
        env = _make_env(POSTGRES_SSLMODE="require")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.database_url.endswith("?sslmode=require")
            assert s.database_url_sync.endswith("?sslmode=require")

    def test_direct_override(self):
        env = _make_env(DATABASE_URL="postgresql://direct:pass@rds:5432/mydb")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            # Async URL adds asyncpg driver
            assert s.database_url == "postgresql+asyncpg://direct:pass@rds:5432/mydb"
            # Sync URL keeps standard driver
            assert s.database_url_sync == "postgresql://direct:pass@rds:5432/mydb"

    def test_direct_override_with_asyncpg(self):
        env = _make_env(DATABASE_URL="postgresql+asyncpg://direct:pass@rds:5432/mydb")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.database_url == "postgresql+asyncpg://direct:pass@rds:5432/mydb"
            assert s.database_url_sync == "postgresql://direct:pass@rds:5432/mydb"


class TestRedisURL:
    """REDIS_URL computed and override behavior."""

    def test_basic_no_auth(self):
        env = _make_env()
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.redis_url == "redis://localhost:6379/0"

    def test_with_password(self):
        env = _make_env(REDIS_PASSWORD="secret123")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.redis_url == "redis://:secret123@localhost:6379/0"

    def test_tls_scheme(self):
        env = _make_env(REDIS_TLS="true", REDIS_PASSWORD="secret")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.redis_url.startswith("rediss://")
            assert ":secret@" in s.redis_url

    def test_direct_override(self):
        env = _make_env(REDIS_URL="rediss://:tok@elasticache:6379/1")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.redis_url == "rediss://:tok@elasticache:6379/1"


class TestElasticsearchURL:
    """Elasticsearch URL computed with SSL flag."""

    def test_http_default(self):
        env = _make_env()
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.elasticsearch_url == "http://localhost:9200"

    def test_https_with_auth(self):
        env = _make_env(
            ELASTICSEARCH_USE_SSL="true",
            ELASTICSEARCH_USER="admin",
            ELASTICSEARCH_PASSWORD="pass",
            ELASTICSEARCH_PORT="443",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.elasticsearch_url == "https://admin:pass@localhost:443"


class TestProductionValidators:
    """Fail-fast validators for production/staging."""

    def test_rejects_default_secret_key_in_production(self):
        env = _make_env(
            ENVIRONMENT="production",
            SECRET_KEY="change-me-in-production-use-secrets-manager",
            POSTGRES_PASSWORD="realpass",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError, match="SECRET_KEY must be changed"):
                Settings(_env_file=None)

    def test_rejects_default_db_password_in_production(self):
        env = _make_env(
            ENVIRONMENT="production",
            SECRET_KEY="a-real-secret-key-for-production",
            POSTGRES_PASSWORD="complianceagent",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError, match="POSTGRES_PASSWORD"):
                Settings(_env_file=None)

    def test_allows_default_db_password_with_database_url_override(self):
        env = _make_env(
            ENVIRONMENT="production",
            SECRET_KEY="a-real-secret-key-for-production",
            POSTGRES_PASSWORD="complianceagent",
            DATABASE_URL="postgresql://real:real@rds:5432/prod",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.environment == "production"

    def test_passes_in_test_environment(self):
        env = _make_env(ENVIRONMENT="test")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.environment == "test"

    def test_passes_in_development(self):
        env = _make_env(
            ENVIRONMENT="development",
            SECRET_KEY="change-me-in-production-use-secrets-manager",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.environment == "development"

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("NEXT_PUBLIC_APP_URL", "http://localhost:3000", "NEXT_PUBLIC_APP_URL"),
            ("NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1", "NEXT_PUBLIC_API_URL"),
            ("CORS_ORIGINS", '["http://localhost:3000"]', "CORS_ORIGINS"),
            ("ALLOWED_HOSTS", '["*"]', "ALLOWED_HOSTS"),
            ("SMTP_HOST", "", "transactional email"),
        ],
    )
    def test_rejects_unsafe_deployed_contract(self, field, value, message):
        env = _make_env(ENVIRONMENT="production", **{field: value})
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.raises(ValidationError, match=message):
                Settings(_env_file=None)


class TestProductionTLSWarnings:
    """TLS warnings in production."""

    def test_warns_on_no_ssl_mode(self):
        env = _make_env(
            ENVIRONMENT="production",
            SECRET_KEY="prod-secret",
            POSTGRES_PASSWORD="realpass",
            POSTGRES_SSLMODE="prefer",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.warns(UserWarning, match="POSTGRES_SSLMODE"):
                Settings(_env_file=None)

    def test_warns_on_no_redis_tls(self):
        env = _make_env(
            ENVIRONMENT="production",
            SECRET_KEY="prod-secret",
            POSTGRES_PASSWORD="realpass",
            POSTGRES_SSLMODE="require",
            REDIS_TLS="false",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            with pytest.warns(UserWarning, match="REDIS_TLS"):
                Settings(_env_file=None)

    def test_no_warnings_with_tls_enabled(self):
        env = _make_env(
            ENVIRONMENT="production",
            SECRET_KEY="prod-secret",
            POSTGRES_PASSWORD="realpass",
            POSTGRES_SSLMODE="require",
            REDIS_TLS="true",
            CORS_ORIGINS='["https://app.example.com"]',
        )
        with patch.dict(os.environ, env, clear=True):
            import warnings

            from app.core.config import Settings

            with warnings.catch_warnings():
                warnings.simplefilter("error")
                # Should not emit any warnings (TLS or CORS)
                Settings(_env_file=None)


class TestFeatureFlags:
    """Feature flags loaded from env."""

    def test_default_flags_are_false(self):
        env = _make_env()
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.feature_github_app is False
            assert s.feature_stripe_billing is False
            assert s.feature_elasticsearch is False
            assert s.feature_email_notifications is False
            assert s.feature_multi_tenancy is False

    def test_flags_can_be_enabled(self):
        env = _make_env(
            FEATURE_GITHUB_APP="true",
            FEATURE_STRIPE_BILLING="true",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.feature_github_app is True
            assert s.feature_stripe_billing is True


class TestNewFields:
    """Newly added fields are present and work correctly."""

    def test_sentry_fields(self):
        env = _make_env(
            SENTRY_DSN="https://key@sentry.io/123",
            SENTRY_TRACES_SAMPLE_RATE="0.5",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.sentry_dsn == "https://key@sentry.io/123"
            assert s.sentry_traces_sample_rate == 0.5
            # Default environment resolution
            assert s.sentry_environment == "development"

    def test_sentry_environment_override(self):
        env = _make_env(
            SENTRY_ENVIRONMENT="custom-env",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.sentry_environment == "custom-env"

    def test_github_app_fields(self):
        env = _make_env(
            GITHUB_APP_ID="12345",
            GITHUB_CLIENT_ID="Iv1.abc",
            GITHUB_CLIENT_SECRET="sec",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.github_app_id == "12345"
            assert s.github_client_id == "Iv1.abc"
            assert s.github_client_secret == "sec"

    def test_stripe_publishable_key(self):
        env = _make_env(STRIPE_PUBLISHABLE_KEY="pk_test_abc")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.stripe_publishable_key == "pk_test_abc"

    def test_proxy_trust_fields(self):
        env = _make_env(FORWARDED_ALLOW_IPS="*", TRUSTED_PROXIES="2")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.forwarded_allow_ips == "*"
            assert s.trusted_proxies == 2

    def test_allowed_hosts(self):
        env = _make_env(ALLOWED_HOSTS='["api.example.com","app.example.com"]')
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.allowed_hosts == ["api.example.com", "app.example.com"]

    def test_smtp_tls_alias(self):
        env = _make_env(SMTP_TLS="false")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.smtp_use_tls is False

    def test_api_base_url(self):
        env = _make_env(API_BASE_URL="https://api.complianceagent.ai")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.api_base_url == "https://api.complianceagent.ai"

    def test_aws_region(self):
        env = _make_env(AWS_REGION="eu-west-1")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.aws_region == "eu-west-1"


class TestPreservedFields:
    """Existing fields that must not be removed."""

    def test_stripe_fields_preserved(self):
        env = _make_env(
            STRIPE_API_KEY="sk_test_abc",
            STRIPE_WEBHOOK_SECRET="whsec_abc",
        )
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.stripe_api_key == "sk_test_abc"
            assert s.stripe_webhook_secret == "whsec_abc"

    def test_avatar_bucket_preserved(self):
        env = _make_env(AVATAR_BUCKET="my-avatars")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.avatar_bucket == "my-avatars"

    def test_celery_broker_defaults_to_redis(self):
        env = _make_env()
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.celery_broker == s.redis_url

    def test_celery_broker_override(self):
        env = _make_env(CELERY_BROKER_URL="redis://broker:6379/1")
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings

            s = Settings(_env_file=None)
            assert s.celery_broker == "redis://broker:6379/1"
