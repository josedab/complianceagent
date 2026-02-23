"""Open Compliance Data Network models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4


class NetworkMembership(str, Enum):
    """Membership tiers in the compliance network."""

    FREE = "free"
    CONTRIBUTOR = "contributor"
    PREMIUM = "premium"


class BenchmarkCategory(str, Enum):
    """Categories for benchmarking."""

    POSTURE_SCORE = "posture_score"
    TIME_TO_REMEDIATE = "time_to_remediate"
    AUDIT_READINESS = "audit_readiness"
    VIOLATION_DENSITY = "violation_density"
    FRAMEWORK_COVERAGE = "framework_coverage"


@dataclass
class IndustryBenchmark:
    """Benchmark data for a specific category and industry."""

    category: BenchmarkCategory = BenchmarkCategory.POSTURE_SCORE
    industry: str = ""
    percentile_25: float = 0.0
    median: float = 0.0
    percentile_75: float = 0.0
    your_value: float = 0.0
    your_percentile: float = 0.0


@dataclass
class ThreatAlert:
    """A compliance threat alert from the network."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    affected_frameworks: list[str] = field(default_factory=list)
    severity: str = "medium"
    reported_by_count: int = 0
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 0.0


@dataclass
class NetworkStats:
    """Overall network statistics."""

    total_members: int = 0
    active_contributors: int = 0
    patterns_shared: int = 0
    threats_detected: int = 0
    industries_represented: int = 0
