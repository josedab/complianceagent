"""Compliance validators for data and policy enforcement."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Protocol


class ValidationSeverity(str, Enum):
    """Severity levels for validation violations."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Regulation(str, Enum):
    """Supported compliance regulations."""
    
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS"
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    CCPA = "CCPA"
    FERPA = "FERPA"
    GLBA = "GLBA"


@dataclass
class ValidationViolation:
    """Represents a single validation violation."""
    
    rule_id: str
    message: str
    severity: ValidationSeverity
    regulation: Regulation | None = None
    requirement_id: str | None = None
    field_path: str | None = None
    actual_value: Any = None
    expected_value: Any = None
    remediation: str | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "regulation": self.regulation.value if self.regulation else None,
            "requirement_id": self.requirement_id,
            "field_path": self.field_path,
            "actual_value": str(self.actual_value) if self.actual_value else None,
            "expected_value": str(self.expected_value) if self.expected_value else None,
            "remediation": self.remediation,
        }


@dataclass
class ValidationResult:
    """Result of a validation run."""
    
    valid: bool
    violations: list[ValidationViolation] = field(default_factory=list)
    warnings: list[ValidationViolation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def error_count(self) -> int:
        """Count of error-level violations."""
        return len([v for v in self.violations if v.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)])
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level violations."""
        return len(self.warnings)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "timestamp": self.timestamp.isoformat(),
        }


class ValidationRule(Protocol):
    """Protocol for validation rules."""
    
    rule_id: str
    regulation: Regulation | None
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]: ...


@dataclass
class PII_Fields:
    """Common PII field patterns."""
    
    EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    PHONE_PATTERN = r"^\+?[\d\s\-().]{7,20}$"
    SSN_PATTERN = r"^\d{3}-?\d{2}-?\d{4}$"
    CREDIT_CARD_PATTERN = r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$"
    IP_ADDRESS_PATTERN = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    
    COMMON_FIELD_NAMES = [
        "email", "phone", "telephone", "mobile", "ssn", "social_security",
        "credit_card", "card_number", "pan", "ip_address", "address",
        "first_name", "last_name", "full_name", "date_of_birth", "dob",
        "passport", "driver_license", "national_id", "tax_id", "bank_account",
    ]


class ComplianceValidator:
    """Main validator class for compliance checking."""
    
    def __init__(self, regulations: list[Regulation] | None = None):
        """Initialize validator with enabled regulations."""
        self.regulations = regulations or list(Regulation)
        self._rules: list[ValidationRule] = []
        self._custom_rules: list[Callable[[Any, dict | None], list[ValidationViolation]]] = []
        self._register_default_rules()
    
    def _register_default_rules(self) -> None:
        """Register default validation rules."""
        self._rules.extend([
            PIIExposureRule(),
            EncryptionRequiredRule(),
            ConsentRequiredRule(),
            RetentionPolicyRule(),
            AccessLoggingRule(),
            DataMinimizationRule(),
            PHIRule(),
            PCIRule(),
        ])
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule."""
        self._rules.append(rule)
    
    def add_custom_validator(
        self,
        validator_fn: Callable[[Any, dict | None], list[ValidationViolation]],
    ) -> None:
        """Add a custom validation function."""
        self._custom_rules.append(validator_fn)
    
    def validate(
        self,
        data: Any,
        context: dict | None = None,
        regulations: list[Regulation] | None = None,
    ) -> ValidationResult:
        """Validate data against compliance rules.
        
        Args:
            data: Data to validate
            context: Additional context for validation
            regulations: Specific regulations to check (defaults to all enabled)
        
        Returns:
            ValidationResult with violations and warnings
        """
        active_regulations = regulations or self.regulations
        all_violations: list[ValidationViolation] = []
        all_warnings: list[ValidationViolation] = []
        
        # Run registered rules
        for rule in self._rules:
            if rule.regulation is None or rule.regulation in active_regulations:
                violations = rule.validate(data, context)
                for v in violations:
                    if v.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
                        all_violations.append(v)
                    else:
                        all_warnings.append(v)
        
        # Run custom rules
        for custom_rule in self._custom_rules:
            violations = custom_rule(data, context)
            for v in violations:
                if v.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
                    all_violations.append(v)
                else:
                    all_warnings.append(v)
        
        return ValidationResult(
            valid=len(all_violations) == 0,
            violations=all_violations,
            warnings=all_warnings,
        )
    
    def validate_pii(
        self,
        data: dict,
        allowed_fields: list[str] | None = None,
    ) -> ValidationResult:
        """Specifically validate PII handling."""
        violations: list[ValidationViolation] = []
        
        def check_dict(d: dict, path: str = "") -> None:
            for key, value in d.items():
                field_path = f"{path}.{key}" if path else key
                
                # Check if field name matches PII patterns
                if key.lower() in [f.lower() for f in PII_Fields.COMMON_FIELD_NAMES]:
                    if allowed_fields and key.lower() not in [f.lower() for f in allowed_fields]:
                        violations.append(ValidationViolation(
                            rule_id="PII_FIELD_NOT_ALLOWED",
                            message=f"PII field '{key}' is present but not in allowed list",
                            severity=ValidationSeverity.ERROR,
                            regulation=Regulation.GDPR,
                            requirement_id="Article 5(1)(c)",
                            field_path=field_path,
                            remediation="Remove the field or add it to the allowed list",
                        ))
                
                # Check for unencrypted sensitive patterns
                if isinstance(value, str):
                    if re.match(PII_Fields.SSN_PATTERN, value):
                        violations.append(ValidationViolation(
                            rule_id="SSN_DETECTED",
                            message="Potential SSN detected in plain text",
                            severity=ValidationSeverity.CRITICAL,
                            regulation=Regulation.GDPR,
                            field_path=field_path,
                            remediation="Encrypt SSN before storage",
                        ))
                    
                    if re.match(PII_Fields.CREDIT_CARD_PATTERN, value.replace(" ", "").replace("-", "")):
                        violations.append(ValidationViolation(
                            rule_id="CREDIT_CARD_DETECTED",
                            message="Potential credit card number detected",
                            severity=ValidationSeverity.CRITICAL,
                            regulation=Regulation.PCI_DSS,
                            requirement_id="Requirement 3.4",
                            field_path=field_path,
                            remediation="Do not store full card numbers; use tokenization",
                        ))
                
                elif isinstance(value, dict):
                    check_dict(value, field_path)
                
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            check_dict(item, f"{field_path}[{i}]")
        
        check_dict(data)
        
        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
        )
    
    def validate_consent(
        self,
        user_id: str,
        purpose: str,
        consent_records: list[dict],
    ) -> ValidationResult:
        """Validate consent requirements."""
        violations: list[ValidationViolation] = []
        
        # Find consent for this user and purpose
        user_consent = None
        for record in consent_records:
            if record.get("user_id") == user_id and record.get("purpose") == purpose:
                user_consent = record
                break
        
        if user_consent is None:
            violations.append(ValidationViolation(
                rule_id="CONSENT_NOT_FOUND",
                message=f"No consent record found for user '{user_id}' and purpose '{purpose}'",
                severity=ValidationSeverity.ERROR,
                regulation=Regulation.GDPR,
                requirement_id="Article 7",
                remediation="Obtain explicit consent before processing",
            ))
        else:
            # Check if consent is still valid
            if user_consent.get("withdrawn"):
                violations.append(ValidationViolation(
                    rule_id="CONSENT_WITHDRAWN",
                    message="User has withdrawn consent for this purpose",
                    severity=ValidationSeverity.ERROR,
                    regulation=Regulation.GDPR,
                    requirement_id="Article 7(3)",
                    remediation="Stop processing or obtain new consent",
                ))
            
            # Check expiration
            if "expires_at" in user_consent:
                expires = datetime.fromisoformat(user_consent["expires_at"].replace("Z", "+00:00"))
                if expires < datetime.now(timezone.utc):
                    violations.append(ValidationViolation(
                        rule_id="CONSENT_EXPIRED",
                        message="Consent has expired",
                        severity=ValidationSeverity.ERROR,
                        regulation=Regulation.GDPR,
                        requirement_id="Article 7",
                        remediation="Request consent renewal",
                    ))
        
        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
        )
    
    def validate_retention(
        self,
        data_records: list[dict],
        retention_policy: dict[str, int],
    ) -> ValidationResult:
        """Validate data retention compliance."""
        violations: list[ValidationViolation] = []
        now = datetime.now(timezone.utc)
        
        for i, record in enumerate(data_records):
            data_type = record.get("data_type", "default")
            created_at = record.get("created_at")
            
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                
                max_days = retention_policy.get(data_type, retention_policy.get("default", 365))
                age_days = (now - created_at).days
                
                if age_days > max_days:
                    violations.append(ValidationViolation(
                        rule_id="RETENTION_EXCEEDED",
                        message=f"Record exceeds retention period ({age_days} days > {max_days} days)",
                        severity=ValidationSeverity.ERROR,
                        regulation=Regulation.GDPR,
                        requirement_id="Article 5(1)(e)",
                        field_path=f"records[{i}]",
                        actual_value=age_days,
                        expected_value=max_days,
                        remediation="Delete or anonymize the record",
                    ))
        
        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
        )


# Built-in validation rules

@dataclass
class PIIExposureRule:
    """Rule to detect exposed PII."""
    
    rule_id: str = "PII_EXPOSURE"
    regulation: Regulation | None = Regulation.GDPR
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check for PII exposure."""
        violations: list[ValidationViolation] = []
        
        def scan_value(value: Any, path: str) -> None:
            if isinstance(value, str):
                # Check for SSN
                if re.match(PII_Fields.SSN_PATTERN, value):
                    violations.append(ValidationViolation(
                        rule_id=self.rule_id,
                        message="SSN pattern detected in plain text",
                        severity=ValidationSeverity.CRITICAL,
                        regulation=self.regulation,
                        field_path=path,
                    ))
                
                # Check for credit card
                clean_value = re.sub(r"[\s-]", "", value)
                if re.match(r"^\d{13,19}$", clean_value) and self._luhn_check(clean_value):
                    violations.append(ValidationViolation(
                        rule_id=self.rule_id,
                        message="Credit card number pattern detected",
                        severity=ValidationSeverity.CRITICAL,
                        regulation=Regulation.PCI_DSS,
                        field_path=path,
                    ))
            
            elif isinstance(value, dict):
                for k, v in value.items():
                    scan_value(v, f"{path}.{k}" if path else k)
            
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    scan_value(item, f"{path}[{i}]")
        
        scan_value(data, "")
        return violations
    
    def _luhn_check(self, number: str) -> bool:
        """Validate card number with Luhn algorithm."""
        try:
            digits = [int(d) for d in number]
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(divmod(d * 2, 10))
            return checksum % 10 == 0
        except (ValueError, IndexError):
            return False


@dataclass
class EncryptionRequiredRule:
    """Rule to check encryption requirements."""
    
    rule_id: str = "ENCRYPTION_REQUIRED"
    regulation: Regulation | None = Regulation.GDPR
    sensitive_fields: list[str] = field(default_factory=lambda: [
        "password", "secret", "token", "api_key", "private_key",
        "ssn", "credit_card", "card_number",
    ])
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check for unencrypted sensitive fields."""
        violations: list[ValidationViolation] = []
        encryption_marker = context.get("encryption_marker", "encrypted:") if context else "encrypted:"
        
        def check_dict(d: dict, path: str = "") -> None:
            for key, value in d.items():
                field_path = f"{path}.{key}" if path else key
                
                if key.lower() in [f.lower() for f in self.sensitive_fields]:
                    if isinstance(value, str) and not value.startswith(encryption_marker):
                        violations.append(ValidationViolation(
                            rule_id=self.rule_id,
                            message=f"Sensitive field '{key}' should be encrypted",
                            severity=ValidationSeverity.ERROR,
                            regulation=self.regulation,
                            requirement_id="Article 32",
                            field_path=field_path,
                            remediation="Encrypt this field before storage",
                        ))
                
                elif isinstance(value, dict):
                    check_dict(value, field_path)
                
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            check_dict(item, f"{field_path}[{i}]")
        
        if isinstance(data, dict):
            check_dict(data)
        
        return violations


@dataclass
class ConsentRequiredRule:
    """Rule to verify consent requirements."""
    
    rule_id: str = "CONSENT_REQUIRED"
    regulation: Regulation | None = Regulation.GDPR
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check consent requirements."""
        violations: list[ValidationViolation] = []
        
        if context and context.get("requires_consent"):
            if not context.get("consent_given"):
                violations.append(ValidationViolation(
                    rule_id=self.rule_id,
                    message="Processing requires consent that has not been given",
                    severity=ValidationSeverity.ERROR,
                    regulation=self.regulation,
                    requirement_id="Article 7",
                    remediation="Obtain explicit consent before processing",
                ))
        
        return violations


@dataclass
class RetentionPolicyRule:
    """Rule to enforce data retention policies."""
    
    rule_id: str = "RETENTION_POLICY"
    regulation: Regulation | None = Regulation.GDPR
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check retention policy compliance."""
        violations: list[ValidationViolation] = []
        
        if context and context.get("retention_check"):
            max_days = context.get("max_retention_days", 365)
            created_at = context.get("created_at")
            
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                
                age_days = (datetime.now(timezone.utc) - created_at).days
                
                if age_days > max_days:
                    violations.append(ValidationViolation(
                        rule_id=self.rule_id,
                        message=f"Data exceeds retention period",
                        severity=ValidationSeverity.ERROR,
                        regulation=self.regulation,
                        requirement_id="Article 5(1)(e)",
                        actual_value=age_days,
                        expected_value=max_days,
                        remediation="Delete or anonymize data",
                    ))
        
        return violations


@dataclass
class AccessLoggingRule:
    """Rule to verify access logging requirements."""
    
    rule_id: str = "ACCESS_LOGGING"
    regulation: Regulation | None = Regulation.HIPAA
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check access logging requirements."""
        violations: list[ValidationViolation] = []
        
        if context and context.get("requires_access_logging"):
            if not context.get("access_logged"):
                violations.append(ValidationViolation(
                    rule_id=self.rule_id,
                    message="Access to sensitive data must be logged",
                    severity=ValidationSeverity.WARNING,
                    regulation=self.regulation,
                    requirement_id="164.312(b)",
                    remediation="Enable audit logging for this access",
                ))
        
        return violations


@dataclass
class DataMinimizationRule:
    """Rule to enforce data minimization."""
    
    rule_id: str = "DATA_MINIMIZATION"
    regulation: Regulation | None = Regulation.GDPR
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check data minimization compliance."""
        violations: list[ValidationViolation] = []
        warnings: list[ValidationViolation] = []
        
        if context and context.get("required_fields"):
            required = set(context["required_fields"])
            
            if isinstance(data, dict):
                actual = set(data.keys())
                extra = actual - required
                
                if extra:
                    for field in extra:
                        warnings.append(ValidationViolation(
                            rule_id=self.rule_id,
                            message=f"Field '{field}' may not be necessary",
                            severity=ValidationSeverity.INFO,
                            regulation=self.regulation,
                            requirement_id="Article 5(1)(c)",
                            field_path=field,
                            remediation="Review if this field is necessary for the purpose",
                        ))
        
        return violations + warnings


@dataclass
class PHIRule:
    """Rule for HIPAA PHI handling."""
    
    rule_id: str = "PHI_HANDLING"
    regulation: Regulation | None = Regulation.HIPAA
    phi_fields: list[str] = field(default_factory=lambda: [
        "diagnosis", "treatment", "prescription", "medical_record_number",
        "health_plan_number", "condition", "medication", "lab_result",
        "patient_name", "patient_dob", "provider_name",
    ])
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check PHI handling compliance."""
        violations: list[ValidationViolation] = []
        
        def check_dict(d: dict, path: str = "") -> None:
            for key, value in d.items():
                field_path = f"{path}.{key}" if path else key
                
                if key.lower() in [f.lower() for f in self.phi_fields]:
                    # Check if access is logged
                    if context and not context.get("phi_access_logged"):
                        violations.append(ValidationViolation(
                            rule_id=self.rule_id,
                            message=f"PHI field '{key}' accessed without logging",
                            severity=ValidationSeverity.ERROR,
                            regulation=self.regulation,
                            requirement_id="164.312(b)",
                            field_path=field_path,
                            remediation="Log all PHI access events",
                        ))
                    
                    # Check if encrypted
                    if isinstance(value, str) and not value.startswith("encrypted:"):
                        if context and context.get("storage_context"):
                            violations.append(ValidationViolation(
                                rule_id=self.rule_id,
                                message=f"PHI field '{key}' should be encrypted at rest",
                                severity=ValidationSeverity.ERROR,
                                regulation=self.regulation,
                                requirement_id="164.312(a)(2)(iv)",
                                field_path=field_path,
                                remediation="Encrypt PHI before storage",
                            ))
                
                elif isinstance(value, dict):
                    check_dict(value, field_path)
        
        if isinstance(data, dict):
            check_dict(data)
        
        return violations


@dataclass
class PCIRule:
    """Rule for PCI-DSS compliance."""
    
    rule_id: str = "PCI_DSS"
    regulation: Regulation | None = Regulation.PCI_DSS
    
    def validate(self, data: Any, context: dict | None = None) -> list[ValidationViolation]:
        """Check PCI-DSS compliance."""
        violations: list[ValidationViolation] = []
        
        def check_dict(d: dict, path: str = "") -> None:
            for key, value in d.items():
                field_path = f"{path}.{key}" if path else key
                
                # Never store CVV
                if key.lower() in ["cvv", "cvc", "cvv2", "cvc2", "security_code"]:
                    if value:  # CVV present
                        violations.append(ValidationViolation(
                            rule_id=self.rule_id,
                            message="CVV/CVC must not be stored after authorization",
                            severity=ValidationSeverity.CRITICAL,
                            regulation=self.regulation,
                            requirement_id="Requirement 3.2",
                            field_path=field_path,
                            remediation="Remove CVV immediately after authorization",
                        ))
                
                # Check for full PAN storage
                if key.lower() in ["card_number", "pan", "primary_account_number", "account_number"]:
                    if isinstance(value, str):
                        clean_val = re.sub(r"[\s-]", "", value)
                        if len(clean_val) >= 12 and not clean_val.startswith("*"):
                            violations.append(ValidationViolation(
                                rule_id=self.rule_id,
                                message="Full PAN should not be stored; use masking or tokenization",
                                severity=ValidationSeverity.ERROR,
                                regulation=self.regulation,
                                requirement_id="Requirement 3.4",
                                field_path=field_path,
                                remediation="Tokenize or mask PAN (show only last 4 digits)",
                            ))
                
                elif isinstance(value, dict):
                    check_dict(value, field_path)
        
        if isinstance(data, dict):
            check_dict(data)
        
        return violations


def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(re.match(PII_Fields.EMAIL_PATTERN, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    return bool(re.match(PII_Fields.PHONE_PATTERN, phone))


def mask_pii(value: str, visible_chars: int = 4) -> str:
    """Mask a PII value, keeping only the last N characters visible."""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def anonymize_data(data: dict, fields_to_anonymize: list[str]) -> dict:
    """Anonymize specified fields in data."""
    result = {}
    for key, value in data.items():
        if key.lower() in [f.lower() for f in fields_to_anonymize]:
            if isinstance(value, str):
                result[key] = mask_pii(value)
            else:
                result[key] = "[ANONYMIZED]"
        elif isinstance(value, dict):
            result[key] = anonymize_data(value, fields_to_anonymize)
        else:
            result[key] = value
    return result
