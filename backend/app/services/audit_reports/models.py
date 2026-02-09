"""Audit Report Generation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class AuditFramework(str, Enum):
    """Supported compliance audit frameworks."""

    SOC2_TYPE2 = "soc2_type2"
    ISO_27001 = "iso_27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    NIST_CSF = "nist_csf"
    EU_AI_ACT = "eu_ai_act"


class ControlStatus(str, Enum):
    """Assessment status for a single control."""

    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    NOT_ASSESSED = "not_assessed"


class EvidenceType(str, Enum):
    """Type of audit evidence artifact."""

    CODE_COMMIT = "code_commit"
    POLICY_DOCUMENT = "policy_document"
    ACCESS_LOG = "access_log"
    TRAINING_RECORD = "training_record"
    INCIDENT_LOG = "incident_log"
    CONFIGURATION = "configuration"
    SCREENSHOT = "screenshot"
    TEST_RESULT = "test_result"


class ReportFormat(str, Enum):
    """Output format for audit reports."""

    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class AuditorRole(str, Enum):
    """Role assigned to an external auditor."""

    LEAD_AUDITOR = "lead_auditor"
    AUDITOR = "auditor"
    OBSERVER = "observer"


@dataclass
class EvidenceItem:
    """A single piece of audit evidence."""

    id: UUID
    type: EvidenceType
    title: str
    description: str
    source: str
    url: str
    collected_at: datetime
    verified: bool = False


@dataclass
class ControlResult:
    """Assessment result for a single compliance control."""

    control_id: str
    control_name: str
    control_description: str
    category: str
    status: ControlStatus
    evidence: list[EvidenceItem] = field(default_factory=list)
    findings: str = ""
    remediation: str = ""
    last_assessed: datetime | None = None


@dataclass
class EvidenceSummary:
    """Aggregate statistics on evidence collected for a report."""

    total_controls: int = 0
    compliant: int = 0
    partially_compliant: int = 0
    non_compliant: int = 0
    not_applicable: int = 0
    coverage_pct: float = 0.0
    evidence_count: int = 0
    auto_collected: int = 0
    manual_uploaded: int = 0


@dataclass
class ControlGap:
    """A gap identified during control assessment."""

    control_id: str
    control_name: str
    status: ControlStatus
    severity: str
    remediation_steps: list[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    deadline: datetime | None = None


@dataclass
class AuditReport:
    """A generated audit-ready compliance report."""

    id: UUID
    org_id: UUID
    framework: AuditFramework
    title: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_status: ControlStatus
    control_results: list[ControlResult] = field(default_factory=list)
    evidence_summary: EvidenceSummary = field(default_factory=EvidenceSummary)
    executive_summary: str = ""
    gaps: list[ControlGap] = field(default_factory=list)
    format: ReportFormat = ReportFormat.PDF


@dataclass
class AuditorPortalSession:
    """An authenticated session for external auditor access."""

    id: UUID
    auditor_email: str
    auditor_name: str
    role: AuditorRole
    org_id: UUID
    framework: AuditFramework
    created_at: datetime
    expires_at: datetime
    access_token: str
    permissions: list[str] = field(default_factory=list)


@dataclass
class AuditorComment:
    """A comment left by an auditor on a control."""

    id: UUID
    session_id: UUID
    control_id: str
    comment: str
    created_at: datetime
    requires_response: bool = False


@dataclass
class FrameworkDefinition:
    """Metadata describing a supported audit framework."""

    framework: AuditFramework
    version: str
    total_controls: int
    categories: list[str] = field(default_factory=list)
    description: str = ""
