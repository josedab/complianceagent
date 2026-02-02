"""Compliance exceptions for the SDK."""


class ComplianceError(Exception):
    """Base exception for compliance-related errors."""
    
    def __init__(
        self,
        message: str,
        regulation: str | None = None,
        requirement: str | None = None,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.regulation = regulation
        self.requirement = requirement
        self.details = details or {}
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.regulation:
            parts.append(f"Regulation: {self.regulation}")
        if self.requirement:
            parts.append(f"Requirement: {self.requirement}")
        return " | ".join(parts)


class ConsentRequiredError(ComplianceError):
    """Raised when required consent has not been obtained."""
    
    def __init__(
        self,
        consent_type: str,
        user_id: str | None = None,
        message: str | None = None,
    ):
        msg = message or f"Consent required: {consent_type}"
        super().__init__(
            message=msg,
            regulation="GDPR",
            requirement="Article 7 - Conditions for consent",
            details={"consent_type": consent_type, "user_id": user_id},
        )
        self.consent_type = consent_type
        self.user_id = user_id


class EncryptionError(ComplianceError):
    """Raised when encryption requirements are not met."""
    
    def __init__(
        self,
        message: str,
        field: str | None = None,
        encryption_type: str | None = None,
    ):
        super().__init__(
            message=message,
            regulation="Multiple",
            requirement="Encryption at rest and in transit",
            details={"field": field, "encryption_type": encryption_type},
        )
        self.field = field
        self.encryption_type = encryption_type


class AccessDeniedError(ComplianceError):
    """Raised when access control requirements deny access."""
    
    def __init__(
        self,
        resource: str,
        user_id: str | None = None,
        required_role: str | None = None,
        message: str | None = None,
    ):
        msg = message or f"Access denied to resource: {resource}"
        super().__init__(
            message=msg,
            regulation="Multiple",
            requirement="Access Control",
            details={
                "resource": resource,
                "user_id": user_id,
                "required_role": required_role,
            },
        )
        self.resource = resource
        self.user_id = user_id
        self.required_role = required_role


class AuditLogError(ComplianceError):
    """Raised when audit logging fails."""
    
    def __init__(
        self,
        message: str,
        action: str | None = None,
    ):
        super().__init__(
            message=message,
            regulation="Multiple",
            requirement="Audit Trail",
            details={"action": action},
        )
        self.action = action


class ValidationError(ComplianceError):
    """Raised when compliance validation fails."""
    
    def __init__(
        self,
        message: str,
        violations: list[dict] | None = None,
    ):
        super().__init__(
            message=message,
            details={"violations": violations or []},
        )
        self.violations = violations or []


class DataRetentionError(ComplianceError):
    """Raised when data retention policies are violated."""
    
    def __init__(
        self,
        message: str,
        data_type: str | None = None,
        retention_period: str | None = None,
    ):
        super().__init__(
            message=message,
            regulation="GDPR",
            requirement="Article 5(1)(e) - Storage limitation",
            details={
                "data_type": data_type,
                "retention_period": retention_period,
            },
        )
        self.data_type = data_type
        self.retention_period = retention_period


class PHIViolationError(ComplianceError):
    """Raised when PHI handling requirements are violated."""
    
    def __init__(
        self,
        message: str,
        violation_type: str | None = None,
    ):
        super().__init__(
            message=message,
            regulation="HIPAA",
            requirement="PHI Safeguards",
            details={"violation_type": violation_type},
        )
        self.violation_type = violation_type


class PCIViolationError(ComplianceError):
    """Raised when PCI-DSS requirements are violated."""
    
    def __init__(
        self,
        message: str,
        requirement_id: str | None = None,
    ):
        super().__init__(
            message=message,
            regulation="PCI-DSS",
            requirement=requirement_id or "Cardholder Data Protection",
            details={"pci_requirement": requirement_id},
        )
        self.requirement_id = requirement_id
