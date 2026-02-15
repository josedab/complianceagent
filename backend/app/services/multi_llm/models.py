"""Multi-LLM Regulatory Parsing Engine models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    COPILOT = "copilot"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class ConsensusStrategy(str, Enum):
    """Strategy for combining multi-model results."""

    MAJORITY_VOTE = "majority_vote"
    HIGHEST_CONFIDENCE = "highest_confidence"
    WEIGHTED_AVERAGE = "weighted_average"
    UNANIMOUS = "unanimous"


class ParseStatus(str, Enum):
    """Status of a parsing request."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DIVERGENT = "divergent"
    FAILED = "failed"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    provider: LLMProvider = LLMProvider.COPILOT
    model_name: str = ""
    api_key: str = ""
    base_url: str = ""
    max_tokens: int = 4096
    temperature: float = 0.1
    weight: float = 1.0
    enabled: bool = True
    timeout_seconds: int = 30


@dataclass
class ProviderResult:
    """Parsing result from a single provider."""

    provider: LLMProvider = LLMProvider.COPILOT
    model_name: str = ""
    obligations: list[dict] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    error: str | None = None
    raw_response: dict = field(default_factory=dict)


@dataclass
class ConsensusResult:
    """Consensus result from multi-model parsing."""

    id: UUID = field(default_factory=uuid4)
    status: ParseStatus = ParseStatus.PENDING
    strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE

    # Provider results
    provider_results: list[ProviderResult] = field(default_factory=list)

    # Consensus output
    obligations: list[dict] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    confidence: float = 0.0

    # Agreement metrics
    agreement_score: float = 0.0
    divergent_items: list[dict] = field(default_factory=list)
    needs_human_review: bool = False

    total_latency_ms: float = 0.0
    completed_at: datetime | None = None


@dataclass
class MultiLLMConfig:
    """Global multi-LLM configuration."""

    providers: list[ProviderConfig] = field(default_factory=list)
    consensus_strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE
    min_providers: int = 2
    divergence_threshold: float = 0.3
    fallback_to_single: bool = True


@dataclass
class ProviderHealthMetrics:
    """Health and performance metrics for an LLM provider."""

    provider: LLMProvider = LLMProvider.COPILOT
    model_name: str = ""
    status: str = "healthy"
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    success_rate: float = 1.0
    total_requests: int = 0
    failed_requests: int = 0
    last_error: str | None = None
    last_check: datetime | None = None
    cost_per_1k_tokens: float = 0.0
    total_tokens_used: int = 0
    estimated_monthly_cost: float = 0.0


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation for LLM usage."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    estimated_savings_monthly: float = 0.0
    effort: str = "low"
    current_cost: float = 0.0
    optimized_cost: float = 0.0


@dataclass
class DivergenceDetail:
    """Details about a divergence between provider results."""

    id: UUID = field(default_factory=uuid4)
    obligation_text: str = ""
    providers_agree: list[str] = field(default_factory=list)
    providers_disagree: list[str] = field(default_factory=list)
    agreement_ratio: float = 0.0
    divergence_type: str = "interpretation"  # interpretation, severity, classification, omission
    recommended_action: str = "human_review"
    auto_escalated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "obligation_text": self.obligation_text,
            "providers_agree": self.providers_agree,
            "providers_disagree": self.providers_disagree,
            "agreement_ratio": self.agreement_ratio,
            "divergence_type": self.divergence_type,
            "recommended_action": self.recommended_action,
            "auto_escalated": self.auto_escalated,
        }


@dataclass
class DivergenceReport:
    """Report of all divergences in a consensus result."""

    consensus_id: str = ""
    total_obligations: int = 0
    agreed_count: int = 0
    diverged_count: int = 0
    divergence_rate: float = 0.0
    divergences: list[DivergenceDetail] = field(default_factory=list)
    needs_human_review: bool = False
    severity: str = "low"  # low, medium, high, critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "consensus_id": self.consensus_id,
            "total_obligations": self.total_obligations,
            "agreed_count": self.agreed_count,
            "diverged_count": self.diverged_count,
            "divergence_rate": self.divergence_rate,
            "divergences": [d.to_dict() for d in self.divergences],
            "needs_human_review": self.needs_human_review,
            "severity": self.severity,
        }


class EscalationStatus(str, Enum):
    """Status of a human escalation ticket."""

    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class EscalationPriority(str, Enum):
    """Priority level for escalation tickets."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EscalationTicket:
    """Human review escalation for low-confidence LLM interpretations."""

    id: UUID = field(default_factory=uuid4)
    consensus_id: UUID = field(default_factory=uuid4)
    regulation_text: str = ""
    provider_interpretations: list[dict[str, Any]] = field(default_factory=list)
    agreement_score: float = 0.0
    confidence_score: float = 0.0
    divergence_summary: str = ""
    priority: EscalationPriority = EscalationPriority.MEDIUM
    status: EscalationStatus = EscalationStatus.PENDING_REVIEW
    assigned_to: str | None = None
    resolution: str | None = None
    resolved_obligations: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None


@dataclass
class FailoverEvent:
    """Record of a provider failover event."""

    id: UUID = field(default_factory=uuid4)
    failed_provider: str = ""
    failover_provider: str = ""
    reason: str = ""
    request_id: UUID = field(default_factory=uuid4)
    latency_ms: float = 0.0
    occurred_at: datetime = field(default_factory=datetime.utcnow)
