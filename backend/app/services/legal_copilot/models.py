"""Legal Copilot models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DocumentType(str, Enum):
    """Types of legal documents."""

    DPA_DRAFT = "dpa_draft"
    LEGAL_MEMO = "legal_memo"
    CONTRACT_REVIEW = "contract_review"
    REGULATORY_BRIEF = "regulatory_brief"
    COMPLIANCE_OPINION = "compliance_opinion"


class ReviewStatus(str, Enum):
    """Status of document review."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SENT = "sent"


@dataclass
class LegalDocument:
    """A legal document generated or reviewed by the copilot."""

    id: UUID = field(default_factory=uuid4)
    doc_type: DocumentType = DocumentType.LEGAL_MEMO
    title: str = ""
    content: str = ""
    citations: list[dict] = field(default_factory=list)
    framework: str = ""
    jurisdiction: str = ""
    status: ReviewStatus = ReviewStatus.DRAFT
    author: str = ""
    reviewer: str = ""
    created_at: datetime | None = None
    approved_at: datetime | None = None


@dataclass
class LegalCitation:
    """A citation to a regulation or legal source."""

    regulation: str = ""
    article: str = ""
    text: str = ""
    url: str = ""


@dataclass
class ContractClause:
    """A contract clause with risk assessment."""

    id: UUID = field(default_factory=uuid4)
    clause_type: str = ""
    text: str = ""
    risk_level: str = ""
    recommendation: str = ""
    framework: str = ""


@dataclass
class LegalCopilotStats:
    """Statistics for the legal copilot service."""

    total_documents: int = 0
    by_type: dict = field(default_factory=dict)
    approved: int = 0
    avg_citations_per_doc: float = 0.0
    frameworks_covered: list[str] = field(default_factory=list)
