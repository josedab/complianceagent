"""Regulatory filing models for compliance submissions and authority management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class FilingType(str, Enum):
    """Types of regulatory filings."""

    gdpr_art30 = "gdpr_art30"
    dpia_submission = "dpia_submission"
    breach_notification = "breach_notification"
    annual_report = "annual_report"
    registration = "registration"


class FilingStatus(str, Enum):
    """Status of a regulatory filing."""

    draft = "draft"
    ready = "ready"
    submitted = "submitted"
    acknowledged = "acknowledged"
    rejected = "rejected"


class AuthorityType(str, Enum):
    """Types of regulatory authorities."""

    dpa = "dpa"
    sec = "sec"
    hhs = "hhs"
    pci_council = "pci_council"
    national_authority = "national_authority"


@dataclass
class RegulatoryAuthority:
    """A regulatory authority that accepts filings."""

    id: str = ""
    name: str = ""
    authority_type: AuthorityType = AuthorityType.dpa
    jurisdiction: str = ""
    api_endpoint: str = ""
    accepts_electronic: bool = True


@dataclass
class RegulatoryFiling:
    """A regulatory filing submission."""

    id: UUID = field(default_factory=uuid4)
    filing_type: FilingType = FilingType.gdpr_art30
    authority_id: str = ""
    title: str = ""
    content: dict = field(default_factory=dict)
    status: FilingStatus = FilingStatus.draft
    reference_number: str = ""
    submitted_at: datetime | None = None
    acknowledged_at: datetime | None = None
    deadline: datetime | None = None


@dataclass
class FilingTemplate:
    """A template for generating regulatory filings."""

    id: str = ""
    filing_type: FilingType = FilingType.gdpr_art30
    authority_id: str = ""
    template_fields: list[str] = field(default_factory=list)
    required_attachments: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class FilingStats:
    """Aggregate filing statistics."""

    total_filings: int = 0
    by_type: dict = field(default_factory=dict)
    by_status: dict = field(default_factory=dict)
    on_time_pct: float = 0.0
    authorities_connected: int = 0
