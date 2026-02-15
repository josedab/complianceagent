"""Compliance Posture Scoring & Benchmarking models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
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


@dataclass
class DimensionDetail:
    """Detailed breakdown of a single scoring dimension."""
    dimension: str = ""
    score: float = 0.0
    max_score: float = 100.0
    grade: str = "C"
    findings_count: int = 0
    critical_findings: int = 0
    drivers: list[dict[str, Any]] = field(default_factory=list)
    trend: str = "stable"  # improving, degrading, stable

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "max_score": self.max_score,
            "grade": self.grade,
            "findings_count": self.findings_count,
            "critical_findings": self.critical_findings,
            "drivers": self.drivers,
            "trend": self.trend,
        }


@dataclass
class DynamicPostureScore:
    """Complete compliance posture score with all dimensions."""
    overall_score: float = 0.0
    overall_grade: str = "C"
    dimensions: list[DimensionDetail] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    repo: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "overall_grade": self.overall_grade,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "calculated_at": self.calculated_at.isoformat(),
            "repo": self.repo,
            "recommendations": self.recommendations,
        }


@dataclass
class DynamicIndustryBenchmark:
    """Benchmark comparison against industry peers."""
    industry: str = ""
    your_score: float = 0.0
    industry_avg: float = 0.0
    industry_median: float = 0.0
    industry_p75: float = 0.0
    industry_p90: float = 0.0
    percentile: float = 0.0
    peer_count: int = 0
    dimension_comparison: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "industry": self.industry,
            "your_score": self.your_score,
            "industry_avg": self.industry_avg,
            "industry_median": self.industry_median,
            "industry_p75": self.industry_p75,
            "industry_p90": self.industry_p90,
            "percentile": self.percentile,
            "peer_count": self.peer_count,
            "dimension_comparison": self.dimension_comparison,
        }


@dataclass
class ScoreHistory:
    """Historical posture scores for trend tracking."""
    repo: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)
    trend: str = "stable"
    improvement_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "history": self.history,
            "trend": self.trend,
            "improvement_rate": self.improvement_rate,
        }
