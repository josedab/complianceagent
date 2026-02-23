"""Automated Certification Pipeline models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class CertFramework(str, Enum):
    SOC2_TYPE2 = "soc2_type2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"


class CertStage(str, Enum):
    GAP_ANALYSIS = "gap_analysis"
    EVIDENCE_COLLECTION = "evidence_collection"
    REPORT_GENERATION = "report_generation"
    AUDITOR_REVIEW = "auditor_review"
    REMEDIATION = "remediation"
    CERTIFICATION = "certification"
    COMPLETED = "completed"


class GapStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"


@dataclass
class CertificationRun:
    id: UUID = field(default_factory=uuid4)
    framework: CertFramework = CertFramework.SOC2_TYPE2
    stage: CertStage = CertStage.GAP_ANALYSIS
    stages_completed: list[str] = field(default_factory=list)
    total_controls: int = 0
    controls_met: int = 0
    gaps_found: int = 0
    gaps_resolved: int = 0
    evidence_collected: int = 0
    readiness_pct: float = 0.0
    auditor_assigned: str = ""
    target_date: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class ControlGap:
    id: UUID = field(default_factory=uuid4)
    run_id: UUID = field(default_factory=uuid4)
    control_id: str = ""
    control_name: str = ""
    gap_description: str = ""
    status: GapStatus = GapStatus.OPEN
    remediation_plan: str = ""
    evidence_needed: list[str] = field(default_factory=list)
    priority: str = "medium"


@dataclass
class CertReport:
    id: UUID = field(default_factory=uuid4)
    run_id: UUID = field(default_factory=uuid4)
    framework: str = ""
    readiness_pct: float = 0.0
    controls_summary: dict[str, int] = field(default_factory=dict)
    open_gaps: int = 0
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class CertPipelineStats:
    total_runs: int = 0
    by_framework: dict[str, int] = field(default_factory=dict)
    by_stage: dict[str, int] = field(default_factory=dict)
    avg_readiness_pct: float = 0.0
    total_gaps_found: int = 0
    total_gaps_resolved: int = 0
