"""Multi-LLM Regulatory Parsing Engine models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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
