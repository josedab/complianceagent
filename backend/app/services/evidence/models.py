"""Data models for Multi-Framework Evidence Auto-Generator."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EvidenceType(str, Enum):
    """Types of compliance evidence."""
    
    DOCUMENT = "document"
    CODE_ARTIFACT = "code_artifact"
    LOG = "log"
    CONFIGURATION = "configuration"
    SCREENSHOT = "screenshot"
    ATTESTATION = "attestation"
    POLICY = "policy"
    PROCEDURE = "procedure"
    TEST_RESULT = "test_result"
    AUDIT_TRAIL = "audit_trail"


class EvidenceStatus(str, Enum):
    """Status of evidence collection."""
    
    PENDING = "pending"
    COLLECTING = "collecting"
    COLLECTED = "collected"
    VALIDATED = "validated"
    EXPIRED = "expired"
    FAILED = "failed"


class Framework(str, Enum):
    """Supported compliance frameworks."""
    
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI-DSS"
    SOX = "SOX"
    NIST_CSF = "NIST-CSF"
    FEDRAMP = "FedRAMP"
    CCPA = "CCPA"
    EU_AI_ACT = "EU-AI-Act"


@dataclass
class Control:
    """A compliance control/requirement."""
    
    control_id: str
    framework: Framework
    title: str
    description: str = ""
    category: str = ""
    sub_controls: list[str] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)
    guidance: str = ""


@dataclass
class EvidenceItem:
    """A single piece of compliance evidence."""
    
    id: UUID = field(default_factory=uuid4)
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    title: str = ""
    description: str = ""
    source: str = ""  # Where evidence was collected from
    content: str = ""  # Actual evidence content or reference
    content_hash: str = ""  # For integrity verification
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by: str = "system"
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    file_path: str | None = None
    url: str | None = None
    
    # Control mappings
    controls: list[str] = field(default_factory=list)  # Control IDs this evidence satisfies
    frameworks: list[Framework] = field(default_factory=list)


@dataclass
class EvidenceCollection:
    """A collection of evidence for a control or audit."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    framework: Framework = Framework.SOC2
    control_id: str = ""
    control_title: str = ""
    status: EvidenceStatus = EvidenceStatus.PENDING
    
    # Evidence items
    evidence: list[EvidenceItem] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    validated_at: datetime | None = None
    validated_by: str | None = None
    
    # Gaps
    missing_evidence: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ControlMapping:
    """Mapping between controls across frameworks."""
    
    source_framework: Framework
    source_control_id: str
    target_framework: Framework
    target_control_id: str
    mapping_type: str = "equivalent"  # equivalent, partial, related
    notes: str = ""


@dataclass
class EvidenceReport:
    """Generated evidence report for audits."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    title: str = ""
    frameworks: list[Framework] = field(default_factory=list)
    
    # Summary
    total_controls: int = 0
    controls_with_evidence: int = 0
    controls_missing_evidence: int = 0
    coverage_percentage: float = 0.0
    
    # Details
    collections: list[EvidenceCollection] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.utcnow)
    generated_by: str = "system"
    report_format: str = "json"  # json, pdf, excel
    
    # Export info
    file_path: str | None = None
    download_url: str | None = None


@dataclass
class CollectionConfig:
    """Configuration for evidence collection."""
    
    organization_id: UUID
    frameworks: list[Framework] = field(default_factory=list)
    
    # Sources to collect from
    github_repos: list[str] = field(default_factory=list)
    cloud_providers: list[str] = field(default_factory=list)  # aws, gcp, azure
    document_sources: list[str] = field(default_factory=list)
    
    # Collection options
    include_code_artifacts: bool = True
    include_logs: bool = True
    include_configs: bool = True
    auto_refresh: bool = False
    refresh_interval_days: int = 30
