"""Models for infrastructure compliance analysis."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"
    MULTI = "multi"


class InfrastructureType(str, Enum):
    """Types of infrastructure configuration."""
    
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    CLOUDFORMATION = "cloudformation"
    ARM = "arm"  # Azure Resource Manager
    PULUMI = "pulumi"
    HELM = "helm"


class ViolationSeverity(str, Enum):
    """Severity levels for compliance violations."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceCategory(str, Enum):
    """Categories of compliance requirements."""
    
    ENCRYPTION = "encryption"
    ACCESS_CONTROL = "access_control"
    NETWORK_SECURITY = "network_security"
    LOGGING = "logging"
    DATA_PROTECTION = "data_protection"
    IDENTITY = "identity"
    CONFIGURATION = "configuration"
    BACKUP = "backup"
    MONITORING = "monitoring"


@dataclass
class InfrastructureResource:
    """Represents an infrastructure resource."""
    
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    resource_type: str = ""
    provider: CloudProvider = CloudProvider.AWS
    infrastructure_type: InfrastructureType = InfrastructureType.TERRAFORM
    
    # Location in source
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    
    # Resource properties
    properties: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    
    # Dependencies
    depends_on: list[str] = field(default_factory=list)
    referenced_by: list[str] = field(default_factory=list)
    
    # Data classification
    contains_pii: bool = False
    contains_phi: bool = False
    contains_pci: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "resource_type": self.resource_type,
            "provider": self.provider.value,
            "infrastructure_type": self.infrastructure_type.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "properties": self.properties,
            "tags": self.tags,
            "depends_on": self.depends_on,
            "contains_pii": self.contains_pii,
            "contains_phi": self.contains_phi,
            "contains_pci": self.contains_pci,
        }


@dataclass
class PolicyRule:
    """A compliance policy rule."""
    
    id: str
    name: str
    description: str
    severity: ViolationSeverity
    category: ComplianceCategory
    
    # Applicable regulations
    regulations: list[str] = field(default_factory=list)
    requirement_ids: list[str] = field(default_factory=list)
    
    # Applicable resource types
    resource_types: list[str] = field(default_factory=list)
    providers: list[CloudProvider] = field(default_factory=list)
    
    # Check function signature: (resource) -> bool
    # True = compliant, False = violation
    check_expression: str = ""
    
    # Remediation
    remediation_guidance: str = ""
    auto_remediation_available: bool = False
    
    # Metadata
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "regulations": self.regulations,
            "requirement_ids": self.requirement_ids,
            "resource_types": self.resource_types,
            "providers": [p.value for p in self.providers],
            "remediation_guidance": self.remediation_guidance,
            "auto_remediation_available": self.auto_remediation_available,
            "enabled": self.enabled,
        }


@dataclass
class RemediationAction:
    """A remediation action for a compliance violation."""
    
    id: UUID = field(default_factory=uuid4)
    action_type: str = ""  # add_property, modify_property, remove_resource, etc.
    description: str = ""
    
    # Target resource
    resource_name: str = ""
    resource_type: str = ""
    file_path: str = ""
    
    # Changes to make
    property_path: str = ""
    current_value: Any = None
    suggested_value: Any = None
    
    # Generated code/config
    suggested_code: str = ""
    
    # Effort
    estimated_effort_minutes: int = 5
    requires_manual_review: bool = False
    
    # Impact
    breaking_change: bool = False
    affected_resources: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "action_type": self.action_type,
            "description": self.description,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "file_path": self.file_path,
            "property_path": self.property_path,
            "current_value": str(self.current_value) if self.current_value else None,
            "suggested_value": str(self.suggested_value) if self.suggested_value else None,
            "suggested_code": self.suggested_code,
            "estimated_effort_minutes": self.estimated_effort_minutes,
            "requires_manual_review": self.requires_manual_review,
            "breaking_change": self.breaking_change,
            "affected_resources": self.affected_resources,
        }


@dataclass
class ComplianceViolation:
    """A compliance violation found in infrastructure."""
    
    id: UUID = field(default_factory=uuid4)
    rule_id: str = ""
    rule_name: str = ""
    
    # Violation details
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    category: ComplianceCategory = ComplianceCategory.CONFIGURATION
    description: str = ""
    
    # Resource info
    resource_name: str = ""
    resource_type: str = ""
    resource_id: str = ""
    provider: CloudProvider = CloudProvider.AWS
    
    # Location
    file_path: str = ""
    line_number: int = 0
    
    # Compliance context
    regulations: list[str] = field(default_factory=list)
    requirement_ids: list[str] = field(default_factory=list)
    
    # Evidence
    evidence: dict[str, Any] = field(default_factory=dict)
    
    # Remediation
    remediation: RemediationAction | None = None
    
    # Metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "provider": self.provider.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "regulations": self.regulations,
            "requirement_ids": self.requirement_ids,
            "evidence": self.evidence,
            "remediation": self.remediation.to_dict() if self.remediation else None,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class InfrastructureAnalysisResult:
    """Result of infrastructure compliance analysis."""
    
    id: UUID = field(default_factory=uuid4)
    
    # Summary
    total_resources: int = 0
    compliant_resources: int = 0
    non_compliant_resources: int = 0
    compliance_score: float = 0.0
    
    # Violation counts by severity
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    
    # Detailed results
    resources: list[InfrastructureResource] = field(default_factory=list)
    violations: list[ComplianceViolation] = field(default_factory=list)
    
    # By provider
    provider_breakdown: dict[str, dict[str, int]] = field(default_factory=dict)
    
    # By category
    category_breakdown: dict[str, dict[str, int]] = field(default_factory=dict)
    
    # By regulation
    regulation_breakdown: dict[str, dict[str, int]] = field(default_factory=dict)
    
    # Metadata
    analyzed_files: list[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_duration_ms: int = 0
    
    def calculate_score(self) -> float:
        """Calculate compliance score."""
        if self.total_resources == 0:
            return 100.0
        
        # Weight violations by severity
        weighted_violations = (
            self.critical_count * 10 +
            self.high_count * 5 +
            self.medium_count * 2 +
            self.low_count * 1 +
            self.info_count * 0.1
        )
        
        # Max possible score (all resources critical)
        max_weight = self.total_resources * 10
        
        # Calculate score
        score = max(0, 100 - (weighted_violations / max_weight * 100))
        self.compliance_score = round(score, 2)
        return self.compliance_score
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "total_resources": self.total_resources,
            "compliant_resources": self.compliant_resources,
            "non_compliant_resources": self.non_compliant_resources,
            "compliance_score": self.compliance_score,
            "violation_counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "resources": [r.to_dict() for r in self.resources],
            "violations": [v.to_dict() for v in self.violations],
            "provider_breakdown": self.provider_breakdown,
            "category_breakdown": self.category_breakdown,
            "regulation_breakdown": self.regulation_breakdown,
            "analyzed_files": self.analyzed_files,
            "analyzed_at": self.analyzed_at.isoformat(),
            "analysis_duration_ms": self.analysis_duration_ms,
        }


# Default compliance policy rules
DEFAULT_POLICY_RULES: list[PolicyRule] = [
    # Encryption rules
    PolicyRule(
        id="ENC001",
        name="S3 Bucket Encryption",
        description="S3 buckets must have server-side encryption enabled",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "PCI-DSS", "SOC2"],
        requirement_ids=["GDPR-32", "HIPAA-164.312(a)(2)(iv)", "PCI-3.4"],
        resource_types=["aws_s3_bucket", "AWS::S3::Bucket"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Enable server-side encryption using AES-256 or AWS KMS",
        auto_remediation_available=True,
    ),
    PolicyRule(
        id="ENC002",
        name="RDS Encryption at Rest",
        description="RDS instances must have encryption at rest enabled",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "PCI-DSS"],
        requirement_ids=["GDPR-32", "HIPAA-164.312(a)(2)(iv)"],
        resource_types=["aws_db_instance", "AWS::RDS::DBInstance"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Enable storage encryption with AWS KMS",
        auto_remediation_available=True,
    ),
    PolicyRule(
        id="ENC003",
        name="EBS Volume Encryption",
        description="EBS volumes must be encrypted",
        severity=ViolationSeverity.MEDIUM,
        category=ComplianceCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "SOC2"],
        requirement_ids=["GDPR-32"],
        resource_types=["aws_ebs_volume", "AWS::EC2::Volume"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Enable EBS encryption with KMS key",
        auto_remediation_available=True,
    ),
    
    # Access control rules
    PolicyRule(
        id="IAM001",
        name="No Wildcard IAM Actions",
        description="IAM policies should not use wildcard (*) actions",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.ACCESS_CONTROL,
        regulations=["SOC2", "ISO27001"],
        requirement_ids=["SOC2-CC6.1", "ISO27001-A.9.2.3"],
        resource_types=["aws_iam_policy", "aws_iam_role_policy"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Specify explicit actions instead of wildcards",
        auto_remediation_available=False,
    ),
    PolicyRule(
        id="IAM002",
        name="No Public S3 Buckets",
        description="S3 buckets should not be publicly accessible",
        severity=ViolationSeverity.CRITICAL,
        category=ComplianceCategory.ACCESS_CONTROL,
        regulations=["GDPR", "HIPAA", "PCI-DSS", "SOC2"],
        requirement_ids=["GDPR-25", "HIPAA-164.312(c)(1)"],
        resource_types=["aws_s3_bucket", "aws_s3_bucket_public_access_block"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Enable public access block on S3 bucket",
        auto_remediation_available=True,
    ),
    
    # Network security rules
    PolicyRule(
        id="NET001",
        name="No Open Security Groups",
        description="Security groups should not allow unrestricted inbound access (0.0.0.0/0)",
        severity=ViolationSeverity.CRITICAL,
        category=ComplianceCategory.NETWORK_SECURITY,
        regulations=["PCI-DSS", "SOC2"],
        requirement_ids=["PCI-1.3", "SOC2-CC6.1"],
        resource_types=["aws_security_group", "AWS::EC2::SecurityGroup"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Restrict CIDR blocks to known IP ranges",
        auto_remediation_available=False,
    ),
    PolicyRule(
        id="NET002",
        name="HTTPS Only",
        description="Load balancers should only allow HTTPS traffic",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.NETWORK_SECURITY,
        regulations=["GDPR", "PCI-DSS"],
        requirement_ids=["GDPR-32", "PCI-4.1"],
        resource_types=["aws_lb_listener", "AWS::ElasticLoadBalancingV2::Listener"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Configure listener to use HTTPS with TLS 1.2+",
        auto_remediation_available=True,
    ),
    
    # Logging rules
    PolicyRule(
        id="LOG001",
        name="CloudTrail Enabled",
        description="CloudTrail should be enabled for all regions",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.LOGGING,
        regulations=["SOC2", "HIPAA", "PCI-DSS"],
        requirement_ids=["SOC2-CC7.2", "HIPAA-164.312(b)"],
        resource_types=["aws_cloudtrail"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Enable CloudTrail with multi-region and log file validation",
        auto_remediation_available=True,
    ),
    PolicyRule(
        id="LOG002",
        name="S3 Access Logging",
        description="S3 buckets should have access logging enabled",
        severity=ViolationSeverity.MEDIUM,
        category=ComplianceCategory.LOGGING,
        regulations=["SOC2", "HIPAA"],
        requirement_ids=["SOC2-CC7.2"],
        resource_types=["aws_s3_bucket"],
        providers=[CloudProvider.AWS],
        remediation_guidance="Enable server access logging to a separate bucket",
        auto_remediation_available=True,
    ),
    
    # Kubernetes rules
    PolicyRule(
        id="K8S001",
        name="No Privileged Containers",
        description="Containers should not run in privileged mode",
        severity=ViolationSeverity.CRITICAL,
        category=ComplianceCategory.ACCESS_CONTROL,
        regulations=["SOC2", "PCI-DSS"],
        requirement_ids=["SOC2-CC6.1"],
        resource_types=["Deployment", "StatefulSet", "DaemonSet", "Pod"],
        providers=[CloudProvider.KUBERNETES],
        remediation_guidance="Set securityContext.privileged to false",
        auto_remediation_available=True,
    ),
    PolicyRule(
        id="K8S002",
        name="Run as Non-Root",
        description="Containers should run as non-root user",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.ACCESS_CONTROL,
        regulations=["SOC2"],
        requirement_ids=["SOC2-CC6.1"],
        resource_types=["Deployment", "StatefulSet", "DaemonSet", "Pod"],
        providers=[CloudProvider.KUBERNETES],
        remediation_guidance="Set securityContext.runAsNonRoot to true",
        auto_remediation_available=True,
    ),
    PolicyRule(
        id="K8S003",
        name="Resource Limits Required",
        description="Containers should have CPU and memory limits",
        severity=ViolationSeverity.MEDIUM,
        category=ComplianceCategory.CONFIGURATION,
        regulations=["SOC2"],
        requirement_ids=["SOC2-CC7.1"],
        resource_types=["Deployment", "StatefulSet", "DaemonSet"],
        providers=[CloudProvider.KUBERNETES],
        remediation_guidance="Set resources.limits for CPU and memory",
        auto_remediation_available=True,
    ),
    PolicyRule(
        id="K8S004",
        name="No Latest Tag",
        description="Container images should not use 'latest' tag",
        severity=ViolationSeverity.MEDIUM,
        category=ComplianceCategory.CONFIGURATION,
        regulations=["SOC2"],
        requirement_ids=["SOC2-CC8.1"],
        resource_types=["Deployment", "StatefulSet", "DaemonSet", "Pod"],
        providers=[CloudProvider.KUBERNETES],
        remediation_guidance="Use specific version tags for container images",
        auto_remediation_available=False,
    ),
    PolicyRule(
        id="K8S005",
        name="Secrets Encrypted",
        description="Kubernetes secrets should be encrypted at rest",
        severity=ViolationSeverity.HIGH,
        category=ComplianceCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "PCI-DSS"],
        requirement_ids=["GDPR-32", "HIPAA-164.312(a)(2)(iv)"],
        resource_types=["Secret"],
        providers=[CloudProvider.KUBERNETES],
        remediation_guidance="Configure EncryptionConfiguration for secrets",
        auto_remediation_available=False,
    ),
]
