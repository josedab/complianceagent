"""Federated Compliance Intelligence Network models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ParticipantStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"


class InsightType(str, Enum):
    BEST_PRACTICE = "best_practice"
    COMMON_PATTERN = "common_pattern"
    INDUSTRY_TREND = "industry_trend"
    RISK_SIGNAL = "risk_signal"
    BENCHMARK = "benchmark"


class PrivacyLevel(str, Enum):
    FULL = "full"  # epsilon=0.1
    STANDARD = "standard"  # epsilon=1.0
    RELAXED = "relaxed"  # epsilon=5.0


@dataclass
class FederatedParticipant:
    """An organization participating in the network."""
    id: UUID = field(default_factory=uuid4)
    organization_name: str = ""
    industry: str = ""
    size_category: str = ""  # small, medium, large, enterprise
    status: ParticipantStatus = ParticipantStatus.PENDING
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    contributed_patterns: int = 0
    insights_received: int = 0
    joined_at: datetime | None = None


@dataclass
class AnonymizedPattern:
    """A privacy-preserving compliance pattern."""
    id: UUID = field(default_factory=uuid4)
    framework: str = ""
    control_id: str = ""
    pattern_description: str = ""
    adoption_rate: float = 0.0  # percentage of orgs using this pattern
    effectiveness_score: float = 0.0
    industry: str = ""
    sample_size: int = 0
    noise_applied: bool = True
    epsilon: float = 1.0
    created_at: datetime | None = None


@dataclass
class IndustryInsight:
    """An insight derived from federated data."""
    id: UUID = field(default_factory=uuid4)
    insight_type: InsightType = InsightType.COMMON_PATTERN
    title: str = ""
    description: str = ""
    framework: str = ""
    industry: str = ""
    relevance_score: float = 0.0
    data_points: int = 0
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class NetworkStats:
    """Statistics about the federated network."""
    total_participants: int = 0
    active_participants: int = 0
    total_patterns: int = 0
    total_insights: int = 0
    industries_represented: list[str] = field(default_factory=list)
    frameworks_covered: list[str] = field(default_factory=list)
    avg_privacy_epsilon: float = 1.0
