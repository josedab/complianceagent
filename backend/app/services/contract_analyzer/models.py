"""Contract Analyzer models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ContractType(str, Enum):
    """Types of contracts for analysis."""

    DPA = "dpa"
    NDA = "nda"
    SERVICE_AGREEMENT = "service_agreement"
    VENDOR_CONTRACT = "vendor_contract"
    SUB_PROCESSOR = "sub_processor"


class ObligationStatus(str, Enum):
    """Status of a contractual obligation."""

    MET = "met"
    PARTIALLY_MET = "partially_met"
    NOT_MET = "not_met"
    NOT_APPLICABLE = "not_applicable"


class ComplianceGapSeverity(str, Enum):
    """Severity of a compliance gap."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExtractedObligation:
    """An obligation extracted from a contract."""

    id: UUID = field(default_factory=uuid4)
    clause_ref: str = ""
    obligation_text: str = ""
    framework: str = ""
    article_ref: str = ""
    obligation_type: str = "must"
    deadline: str = ""


@dataclass
class ContractAnalysis:
    """Result of analyzing a contract for compliance obligations."""

    id: UUID = field(default_factory=uuid4)
    contract_name: str = ""
    contract_type: ContractType = ContractType.DPA
    vendor: str = ""
    obligations: list[ExtractedObligation] = field(default_factory=list)
    compliance_gaps: list[dict] = field(default_factory=list)
    gap_count: int = 0
    obligations_met: int = 0
    total_obligations: int = 0
    coverage_pct: float = 0.0
    analyzed_at: datetime | None = None


@dataclass
class ContractStats:
    """Aggregate statistics for contract analyses."""

    total_analyses: int = 0
    by_contract_type: dict = field(default_factory=dict)
    avg_obligations: int = 0
    avg_coverage_pct: float = 0.0
    total_gaps_found: int = 0
