"""Configuration for ComplianceAgent SDK."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class EnforcementMode(str, Enum):
    """How compliance violations are handled."""
    STRICT = "strict"        # Raise exceptions on violations
    WARN = "warn"           # Log warnings but continue
    AUDIT_ONLY = "audit_only"  # Only log for audit, no enforcement
    DISABLED = "disabled"    # No compliance checks


class EncryptionProvider(str, Enum):
    """Supported encryption providers."""
    AES256_GCM = "aes256_gcm"
    FERNET = "fernet"
    AWS_KMS = "aws_kms"
    GCP_KMS = "gcp_kms"
    AZURE_KEY_VAULT = "azure_key_vault"
    CUSTOM = "custom"


@dataclass
class ConsentConfig:
    """Configuration for consent management."""
    consent_service_url: str | None = None
    consent_service_api_key: str | None = None
    consent_cache_ttl_seconds: int = 300
    required_consent_types: list[str] = field(default_factory=lambda: ["marketing", "analytics", "personalization"])
    consent_callback: Callable[[str, str], bool] | None = None  # user_id, consent_type -> has_consent


@dataclass
class EncryptionConfig:
    """Configuration for encryption."""
    provider: EncryptionProvider = EncryptionProvider.FERNET
    encryption_key: str | None = None
    key_id: str | None = None
    kms_endpoint: str | None = None
    custom_encrypt_fn: Callable[[bytes], bytes] | None = None
    custom_decrypt_fn: Callable[[bytes], bytes] | None = None
    pii_fields: list[str] = field(default_factory=lambda: [
        "email", "phone", "ssn", "social_security_number", 
        "address", "name", "first_name", "last_name",
        "date_of_birth", "dob", "password", "credit_card",
    ])


@dataclass
class AuditConfig:
    """Configuration for audit logging."""
    enabled: bool = True
    audit_service_url: str | None = None
    audit_service_api_key: str | None = None
    log_to_file: bool = False
    log_file_path: str = "/var/log/complianceagent/audit.log"
    log_to_stdout: bool = True
    include_request_body: bool = False
    include_response_body: bool = False
    sensitive_fields_to_mask: list[str] = field(default_factory=lambda: [
        "password", "token", "api_key", "secret", "credit_card",
    ])
    custom_logger: Callable[[dict], None] | None = None


@dataclass
class AccessControlConfig:
    """Configuration for access control."""
    rbac_enabled: bool = True
    role_provider: Callable[[str], list[str]] | None = None  # user_id -> roles
    permission_provider: Callable[[str, str], bool] | None = None  # user_id, permission -> allowed
    default_deny: bool = True


@dataclass
class ComplianceConfig:
    """Main configuration for ComplianceAgent SDK."""
    
    # General settings
    enforcement_mode: EnforcementMode = EnforcementMode.STRICT
    enabled_regulations: list[str] = field(default_factory=lambda: ["GDPR", "CCPA", "HIPAA", "PCI-DSS"])
    
    # Service connection
    complianceagent_api_url: str | None = None
    complianceagent_api_key: str | None = None
    
    # Feature configs
    consent: ConsentConfig = field(default_factory=ConsentConfig)
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    access_control: AccessControlConfig = field(default_factory=AccessControlConfig)
    
    # HIPAA settings
    hipaa_minimum_necessary: bool = True
    hipaa_audit_all_phi_access: bool = True
    
    # PCI-DSS settings
    pci_mask_pan: bool = True
    pci_never_store_cvv: bool = True
    pci_encrypt_cardholder_data: bool = True
    
    # Data retention
    default_retention_days: int = 365
    retention_policies: dict[str, int] = field(default_factory=dict)
    
    # Callbacks
    on_violation: Callable[[str, dict], None] | None = None
    on_audit_event: Callable[[dict], None] | None = None
    
    def is_regulation_enabled(self, regulation: str) -> bool:
        """Check if a regulation is enabled."""
        return regulation.upper() in [r.upper() for r in self.enabled_regulations]


# Global configuration instance
_config: ComplianceConfig | None = None


def configure(
    enforcement_mode: EnforcementMode | str | None = None,
    enabled_regulations: list[str] | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
    consent: ConsentConfig | dict | None = None,
    encryption: EncryptionConfig | dict | None = None,
    audit: AuditConfig | dict | None = None,
    access_control: AccessControlConfig | dict | None = None,
    **kwargs: Any,
) -> ComplianceConfig:
    """Configure the ComplianceAgent SDK.
    
    Args:
        enforcement_mode: How violations are handled (strict, warn, audit_only, disabled)
        enabled_regulations: List of regulations to enforce (GDPR, CCPA, HIPAA, PCI-DSS)
        api_url: ComplianceAgent API URL for reporting
        api_key: ComplianceAgent API key
        consent: Consent management configuration
        encryption: Encryption configuration
        audit: Audit logging configuration
        access_control: Access control configuration
        **kwargs: Additional configuration options
    
    Returns:
        The configured ComplianceConfig instance
    
    Example:
        configure(
            enforcement_mode="strict",
            enabled_regulations=["GDPR", "HIPAA"],
            api_url="https://api.complianceagent.io",
            api_key="your-api-key",
        )
    """
    global _config
    
    config = ComplianceConfig()
    
    if enforcement_mode:
        if isinstance(enforcement_mode, str):
            enforcement_mode = EnforcementMode(enforcement_mode)
        config.enforcement_mode = enforcement_mode
    
    if enabled_regulations:
        config.enabled_regulations = enabled_regulations
    
    if api_url:
        config.complianceagent_api_url = api_url
    
    if api_key:
        config.complianceagent_api_key = api_key
    
    if consent:
        if isinstance(consent, dict):
            config.consent = ConsentConfig(**consent)
        else:
            config.consent = consent
    
    if encryption:
        if isinstance(encryption, dict):
            config.encryption = EncryptionConfig(**encryption)
        else:
            config.encryption = encryption
    
    if audit:
        if isinstance(audit, dict):
            config.audit = AuditConfig(**audit)
        else:
            config.audit = audit
    
    if access_control:
        if isinstance(access_control, dict):
            config.access_control = AccessControlConfig(**access_control)
        else:
            config.access_control = access_control
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    _config = config
    return config


def get_config() -> ComplianceConfig:
    """Get the current configuration.
    
    Returns the global configuration, creating a default one if not configured.
    """
    global _config
    if _config is None:
        _config = ComplianceConfig()
    return _config


def reset_config() -> None:
    """Reset configuration to defaults. Useful for testing."""
    global _config
    _config = None
