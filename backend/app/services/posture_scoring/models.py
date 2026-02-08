"""Compliance Posture Scoring & Benchmarking models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ScoreDimension(str, Enum):
    DATA_PRIVACY = "data_privacy"
    SECURITY_CONTROLS = "security_controls"
    REGULATORY_COVERAGE = "regulatory_coverage"
    ACCESS_CONTROL = "access_control"
    INCIDENT_RESPONSE = "incident_response"
    VENDOR_MANAGEMENT = "vendor_management"
    DOCUMENTATION = "documentation"


class BenchmarkTier(str, Enum):
    TOP_10 = "top_10"
    TOP_25 = "top_25"
    TOP_50 = "top_50"
    BOTTOM_50 = "bottom_50"
    BOTTOM_25 = "bottom_25"


@dataclass
class DimensionScore:
    dimension: ScoreDimension = ScoreDimension.DATA_PRIVACY
    score: float = 0.0
    max_score: float = 100.0
    weight: float = 1.0
    findings: int = 0
    recommendations: list[str] = field(default_factory=list)


@dataclass
class PostureScore:
    """Comprehensive compliance posture score."""
    id: UUID = field(default_factory=uuid4)
    overall_score: float = 0.0
    grade: str = ""  # A+, A, B, C, D, F
    dimensions: list[DimensionScore] = field(default_factory=list)
    framework_scores: dict[str, float] = field(default_factory=dict)
    trend_7d: float = 0.0
    trend_30d: float = 0.0
    percentile: float = 0.0
    tier: BenchmarkTier = BenchmarkTier.TOP_50
    industry: str = ""
    computed_at: datetime | None = None


@dataclass
class IndustryBenchmark:
    """Industry benchmark data."""
    industry: str = ""
    sample_size: int = 0
    average_score: float = 0.0
    median_score: float = 0.0
    p25_score: float = 0.0
    p75_score: float = 0.0
    p90_score: float = 0.0
    top_dimensions: list[str] = field(default_factory=list)
    updated_at: datetime | None = None


@dataclass
class PostureReport:
    """Executive compliance posture report."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    posture: PostureScore = field(default_factory=PostureScore)
    benchmark: IndustryBenchmark | None = None
    highlights: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
    format: str = "html"  # html, pdf, json
