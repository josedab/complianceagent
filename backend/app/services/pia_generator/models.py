"""Privacy Impact Assessment Generator models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PIAStatus(str, Enum):
    """Status of a PIA document."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class DataCategory(str, Enum):
    """Categories of personal data."""

    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    SPECIAL_CATEGORY = "special_category"
    ANONYMIZED = "anonymized"
    PSEUDONYMIZED = "pseudonymized"


class LegalBasis(str, Enum):
    """Legal basis for data processing under GDPR."""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTEREST = "vital_interest"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTEREST = "legitimate_interest"


@dataclass
class DataFlow:
    """A data flow within a privacy impact assessment."""

    id: UUID = field(default_factory=uuid4)
    source: str = ""
    destination: str = ""
    data_categories: list[DataCategory] = field(default_factory=list)
    purpose: str = ""
    legal_basis: LegalBasis = LegalBasis.CONSENT
    retention_period: str = ""
    cross_border: bool = False
    safeguards: list[str] = field(default_factory=list)


@dataclass
class PIADocument:
    """A complete Privacy Impact Assessment document."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    repo: str = ""
    status: PIAStatus = PIAStatus.DRAFT
    data_flows: list[DataFlow] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    mitigations: list[dict] = field(default_factory=list)
    dpo_approved: bool = False
    approved_by: str = ""
    overall_risk_level: str = "medium"
    generated_at: datetime | None = None
    approved_at: datetime | None = None


@dataclass
class PIAStats:
    """Statistics for PIA assessments."""

    total_assessments: int = 0
    by_status: dict = field(default_factory=dict)
    by_risk_level: dict = field(default_factory=dict)
    avg_data_flows_per_pia: float = 0.0
    cross_border_flows: int = 0
