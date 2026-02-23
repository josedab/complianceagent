"""Cross-Organization Compliance Benchmarking models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class Industry(str, Enum):
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    INSURTECH = "insurtech"
    EDTECH = "edtech"
    AI_ML = "ai_ml"
    GOVERNMENT = "government"


class OrgSize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class PrivacyLevel(str, Enum):
    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


@dataclass
class AnonymizedProfile:
    id: UUID = field(default_factory=uuid4)
    industry: Industry = Industry.SAAS
    org_size: OrgSize = OrgSize.MEDIUM
    frameworks: list[str] = field(default_factory=list)
    overall_score: float = 0.0
    framework_scores: dict[str, float] = field(default_factory=dict)
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    contributed_at: datetime | None = None


@dataclass
class BenchmarkResult:
    id: UUID = field(default_factory=uuid4)
    industry: Industry = Industry.SAAS
    org_size: OrgSize = OrgSize.MEDIUM
    your_score: float = 0.0
    percentile: float = 0.0
    industry_avg: float = 0.0
    industry_median: float = 0.0
    top_quartile: float = 0.0
    peer_count: int = 0
    framework_comparisons: list[dict[str, Any]] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class BenchmarkTrend:
    period: str = "30d"
    data_points: list[dict[str, Any]] = field(default_factory=list)
    your_trend: str = "improving"
    industry_trend: str = "stable"


@dataclass
class BenchmarkStats:
    total_participants: int = 0
    by_industry: dict[str, int] = field(default_factory=dict)
    by_size: dict[str, int] = field(default_factory=dict)
    global_avg_score: float = 0.0
    data_freshness_hours: float = 0.0
