"""Data models for Policy-as-Code service."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PolicyLanguage(str, Enum):
    """Supported policy languages."""
    
    REGO = "rego"
    CEL = "cel"  # Common Expression Language
    YAML = "yaml"  # Simple declarative
    JSON = "json"  # JSON Schema-based


class PolicyFormat(str, Enum):
    """Output format options."""
    
    OPA_BUNDLE = "opa-bundle"
    CONFTEST = "conftest"
    GATEKEEPER = "gatekeeper"
    KYVERNO = "kyverno"
    RAW = "raw"


class PolicySeverity(str, Enum):
    """Policy violation severity."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PolicyCategory(str, Enum):
    """Policy category."""
    
    DATA_PROTECTION = "data_protection"
    ACCESS_CONTROL = "access_control"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    DATA_RETENTION = "data_retention"
    CONSENT = "consent"
    BREACH_NOTIFICATION = "breach_notification"
    VULNERABILITY = "vulnerability"
    THIRD_PARTY = "third_party"
    AI_GOVERNANCE = "ai_governance"


class PolicyRule(BaseModel):
    """A single policy rule."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    regulation: str
    requirement_id: str | None = None
    article: str | None = None
    category: PolicyCategory
    severity: PolicySeverity
    
    # Rule logic
    condition: str = Field(description="Human-readable condition")
    rego_code: str | None = None
    cel_expression: str | None = None
    
    # Metadata
    tags: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    remediation: str | None = None
    
    # Testing
    test_cases: list["PolicyTestCase"] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyTestCase(BaseModel):
    """Test case for a policy rule."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    input_data: dict[str, Any]
    expected_result: bool
    expected_violations: list[str] = Field(default_factory=list)


class PolicyTestResult(BaseModel):
    """Result of running a policy test."""
    
    test_case_id: UUID
    test_name: str
    passed: bool
    actual_result: bool
    actual_violations: list[str]
    error: str | None = None
    execution_time_ms: float


class PolicyPackage(BaseModel):
    """A collection of related policy rules."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    namespace: str
    description: str
    version: str = "1.0.0"
    
    regulations: list[str] = Field(default_factory=list)
    rules: list[PolicyRule] = Field(default_factory=list)
    
    # Generated code
    rego_package: str | None = None
    cel_rules: list[str] | None = None
    
    # Metadata
    author: str | None = None
    organization_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_rules(self) -> int:
        return len(self.rules)
    
    @property
    def critical_rules(self) -> int:
        return len([r for r in self.rules if r.severity == PolicySeverity.CRITICAL])


class PolicyValidationResult(BaseModel):
    """Result of validating a policy."""
    
    id: UUID = Field(default_factory=uuid4)
    policy_id: UUID
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    
    # Syntax check
    syntax_valid: bool = True
    syntax_errors: list[str] = Field(default_factory=list)
    
    # Semantic check
    semantic_valid: bool = True
    semantic_errors: list[str] = Field(default_factory=list)
    
    # Test results
    tests_run: int = 0
    tests_passed: int = 0
    test_results: list[PolicyTestResult] = Field(default_factory=list)
    
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class CompliancePolicyTemplate(BaseModel):
    """Pre-built compliance policy template."""
    
    id: str
    name: str
    description: str
    regulation: str
    version: str
    
    # Template content
    rules: list[PolicyRule]
    
    # Customization
    parameters: dict[str, Any] = Field(default_factory=dict)
    parameter_descriptions: dict[str, str] = Field(default_factory=dict)
    
    # Usage
    use_cases: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    
    # Metadata
    maintainer: str = "ComplianceAgent"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Pre-built Compliance Policy Templates
# ============================================================================

GDPR_DATA_PROTECTION_RULES: list[dict] = [
    {
        "name": "personal_data_encryption",
        "description": "Personal data must be encrypted at rest and in transit",
        "regulation": "GDPR",
        "article": "Article 32 - Security of Processing",
        "category": PolicyCategory.ENCRYPTION,
        "severity": PolicySeverity.HIGH,
        "condition": "All personal data storage must use AES-256 encryption",
        "remediation": "Enable encryption for all data stores containing personal data",
        "tags": ["encryption", "personal-data", "security"],
    },
    {
        "name": "data_minimization",
        "description": "Only collect personal data necessary for the stated purpose",
        "regulation": "GDPR",
        "article": "Article 5(1)(c) - Data Minimization",
        "category": PolicyCategory.DATA_PROTECTION,
        "severity": PolicySeverity.MEDIUM,
        "condition": "Data collection must be limited to required fields only",
        "remediation": "Review and remove unnecessary data collection points",
        "tags": ["data-minimization", "privacy"],
    },
    {
        "name": "consent_tracking",
        "description": "Valid consent must be obtained and documented",
        "regulation": "GDPR",
        "article": "Article 7 - Conditions for Consent",
        "category": PolicyCategory.CONSENT,
        "severity": PolicySeverity.HIGH,
        "condition": "Consent records must exist for all personal data processing",
        "remediation": "Implement consent management system",
        "tags": ["consent", "documentation"],
    },
    {
        "name": "data_retention_limits",
        "description": "Personal data must not be kept longer than necessary",
        "regulation": "GDPR",
        "article": "Article 5(1)(e) - Storage Limitation",
        "category": PolicyCategory.DATA_RETENTION,
        "severity": PolicySeverity.MEDIUM,
        "condition": "Data retention policies must be defined and enforced",
        "remediation": "Implement automated data deletion based on retention schedules",
        "tags": ["retention", "deletion"],
    },
    {
        "name": "breach_notification",
        "description": "Data breaches must be reported within 72 hours",
        "regulation": "GDPR",
        "article": "Article 33 - Notification to Supervisory Authority",
        "category": PolicyCategory.BREACH_NOTIFICATION,
        "severity": PolicySeverity.CRITICAL,
        "condition": "Breach detection and notification procedures must be in place",
        "remediation": "Implement automated breach detection and notification workflows",
        "tags": ["breach", "notification", "incident-response"],
    },
    {
        "name": "access_logging",
        "description": "All access to personal data must be logged",
        "regulation": "GDPR",
        "article": "Article 30 - Records of Processing Activities",
        "category": PolicyCategory.LOGGING,
        "severity": PolicySeverity.HIGH,
        "condition": "Audit logs must be enabled for all personal data access",
        "remediation": "Enable comprehensive audit logging",
        "tags": ["logging", "audit", "traceability"],
    },
]

HIPAA_RULES: list[dict] = [
    {
        "name": "phi_encryption",
        "description": "Protected Health Information must be encrypted",
        "regulation": "HIPAA",
        "article": "Security Rule §164.312(a)(2)(iv)",
        "category": PolicyCategory.ENCRYPTION,
        "severity": PolicySeverity.CRITICAL,
        "condition": "All PHI must be encrypted using FIPS 140-2 validated algorithms",
        "remediation": "Implement encryption for all PHI storage and transmission",
        "tags": ["phi", "encryption", "healthcare"],
    },
    {
        "name": "access_controls",
        "description": "Implement technical access controls for PHI",
        "regulation": "HIPAA",
        "article": "Security Rule §164.312(a)(1)",
        "category": PolicyCategory.ACCESS_CONTROL,
        "severity": PolicySeverity.CRITICAL,
        "condition": "Role-based access control must be implemented for PHI",
        "remediation": "Implement RBAC with least privilege principle",
        "tags": ["access-control", "rbac", "phi"],
    },
    {
        "name": "audit_controls",
        "description": "Implement audit controls for PHI access",
        "regulation": "HIPAA",
        "article": "Security Rule §164.312(b)",
        "category": PolicyCategory.LOGGING,
        "severity": PolicySeverity.HIGH,
        "condition": "All PHI access must be logged with user identification",
        "remediation": "Enable comprehensive audit logging for all PHI systems",
        "tags": ["audit", "logging", "phi"],
    },
    {
        "name": "transmission_security",
        "description": "Implement transmission security for PHI",
        "regulation": "HIPAA",
        "article": "Security Rule §164.312(e)(1)",
        "category": PolicyCategory.ENCRYPTION,
        "severity": PolicySeverity.CRITICAL,
        "condition": "PHI transmission must use TLS 1.2 or higher",
        "remediation": "Configure TLS 1.2+ for all PHI transmission channels",
        "tags": ["transmission", "tls", "phi"],
    },
]

PCI_DSS_RULES: list[dict] = [
    {
        "name": "cardholder_data_encryption",
        "description": "Encrypt stored cardholder data",
        "regulation": "PCI-DSS",
        "article": "Requirement 3.4",
        "category": PolicyCategory.ENCRYPTION,
        "severity": PolicySeverity.CRITICAL,
        "condition": "PANs must be encrypted using strong cryptography",
        "remediation": "Implement PAN encryption with AES-256",
        "tags": ["pan", "encryption", "payment"],
    },
    {
        "name": "vulnerability_management",
        "description": "Develop and maintain secure systems",
        "regulation": "PCI-DSS",
        "article": "Requirement 6.2",
        "category": PolicyCategory.VULNERABILITY,
        "severity": PolicySeverity.HIGH,
        "condition": "Critical vulnerabilities must be patched within 30 days",
        "remediation": "Implement vulnerability scanning and patching program",
        "tags": ["vulnerability", "patching", "security"],
    },
    {
        "name": "access_restriction",
        "description": "Restrict access to cardholder data",
        "regulation": "PCI-DSS",
        "article": "Requirement 7.1",
        "category": PolicyCategory.ACCESS_CONTROL,
        "severity": PolicySeverity.HIGH,
        "condition": "Access to cardholder data must be need-to-know",
        "remediation": "Implement role-based access with business justification",
        "tags": ["access-control", "need-to-know"],
    },
]

EU_AI_ACT_RULES: list[dict] = [
    {
        "name": "risk_classification",
        "description": "AI systems must be classified by risk level",
        "regulation": "EU AI Act",
        "article": "Article 6 - Classification Rules",
        "category": PolicyCategory.AI_GOVERNANCE,
        "severity": PolicySeverity.HIGH,
        "condition": "AI systems must have documented risk classification",
        "remediation": "Complete AI risk assessment and classification",
        "tags": ["ai", "risk-assessment", "classification"],
    },
    {
        "name": "transparency_requirements",
        "description": "AI systems must provide transparency to users",
        "regulation": "EU AI Act",
        "article": "Article 13 - Transparency and Provision of Information",
        "category": PolicyCategory.AI_GOVERNANCE,
        "severity": PolicySeverity.HIGH,
        "condition": "AI systems must clearly indicate AI interaction to users",
        "remediation": "Implement AI disclosure notices",
        "tags": ["ai", "transparency", "disclosure"],
    },
    {
        "name": "human_oversight",
        "description": "High-risk AI must allow human oversight",
        "regulation": "EU AI Act",
        "article": "Article 14 - Human Oversight",
        "category": PolicyCategory.AI_GOVERNANCE,
        "severity": PolicySeverity.CRITICAL,
        "condition": "High-risk AI must have human-in-the-loop controls",
        "remediation": "Implement human override capabilities",
        "tags": ["ai", "human-oversight", "high-risk"],
    },
    {
        "name": "ai_accuracy_monitoring",
        "description": "AI accuracy must be continuously monitored",
        "regulation": "EU AI Act",
        "article": "Article 9 - Risk Management",
        "category": PolicyCategory.AI_GOVERNANCE,
        "severity": PolicySeverity.MEDIUM,
        "condition": "AI model performance must be monitored and logged",
        "remediation": "Implement model monitoring and drift detection",
        "tags": ["ai", "monitoring", "accuracy"],
    },
    {
        "name": "bias_detection",
        "description": "AI systems must be tested for bias",
        "regulation": "EU AI Act",
        "article": "Article 10 - Data and Data Governance",
        "category": PolicyCategory.AI_GOVERNANCE,
        "severity": PolicySeverity.HIGH,
        "condition": "AI training data must be tested for bias",
        "remediation": "Implement bias testing and mitigation procedures",
        "tags": ["ai", "bias", "fairness"],
    },
]


COMPLIANCE_TEMPLATES: dict[str, list[dict]] = {
    "GDPR": GDPR_DATA_PROTECTION_RULES,
    "HIPAA": HIPAA_RULES,
    "PCI-DSS": PCI_DSS_RULES,
    "EU AI Act": EU_AI_ACT_RULES,
}
