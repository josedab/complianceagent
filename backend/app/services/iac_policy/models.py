"""Multi-Cloud IaC Policy Engine models."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class IaCViolation:
    """A violation found during IaC scanning."""

    id: UUID = field(default_factory=uuid4)
    rule_id: str = ""
    resource_type: str = ""
    resource_name: str = ""
    provider: CloudProvider = CloudProvider.AWS
    severity: PolicySeverity = PolicySeverity.MEDIUM
    framework: str = ""
    description: str = ""
    remediation: str = ""
    file_path: str = ""
    line_number: int = 0


@dataclass
class PolicyRule:
    """A policy rule for IaC scanning."""

    id: str = ""
    name: str = ""
    provider: CloudProvider = CloudProvider.AWS
    framework: str = ""
    severity: PolicySeverity = PolicySeverity.MEDIUM
    description: str = ""
    pattern: str = ""


@dataclass
class IaCScanResult:
    """Result of an IaC scan."""

    id: UUID = field(default_factory=uuid4)
    provider: CloudProvider = CloudProvider.AWS
    files_scanned: int = 0
    violations: list[IaCViolation] = field(default_factory=list)
    pass_count: int = 0
    fail_count: int = 0
    scan_duration_ms: int = 0
