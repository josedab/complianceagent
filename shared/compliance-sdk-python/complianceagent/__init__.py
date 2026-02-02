"""ComplianceAgent SDK - Compliance-as-Code for Python.

This SDK provides decorators and utilities for implementing compliance
requirements directly in your Python code.

Example usage:
    from complianceagent import require_consent, encrypt_pii, audit_log, hipaa_phi
    
    @require_consent("marketing")
    def send_marketing_email(user_id: str, content: str):
        # Consent is automatically verified before execution
        pass
    
    @encrypt_pii(fields=["email", "phone"])
    def store_user_data(user_id: str, email: str, name: str):
        # PII fields are automatically encrypted
        pass
    
    @audit_log(action="data_access", regulation="GDPR")
    def access_personal_data(user_id: str):
        # Access is automatically logged for audit trail
        pass
    
    @hipaa_phi(purpose="treatment")
    def process_medical_record(patient_id: str, diagnosis: str):
        # PHI handling safeguards are enforced
        pass
"""

from complianceagent.decorators import (
    require_consent,
    encrypt_pii,
    audit_log,
    hipaa_phi,
    pci_cardholder,
    gdpr_compliant,
    data_retention,
    access_control,
    breach_detection,
    privacy_by_design,
)

from complianceagent.validators import (
    ComplianceValidator,
    ValidationResult,
    ValidationViolation,
    ValidationSeverity,
    Regulation,
    validate_email,
    validate_phone,
    mask_pii,
    anonymize_data,
)

from complianceagent.audit import (
    AuditLogger,
    AuditEntry,
    AuditAction,
    AuditSeverity,
    get_audit_logger,
)

from complianceagent.config import (
    ComplianceConfig,
    EnforcementMode,
    EncryptionProvider,
    configure,
    get_config,
)

from complianceagent.exceptions import (
    ComplianceError,
    ConsentRequiredError,
    EncryptionError,
    AccessDeniedError,
    ValidationError,
    PHIViolationError,
    PCIViolationError,
    DataRetentionError,
)

__version__ = "0.1.0"

__all__ = [
    # Decorators
    "require_consent",
    "encrypt_pii",
    "audit_log",
    "hipaa_phi",
    "pci_cardholder",
    "gdpr_compliant",
    "data_retention",
    "access_control",
    "breach_detection",
    "privacy_by_design",
    # Validators
    "ComplianceValidator",
    "ValidationResult",
    "ValidationViolation",
    "ValidationSeverity",
    "Regulation",
    "validate_email",
    "validate_phone",
    "mask_pii",
    "anonymize_data",
    # Audit
    "AuditLogger",
    "AuditEntry",
    "AuditAction",
    "AuditSeverity",
    "get_audit_logger",
    # Config
    "ComplianceConfig",
    "EnforcementMode",
    "EncryptionProvider",
    "configure",
    "get_config",
    # Exceptions
    "ComplianceError",
    "ConsentRequiredError",
    "EncryptionError",
    "AccessDeniedError",
    "ValidationError",
    "PHIViolationError",
    "PCIViolationError",
    "DataRetentionError",
]
