"""Zero-Trust Compliance Architecture Scanner models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ResourceType(str, Enum):
    """Cloud resource type."""

    IAM_ROLE = "iam_role"
    SECURITY_GROUP = "security_group"
    S3_BUCKET = "s3_bucket"
    RDS_INSTANCE = "rds_instance"
    LAMBDA_FUNCTION = "lambda_function"
    EKS_CLUSTER = "eks_cluster"
    API_GATEWAY = "api_gateway"
    KMS_KEY = "kms_key"


class ComplianceFramework(str, Enum):
    """Compliance framework reference."""

    GDPR_ART32 = "gdpr_art32"
    HIPAA_164_312 = "hipaa_164_312"
    SOC2_CC6_1 = "soc2_cc6_1"
    NIST_800_207 = "nist_800_207"
    PCI_DSS_REQ7 = "pci_dss_req7"
    ISO27001_A9 = "iso27001_a9"


class ViolationStatus(str, Enum):
    """Violation lifecycle status."""

    OPEN = "open"
    REMEDIATED = "remediated"
    SUPPRESSED = "suppressed"
    FALSE_POSITIVE = "false_positive"


@dataclass
class ZeroTrustPolicy:
    """A zero-trust compliance policy definition."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    framework: ComplianceFramework = ComplianceFramework.NIST_800_207
    resource_types: list[ResourceType] = field(default_factory=list)
    description: str = ""
    rego_rule: str = ""
    severity: str = "medium"


@dataclass
class InfraResource:
    """A discovered infrastructure resource."""

    id: UUID = field(default_factory=uuid4)
    resource_type: ResourceType = ResourceType.IAM_ROLE
    name: str = ""
    arn: str = ""
    region: str = ""
    tags: dict = field(default_factory=dict)
    configuration: dict = field(default_factory=dict)
    discovered_at: datetime | None = None


@dataclass
class ZeroTrustViolation:
    """A detected zero-trust violation."""

    id: UUID = field(default_factory=uuid4)
    policy_id: UUID = field(default_factory=uuid4)
    resource_id: UUID = field(default_factory=uuid4)
    resource_name: str = ""
    violation_type: str = ""
    severity: str = "medium"
    description: str = ""
    framework: ComplianceFramework = ComplianceFramework.NIST_800_207
    remediation_hint: str = ""
    iac_file: str = ""
    iac_line: int = 0
    status: ViolationStatus = ViolationStatus.OPEN
    detected_at: datetime | None = None


@dataclass
class ScanResult:
    """Result of an infrastructure scan."""

    id: UUID = field(default_factory=uuid4)
    scan_type: str = "iac"
    resources_scanned: int = 0
    violations_found: int = 0
    violations: list[ZeroTrustViolation] = field(default_factory=list)
    compliance_score: float = 100.0
    scanned_at: datetime | None = None


@dataclass
class RemediationPlan:
    """A remediation plan for a violation."""

    id: UUID = field(default_factory=uuid4)
    violation_id: UUID = field(default_factory=uuid4)
    iac_diff: str = ""
    description: str = ""
    auto_fixable: bool = False
    risk: str = "low"
