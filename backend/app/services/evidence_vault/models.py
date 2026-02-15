"""Compliance Evidence Vault models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EvidenceType(str, Enum):
    """Type of compliance evidence."""

    CODE_REVIEW = "code_review"
    SCAN_RESULT = "scan_result"
    POLICY_DOCUMENT = "policy_document"
    AUDIT_LOG = "audit_log"
    CONFIGURATION = "configuration"
    TEST_RESULT = "test_result"
    APPROVAL_RECORD = "approval_record"
    TRAINING_RECORD = "training_record"
    INCIDENT_REPORT = "incident_report"


class ControlFramework(str, Enum):
    """Compliance control frameworks."""

    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"
    GDPR = "gdpr"


class AuditorRole(str, Enum):
    """Auditor access roles."""

    VIEWER = "viewer"
    REVIEWER = "reviewer"
    LEAD_AUDITOR = "lead_auditor"


@dataclass
class EvidenceItem:
    """A single piece of compliance evidence."""

    id: UUID = field(default_factory=uuid4)
    evidence_type: EvidenceType = EvidenceType.SCAN_RESULT
    title: str = ""
    description: str = ""
    content_hash: str = ""
    s3_key: str = ""
    framework: ControlFramework = ControlFramework.SOC2
    control_id: str = ""
    control_name: str = ""
    collected_at: datetime | None = None
    source: str = ""
    metadata: dict = field(default_factory=dict)
    previous_hash: str = ""


@dataclass
class EvidenceChain:
    """Immutable chain of evidence items with integrity verification."""

    id: UUID = field(default_factory=uuid4)
    framework: ControlFramework = ControlFramework.SOC2
    items: list[EvidenceItem] = field(default_factory=list)
    chain_hash: str = ""
    verified: bool = False
    last_verified_at: datetime | None = None

    @property
    def total_items(self) -> int:
        return len(self.items)


@dataclass
class ControlMapping:
    """Mapping between framework control and evidence."""

    control_id: str = ""
    control_name: str = ""
    framework: ControlFramework = ControlFramework.SOC2
    evidence_ids: list[UUID] = field(default_factory=list)
    coverage_pct: float = 0.0
    status: str = "incomplete"


@dataclass
class AuditorSession:
    """Read-only auditor portal session."""

    id: UUID = field(default_factory=uuid4)
    auditor_email: str = ""
    auditor_name: str = ""
    firm: str = ""
    role: AuditorRole = AuditorRole.VIEWER
    frameworks: list[ControlFramework] = field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime | None = None
    is_active: bool = True


@dataclass
class AuditReport:
    """Generated audit report."""

    id: UUID = field(default_factory=uuid4)
    framework: ControlFramework = ControlFramework.SOC2
    title: str = ""
    period_start: datetime | None = None
    period_end: datetime | None = None
    total_controls: int = 0
    controls_with_evidence: int = 0
    coverage_pct: float = 0.0
    control_mappings: list[ControlMapping] = field(default_factory=list)
    generated_at: datetime | None = None
    report_format: str = "pdf"


@dataclass
class CoverageMetrics:
    """Detailed coverage metrics for a compliance framework."""

    framework: str = ""
    total_controls: int = 0
    controls_with_evidence: int = 0
    controls_partial: int = 0
    controls_missing: int = 0
    coverage_percentage: float = 0.0
    evidence_freshness_avg_days: float = 0.0
    stale_evidence_count: int = 0
    control_breakdown: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "total_controls": self.total_controls,
            "controls_with_evidence": self.controls_with_evidence,
            "controls_partial": self.controls_partial,
            "controls_missing": self.controls_missing,
            "coverage_percentage": self.coverage_percentage,
            "evidence_freshness_avg_days": self.evidence_freshness_avg_days,
            "stale_evidence_count": self.stale_evidence_count,
            "control_breakdown": self.control_breakdown,
        }


@dataclass
class ChainVerificationResult:
    """Result of verifying the evidence hash chain."""

    framework: str = ""
    chain_length: int = 0
    is_valid: bool = True
    verified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    invalid_links: list[dict[str, str]] = field(default_factory=list)
    tamper_detected: bool = False
    verification_time_ms: float = 0.0
    hash_algorithm: str = "SHA-256"
    root_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "chain_length": self.chain_length,
            "is_valid": self.is_valid,
            "verified_at": self.verified_at.isoformat(),
            "invalid_links": self.invalid_links,
            "tamper_detected": self.tamper_detected,
            "verification_time_ms": self.verification_time_ms,
            "hash_algorithm": self.hash_algorithm,
            "root_hash": self.root_hash,
        }


@dataclass
class EvidenceGap:
    """An identified gap in evidence coverage."""

    control_id: str = ""
    control_name: str = ""
    framework: str = ""
    gap_type: str = "missing"  # missing, stale, insufficient
    last_evidence_date: str | None = None
    required_evidence_types: list[str] = field(default_factory=list)
    remediation_suggestion: str = ""
    priority: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_id": self.control_id,
            "control_name": self.control_name,
            "framework": self.framework,
            "gap_type": self.gap_type,
            "last_evidence_date": self.last_evidence_date,
            "required_evidence_types": self.required_evidence_types,
            "remediation_suggestion": self.remediation_suggestion,
            "priority": self.priority,
        }


@dataclass
class BlockchainAnchor:
    """A blockchain anchor for evidence chain verification."""

    id: UUID = field(default_factory=uuid4)
    framework: str = ""
    chain_hash: str = ""
    evidence_count: int = 0
    anchor_hash: str = ""
    blockchain_network: str = "polygon"
    transaction_id: str = ""
    block_number: int = 0
    status: str = "pending"  # pending, confirmed, failed
    anchored_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confirmed_at: datetime | None = None
    cost_usd: float = 0.0


@dataclass
class BatchVerificationResult:
    """Result of verifying multiple evidence items at once."""

    id: UUID = field(default_factory=uuid4)
    items_verified: int = 0
    items_valid: int = 0
    items_invalid: int = 0
    items_missing: int = 0
    chain_intact: bool = True
    blockchain_verified: bool = False
    invalid_items: list[dict[str, Any]] = field(default_factory=list)
    verification_duration_ms: float = 0.0
    verified_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AuditTimelineEvent:
    """An event in the audit timeline."""

    id: UUID = field(default_factory=uuid4)
    event_type: str = ""  # evidence_stored, chain_verified, anchor_created, session_started, report_generated, gap_identified
    description: str = ""
    framework: str = ""
    actor: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
