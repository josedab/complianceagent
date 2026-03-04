"""Compliance Certification Autopilot models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
from uuid import UUID, uuid4


class CertificationFramework(str, Enum):
    """Supported certification frameworks."""

    SOC2_TYPE2 = "soc2_type2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST_800_53 = "nist_800_53"


class CertificationPhase(str, Enum):
    """Phases of a certification journey."""

    GAP_ANALYSIS = "gap_analysis"
    EVIDENCE_COLLECTION = "evidence_collection"
    CONTROL_IMPLEMENTATION = "control_implementation"
    INTERNAL_AUDIT = "internal_audit"
    EXTERNAL_AUDIT = "external_audit"
    CERTIFICATION = "certification"


class EvidenceSourceType(str, Enum):
    """Types of evidence sources for auto-collection."""

    GIT_COMMIT = "git_commit"
    CI_CD_PIPELINE = "ci_cd_pipeline"
    ACCESS_LOG = "access_log"
    CLOUD_CONFIG = "cloud_config"
    MANUAL = "manual"


class GapStatus(str, Enum):
    """Status of a gap analysis item."""

    NOT_MET = "not_met"
    PARTIALLY_MET = "partially_met"
    MET = "met"
    EVIDENCE_COLLECTED = "evidence_collected"


@dataclass
class CertificationJourney:
    """Tracks progress through a certification process."""

    id: UUID = field(default_factory=uuid4)
    framework: CertificationFramework = CertificationFramework.SOC2_TYPE2
    organization_id: str = ""
    current_phase: CertificationPhase = CertificationPhase.GAP_ANALYSIS
    phases_completed: list[str] = field(default_factory=list)
    estimated_completion: datetime | None = None
    controls_total: int = 0
    controls_met: int = 0
    evidence_collected: int = 0
    readiness_score: float = 0.0


@dataclass
class ControlGap:
    """A gap identified in certification controls."""

    control_id: str = ""
    control_name: str = ""
    framework: CertificationFramework = CertificationFramework.SOC2_TYPE2
    status: str = "not_met"
    evidence_needed: list[str] = field(default_factory=list)
    remediation_steps: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0


@dataclass
class EvidenceSource:
    """Describes a source from which evidence can be auto-collected."""

    id: UUID = field(default_factory=uuid4)
    source_type: EvidenceSourceType = EvidenceSourceType.MANUAL
    name: str = ""
    description: str = ""
    endpoint: str = ""
    enabled: bool = True
    last_collected_at: datetime | None = None
    collection_frequency_hours: int = 24


@dataclass
class AutoCollectedEvidence:
    """A record of evidence automatically collected from a source."""

    id: UUID = field(default_factory=uuid4)
    journey_id: UUID = field(default_factory=uuid4)
    control_id: str = ""
    source_type: EvidenceSourceType = EvidenceSourceType.MANUAL
    source_name: str = ""
    content: str = ""
    content_hash: str = ""
    collected_at: datetime | None = None
    verified: bool = False
    metadata: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of evidence content for integrity verification."""
        self.content_hash = sha256(self.content.encode()).hexdigest()
        return self.content_hash


@dataclass
class GapAnalysisItem:
    """Detailed gap analysis item with mapping and auto-collection metadata."""

    id: UUID = field(default_factory=uuid4)
    journey_id: UUID = field(default_factory=uuid4)
    control_id: str = ""
    control_name: str = ""
    framework: CertificationFramework = CertificationFramework.SOC2_TYPE2
    status: GapStatus = GapStatus.NOT_MET
    evidence_needed: list[str] = field(default_factory=list)
    evidence_collected: list[UUID] = field(default_factory=list)
    remediation_steps: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    auto_collectible: bool = False
    mapped_sources: list[EvidenceSourceType] = field(default_factory=list)
    cross_framework_mappings: list[str] = field(default_factory=list)


@dataclass
class AuditorPortalSession:
    """Read-only auditor portal session with time-limited access."""

    id: UUID = field(default_factory=uuid4)
    journey_id: UUID = field(default_factory=uuid4)
    auditor_email: str = ""
    auditor_name: str = ""
    access_token: str = ""
    created_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
    accessed_controls: list[str] = field(default_factory=list)
    last_accessed_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        if not self.expires_at:
            return True
        from datetime import UTC

        return datetime.now(UTC) > self.expires_at


@dataclass
class CertificationReadinessReport:
    """Certification readiness report with gap and remediation summaries."""

    id: UUID = field(default_factory=uuid4)
    journey_id: UUID = field(default_factory=uuid4)
    framework: CertificationFramework = CertificationFramework.SOC2_TYPE2
    generated_at: datetime | None = None
    overall_readiness_score: float = 0.0
    auto_collection_rate: float = 0.0
    controls_total: int = 0
    controls_met: int = 0
    controls_partially_met: int = 0
    controls_not_met: int = 0
    total_evidence_collected: int = 0
    auto_collected_evidence_count: int = 0
    manual_evidence_count: int = 0
    gap_summary: list[dict] = field(default_factory=list)
    remediation_summary: list[dict] = field(default_factory=list)
    estimated_remaining_hours: float = 0.0
    target_auto_collection_rate: float = 80.0
    meets_auto_collection_target: bool = False
