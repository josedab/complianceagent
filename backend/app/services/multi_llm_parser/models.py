"""Multi-LLM Compliance Parsing models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class LLMProvider(str, Enum):
    COPILOT = "copilot"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class ConsensusStrategy(str, Enum):
    MAJORITY_VOTE = "majority_vote"
    HIGHEST_CONFIDENCE = "highest_confidence"
    WEIGHTED_AVERAGE = "weighted_average"
    UNANIMOUS = "unanimous"


class ParseStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    DIVERGENT = "divergent"
    FAILED = "failed"


@dataclass
class ProviderConfig:
    provider: LLMProvider = LLMProvider.COPILOT
    model: str = ""
    enabled: bool = True
    weight: float = 1.0
    timeout_seconds: int = 30
    max_tokens: int = 4096


@dataclass
class ProviderResult:
    provider: LLMProvider = LLMProvider.COPILOT
    model: str = ""
    requirements: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: float = 0.0
    error: str = ""


@dataclass
class ConsensusResult:
    id: UUID = field(default_factory=uuid4)
    text_input: str = ""
    strategy: ConsensusStrategy = ConsensusStrategy.MAJORITY_VOTE
    status: ParseStatus = ParseStatus.SUCCESS
    consensus_requirements: list[dict[str, Any]] = field(default_factory=list)
    provider_results: list[ProviderResult] = field(default_factory=list)
    agreement_rate: float = 0.0
    divergences: list[dict[str, Any]] = field(default_factory=list)
    final_confidence: float = 0.0
    total_latency_ms: float = 0.0
    parsed_at: datetime | None = None


@dataclass
class ParserStats:
    total_parses: int = 0
    by_provider: dict[str, int] = field(default_factory=dict)
    by_strategy: dict[str, int] = field(default_factory=dict)
    avg_agreement_rate: float = 0.0
    avg_confidence: float = 0.0
    divergence_count: int = 0
