"""Cross-Cloud Mesh models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ON_PREM = "on_prem"


class ResourceType(str, Enum):
    """Types of cloud resources."""

    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    IDENTITY = "identity"
    ENCRYPTION = "encryption"


class ComplianceStatus(str, Enum):
    """Compliance status of a cloud resource."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class CloudResource:
    """A cloud resource tracked for compliance."""

    id: UUID = field(default_factory=uuid4)
    provider: CloudProvider = CloudProvider.AWS
    resource_type: ResourceType = ResourceType.COMPUTE
    name: str = ""
    region: str = ""
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    controls_mapped: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)


@dataclass
class CloudAccount:
    """A cloud provider account."""

    id: UUID = field(default_factory=uuid4)
    provider: CloudProvider = CloudProvider.AWS
    account_id: str = ""
    name: str = ""
    regions: list[str] = field(default_factory=list)
    resources_discovered: int = 0
    compliance_score: float = 0.0
    last_scan_at: datetime | None = None


@dataclass
class CrossCloudPosture:
    """Aggregated compliance posture across all cloud providers."""

    overall_score: float = 0.0
    by_provider: dict[str, float] = field(default_factory=dict)
    by_resource_type: dict[str, int] = field(default_factory=dict)
    total_resources: int = 0
    non_compliant: int = 0
    findings: list[dict] = field(default_factory=list)


@dataclass
class CrossCloudStats:
    """Statistics for the cross-cloud mesh service."""

    total_accounts: int = 0
    total_resources: int = 0
    by_provider: dict = field(default_factory=dict)
    overall_compliance_pct: float = 0.0
    findings_count: int = 0
