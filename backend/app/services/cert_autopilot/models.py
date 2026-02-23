"""Compliance Certification Autopilot models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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
