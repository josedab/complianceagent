"""Compliance Evidence Vault models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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
