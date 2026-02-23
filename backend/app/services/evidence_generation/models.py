"""Automated Evidence Generation models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EvidenceFramework(str, Enum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST = "nist"


class ControlStatus(str, Enum):
    MET = "met"
    PARTIALLY_MET = "partially_met"
    NOT_MET = "not_met"
    NOT_APPLICABLE = "not_applicable"


class EvidenceFreshness(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"


@dataclass
class ControlMapping:
    control_id: str = ""
    control_name: str = ""
    framework: EvidenceFramework = EvidenceFramework.SOC2
    status: ControlStatus = ControlStatus.NOT_MET
    evidence_count: int = 0
    last_evidence_at: datetime | None = None
    freshness: EvidenceFreshness = EvidenceFreshness.FRESH
    code_refs: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class EvidenceItem:
    id: UUID = field(default_factory=uuid4)
    control_id: str = ""
    framework: EvidenceFramework = EvidenceFramework.SOC2
    title: str = ""
    description: str = ""
    evidence_type: str = "automated"
    content: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime | None = None
    expires_at: datetime | None = None
    freshness: EvidenceFreshness = EvidenceFreshness.FRESH


@dataclass
class EvidencePackage:
    id: UUID = field(default_factory=uuid4)
    framework: EvidenceFramework = EvidenceFramework.SOC2
    controls_total: int = 0
    controls_met: int = 0
    coverage_pct: float = 0.0
    items: list[EvidenceItem] = field(default_factory=list)
    control_mappings: list[ControlMapping] = field(default_factory=list)
    generated_at: datetime | None = None
    valid_until: datetime | None = None


@dataclass
class EvidenceStats:
    total_items: int = 0
    by_framework: dict[str, int] = field(default_factory=dict)
    by_freshness: dict[str, int] = field(default_factory=dict)
    overall_coverage_pct: float = 0.0
    stale_items: int = 0
