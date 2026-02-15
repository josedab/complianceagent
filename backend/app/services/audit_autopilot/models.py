"""Audit Preparation Autopilot models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class AuditFramework(str, Enum):
    SOC2_TYPE2 = "soc2_type2"
    ISO_27001 = "iso_27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    SOX = "sox"


class GapSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceStatus(str, Enum):
    COLLECTED = "collected"
    PARTIAL = "partial"
    MISSING = "missing"
    STALE = "stale"


@dataclass
class ControlMapping:
    """Mapping of a control to collected evidence."""
    control_id: str = ""
    control_name: str = ""
    description: str = ""
    evidence_status: EvidenceStatus = EvidenceStatus.MISSING
    evidence_items: list[str] = field(default_factory=list)
    gap_description: str | None = None
    gap_severity: GapSeverity | None = None
    remediation_task: str | None = None


@dataclass
class GapAnalysis:
    """Gap analysis results for an audit framework."""
    id: UUID = field(default_factory=uuid4)
    framework: AuditFramework = AuditFramework.SOC2_TYPE2
    total_controls: int = 0
    controls_met: int = 0
    controls_partial: int = 0
    controls_missing: int = 0
    readiness_score: float = 0.0
    control_mappings: list[ControlMapping] = field(default_factory=list)
    critical_gaps: list[str] = field(default_factory=list)
    estimated_remediation_hours: float = 0.0
    analyzed_at: datetime | None = None

    @property
    def readiness_percentage(self) -> float:
        if self.total_controls == 0:
            return 0.0
        return (self.controls_met / self.total_controls) * 100


@dataclass
class EvidencePackage:
    """Auto-generated evidence package for auditors."""
    id: UUID = field(default_factory=uuid4)
    framework: AuditFramework = AuditFramework.SOC2_TYPE2
    title: str = ""
    total_items: int = 0
    controls_covered: int = 0
    total_controls: int = 0
    coverage_percent: float = 0.0
    sections: list[dict] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class AuditReadinessReport:
    """Complete audit readiness report."""
    id: UUID = field(default_factory=uuid4)
    framework: AuditFramework = AuditFramework.SOC2_TYPE2
    gap_analysis: GapAnalysis = field(default_factory=GapAnalysis)
    evidence_package: EvidencePackage | None = None
    overall_readiness: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    estimated_prep_weeks: float = 0.0
    generated_at: datetime | None = None


class RemediationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"


@dataclass
class EvidenceTimelineEntry:
    """An entry in the evidence collection timeline."""
    id: UUID = field(default_factory=uuid4)
    framework: AuditFramework = AuditFramework.SOC2_TYPE2
    control_id: str = ""
    control_name: str = ""
    event_type: str = ""  # collected, updated, reviewed, expired
    description: str = ""
    evidence_items: list[str] = field(default_factory=list)
    actor: str = ""
    timestamp: datetime | None = None


@dataclass
class RemediationTracker:
    """Track remediation of a control gap."""
    id: UUID = field(default_factory=uuid4)
    framework: AuditFramework = AuditFramework.SOC2_TYPE2
    control_id: str = ""
    control_name: str = ""
    gap_description: str = ""
    severity: GapSeverity = GapSeverity.MEDIUM
    status: RemediationStatus = RemediationStatus.NOT_STARTED
    assignee: str = ""
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    due_date: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str = ""
