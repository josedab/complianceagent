"""Multi-Cloud IaC Compliance Scanner models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class IaCPlatform(str, Enum):
    """Supported Infrastructure-as-Code platforms."""

    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    KUBERNETES = "kubernetes"
    PULUMI = "pulumi"
    ANSIBLE = "ansible"


class CloudProvider(str, Enum):
    """Cloud provider targets."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"


class ViolationSeverity(str, Enum):
    """Severity level for compliance violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ResourceType(str, Enum):
    """Infrastructure resource types."""

    S3_BUCKET = "s3_bucket"
    RDS_INSTANCE = "rds_instance"
    EC2_INSTANCE = "ec2_instance"
    IAM_POLICY = "iam_policy"
    VPC = "vpc"
    SECURITY_GROUP = "security_group"
    KMS_KEY = "kms_key"
    LAMBDA_FUNCTION = "lambda_function"
    ECS_TASK = "ecs_task"
    EKS_CLUSTER = "eks_cluster"
    AZURE_STORAGE = "azure_storage"
    GCS_BUCKET = "gcs_bucket"
    K8S_POD = "k8s_pod"
    K8S_NETWORK_POLICY = "k8s_network_policy"
    K8S_RBAC = "k8s_rbac"
    K8S_SECRET = "k8s_secret"


@dataclass
class IaCViolation:
    """A single compliance violation found in IaC code."""

    id: UUID = field(default_factory=uuid4)
    rule_id: str = ""
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    resource_type: ResourceType = ResourceType.S3_BUCKET
    resource_name: str = ""
    file_path: str = ""
    line_number: int = 0
    description: str = ""
    regulation: str = ""
    article: str = ""
    fix_suggestion: str = ""
    auto_fixable: bool = False


@dataclass
class ScanSummary:
    """Summary statistics for a scan."""

    total_resources: int = 0
    total_violations: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    compliance_score: float = 100.0
    top_violations: list[str] = field(default_factory=list)


@dataclass
class IaCScanResult:
    """Result of an IaC compliance scan."""

    id: UUID = field(default_factory=uuid4)
    org_id: str = ""
    platform: IaCPlatform = IaCPlatform.TERRAFORM
    provider: CloudProvider = CloudProvider.AWS
    files_scanned: int = 0
    violations: list[IaCViolation] = field(default_factory=list)
    summary: ScanSummary = field(default_factory=ScanSummary)
    scanned_at: datetime | None = None
    duration_ms: int = 0


@dataclass
class ComplianceRule:
    """A compliance rule for IaC scanning."""

    id: str = ""
    name: str = ""
    description: str = ""
    platform: IaCPlatform = IaCPlatform.TERRAFORM
    provider: CloudProvider = CloudProvider.AWS
    resource_type: ResourceType = ResourceType.S3_BUCKET
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    regulation: str = ""
    article: str = ""
    check_function: str = ""
    fix_template: str = ""
    enabled: bool = True


@dataclass
class IaCFixSuggestion:
    """Auto-fix suggestion for a violation."""

    violation_id: UUID = field(default_factory=uuid4)
    original_code: str = ""
    fixed_code: str = ""
    explanation: str = ""
    confidence: float = 0.0


@dataclass
class ScanConfiguration:
    """Configuration for an IaC scan."""

    platforms: list[IaCPlatform] = field(default_factory=lambda: [IaCPlatform.TERRAFORM])
    providers: list[CloudProvider] = field(default_factory=lambda: [CloudProvider.AWS])
    regulations: list[str] = field(default_factory=list)
    severity_threshold: ViolationSeverity = ViolationSeverity.LOW
    ignore_rules: list[str] = field(default_factory=list)
    custom_rules: list[ComplianceRule] = field(default_factory=list)
