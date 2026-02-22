"""Tests for SDK configuration and core decorators."""

import pytest

from complianceagent.config import (
    ComplianceConfig,
    EnforcementMode,
    configure,
    get_config,
    reset_config,
)
from complianceagent.decorators import require_consent, audit_log, encrypt_pii
from complianceagent.exceptions import ConsentRequiredError
from complianceagent.validators import (
    ComplianceValidator,
    Regulation,
    ValidationSeverity,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class TestConfiguration:
    def setup_method(self):
        reset_config()

    def test_default_config(self):
        cfg = get_config()
        assert cfg.enforcement_mode == EnforcementMode.STRICT
        assert "GDPR" in cfg.enabled_regulations

    def test_configure_enforcement_mode(self):
        cfg = configure(enforcement_mode="warn")
        assert cfg.enforcement_mode == EnforcementMode.WARN

    def test_configure_regulations(self):
        cfg = configure(enabled_regulations=["HIPAA", "SOC2"])
        assert cfg.enabled_regulations == ["HIPAA", "SOC2"]
        assert cfg.is_regulation_enabled("HIPAA")
        assert not cfg.is_regulation_enabled("GDPR")

    def test_configure_api_connection(self):
        cfg = configure(api_url="https://api.example.com", api_key="test-key")
        assert cfg.complianceagent_api_url == "https://api.example.com"
        assert cfg.complianceagent_api_key == "test-key"

    def test_reset_config(self):
        configure(enforcement_mode="disabled")
        reset_config()
        cfg = get_config()
        assert cfg.enforcement_mode == EnforcementMode.STRICT


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


class TestRequireConsentDecorator:
    def setup_method(self):
        reset_config()

    def test_disabled_mode_skips_check(self):
        configure(enforcement_mode="disabled")

        @require_consent("marketing")
        def send_email(user_id: str, content: str) -> str:
            return "sent"

        assert send_email("user-1", "hello") == "sent"

    def test_strict_mode_blocks_without_consent(self):
        configure(enforcement_mode="strict")

        @require_consent("marketing")
        def send_email(user_id: str, content: str) -> str:
            return "sent"

        with pytest.raises(ConsentRequiredError):
            send_email("user-1", "hello")

    def test_consent_callback_allows(self):
        from complianceagent.config import ConsentConfig

        configure(
            enforcement_mode="strict",
            consent=ConsentConfig(
                consent_callback=lambda uid, ctype: True,
            ),
        )

        @require_consent("marketing")
        def send_email(user_id: str, content: str) -> str:
            return "sent"

        assert send_email("user-1", "hello") == "sent"

    def test_fail_silently(self):
        configure(enforcement_mode="strict")

        @require_consent("marketing", fail_silently=True)
        def send_email(user_id: str, content: str) -> str:
            return "sent"

        result = send_email("user-1", "hello")
        assert result is None


class TestAuditLogDecorator:
    def setup_method(self):
        reset_config()

    def test_audit_log_passes_through(self):
        configure(enforcement_mode="strict")

        @audit_log(action="data_access", regulation="GDPR")
        def read_data(user_id: str) -> dict:
            return {"data": "value"}

        result = read_data("user-1")
        assert result == {"data": "value"}

    def test_audit_log_disabled_mode(self):
        configure(enforcement_mode="disabled")

        @audit_log(action="data_access")
        def read_data() -> str:
            return "ok"

        assert read_data() == "ok"


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class TestValidator:
    def test_create_validator(self):
        v = ComplianceValidator()
        assert v is not None

    def test_regulation_enum(self):
        assert Regulation.GDPR.value == "GDPR"
        assert Regulation.HIPAA.value == "HIPAA"
        assert Regulation.PCI_DSS.value == "PCI-DSS"

    def test_severity_enum(self):
        assert ValidationSeverity.CRITICAL.value == "critical"
        assert ValidationSeverity.ERROR.value == "error"


# ---------------------------------------------------------------------------
# Imports / Public API
# ---------------------------------------------------------------------------


class TestPublicAPI:
    def test_top_level_imports(self):
        import complianceagent

        assert hasattr(complianceagent, "require_consent")
        assert hasattr(complianceagent, "encrypt_pii")
        assert hasattr(complianceagent, "audit_log")
        assert hasattr(complianceagent, "hipaa_phi")
        assert hasattr(complianceagent, "configure")
        assert hasattr(complianceagent, "ComplianceConfig")
        assert hasattr(complianceagent, "__version__")
        assert complianceagent.__version__ == "0.1.0"
