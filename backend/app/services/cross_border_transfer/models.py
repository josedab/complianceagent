"""Cross-Border Data Transfer Automation models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TransferMechanism(str, Enum):
    """Legal mechanism for cross-border data transfer."""

    SCC = "standard_contractual_clauses"
    BCR = "binding_corporate_rules"
    ADEQUACY = "adequacy_decision"
    DEROGATION = "derogation"
    CONSENT = "explicit_consent"
    ENCRYPTION = "supplementary_encryption"


class AdequacyStatus(str, Enum):
    """Status of an adequacy decision."""

    ADEQUATE = "adequate"
    PARTIALLY_ADEQUATE = "partially_adequate"
    INADEQUATE = "inadequate"
    PENDING_REVIEW = "pending_review"
    INVALIDATED = "invalidated"


class TransferRisk(str, Enum):
    """Risk level for a data transfer."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Jurisdiction:
    """A regulatory jurisdiction."""

    code: str = ""
    name: str = ""
    region: str = ""
    adequacy_status: AdequacyStatus = AdequacyStatus.PENDING_REVIEW
    data_protection_law: str = ""
    supervisory_authority: str = ""
    last_reviewed: datetime | None = None


@dataclass
class DataFlow:
    """A cross-border data flow between two jurisdictions."""

    id: UUID = field(default_factory=uuid4)
    source_jurisdiction: str = ""
    destination_jurisdiction: str = ""
    data_categories: list[str] = field(default_factory=list)
    data_subjects: list[str] = field(default_factory=list)
    transfer_mechanism: TransferMechanism = TransferMechanism.SCC
    purpose: str = ""
    volume_estimate: str = ""
    risk_level: TransferRisk = TransferRisk.MEDIUM
    is_compliant: bool = False
    services_involved: list[str] = field(default_factory=list)
    detected_at: datetime | None = None


@dataclass
class SCCDocument:
    """A Standard Contractual Clauses document."""

    id: UUID = field(default_factory=uuid4)
    data_flow_id: UUID = field(default_factory=uuid4)
    module_type: str = "module_2"  # controller-to-processor
    version: str = "2021/914"
    parties: dict[str, str] = field(default_factory=dict)
    annexes: list[dict[str, Any]] = field(default_factory=list)
    supplementary_measures: list[str] = field(default_factory=list)
    status: str = "draft"
    generated_at: datetime | None = None
    last_updated: datetime | None = None
    valid_until: datetime | None = None


@dataclass
class AdequacyDecision:
    """An EDPB/EC adequacy decision record."""

    id: UUID = field(default_factory=uuid4)
    country_code: str = ""
    country_name: str = ""
    status: AdequacyStatus = AdequacyStatus.PENDING_REVIEW
    decision_reference: str = ""
    decision_date: datetime | None = None
    review_date: datetime | None = None
    scope: str = ""
    conditions: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class TransferImpactAssessment:
    """Transfer Impact Assessment (TIA) for a data flow."""

    id: UUID = field(default_factory=uuid4)
    data_flow_id: UUID = field(default_factory=uuid4)
    risk_level: TransferRisk = TransferRisk.MEDIUM
    legal_basis_adequate: bool = False
    supplementary_measures_needed: list[str] = field(default_factory=list)
    government_access_risk: str = "medium"
    encryption_in_transit: bool = True
    encryption_at_rest: bool = True
    pseudonymization_applied: bool = False
    recommendations: list[str] = field(default_factory=list)
    assessed_at: datetime | None = None


@dataclass
class TransferAlert:
    """Alert for changes affecting data transfers."""

    id: UUID = field(default_factory=uuid4)
    alert_type: str = ""  # adequacy_change, scc_expiry, new_regulation
    severity: TransferRisk = TransferRisk.MEDIUM
    jurisdiction: str = ""
    title: str = ""
    description: str = ""
    affected_flows: list[str] = field(default_factory=list)
    recommended_action: str = ""
    created_at: datetime | None = None
    acknowledged: bool = False


@dataclass
class TransferReport:
    """Summary report of cross-border data transfers."""

    total_flows: int = 0
    compliant_flows: int = 0
    non_compliant_flows: int = 0
    flows_by_mechanism: dict[str, int] = field(default_factory=dict)
    flows_by_risk: dict[str, int] = field(default_factory=dict)
    jurisdictions_involved: list[str] = field(default_factory=list)
    active_sccs: int = 0
    pending_tias: int = 0
    active_alerts: int = 0
    generated_at: datetime | None = None
