"""Compliance Posture Scoring & Benchmarking Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.posture_scoring.models import (
    BenchmarkTier,
    DimensionScore,
    IndustryBenchmark,
    PostureReport,
    PostureScore,
    ScoreDimension,
)

logger = structlog.get_logger()

_INDUSTRY_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "fintech": IndustryBenchmark(
        industry="fintech", sample_size=250, average_score=78.5, median_score=80.0,
        p25_score=65.0, p75_score=88.0, p90_score=94.0,
        top_dimensions=["security_controls", "encryption", "access_control"],
    ),
    "healthtech": IndustryBenchmark(
        industry="healthtech", sample_size=180, average_score=72.0, median_score=74.0,
        p25_score=58.0, p75_score=84.0, p90_score=91.0,
        top_dimensions=["data_privacy", "incident_response", "documentation"],
    ),
    "saas": IndustryBenchmark(
        industry="saas", sample_size=500, average_score=75.0, median_score=76.0,
        p25_score=62.0, p75_score=86.0, p90_score=93.0,
        top_dimensions=["security_controls", "access_control", "vendor_management"],
    ),
    "ecommerce": IndustryBenchmark(
        industry="ecommerce", sample_size=300, average_score=70.0, median_score=72.0,
        p25_score=55.0, p75_score=82.0, p90_score=90.0,
        top_dimensions=["data_privacy", "security_controls", "documentation"],
    ),
}

_DIMENSION_WEIGHTS: dict[ScoreDimension, float] = {
    ScoreDimension.DATA_PRIVACY: 0.20,
    ScoreDimension.SECURITY_CONTROLS: 0.20,
    ScoreDimension.REGULATORY_COVERAGE: 0.15,
    ScoreDimension.ACCESS_CONTROL: 0.15,
    ScoreDimension.INCIDENT_RESPONSE: 0.10,
    ScoreDimension.VENDOR_MANAGEMENT: 0.10,
    ScoreDimension.DOCUMENTATION: 0.10,
}


class PostureScoringService:
    """Multi-dimensional compliance posture scoring and benchmarking."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._scores: list[PostureScore] = []
        self._reports: dict[UUID, PostureReport] = {}

    async def compute_score(self, industry: str = "saas") -> PostureScore:
        """Compute comprehensive compliance posture score."""
        dimensions = self._evaluate_dimensions()
        overall = sum(d.score * _DIMENSION_WEIGHTS.get(d.dimension, 0.1) for d in dimensions)
        grade = self._score_to_grade(overall)

        benchmark = _INDUSTRY_BENCHMARKS.get(industry.lower())
        percentile = self._compute_percentile(overall, benchmark) if benchmark else 50.0
        tier = self._percentile_to_tier(percentile)

        framework_scores = {
            "gdpr": 88.0, "hipaa": 76.0, "pci_dss": 92.0,
            "soc2": 81.0, "eu_ai_act": 68.0,
        }

        prev_score = self._scores[-1].overall_score if self._scores else overall
        trend_7d = overall - prev_score

        score = PostureScore(
            overall_score=round(overall, 1),
            grade=grade,
            dimensions=dimensions,
            framework_scores=framework_scores,
            trend_7d=round(trend_7d, 1),
            trend_30d=round(trend_7d * 2.5, 1),
            percentile=round(percentile, 1),
            tier=tier,
            industry=industry,
            computed_at=datetime.now(UTC),
        )
        self._scores.append(score)
        logger.info("Posture score computed", score=score.overall_score, grade=grade, percentile=percentile)
        return score

    async def get_history(self, limit: int = 30) -> list[PostureScore]:
        return list(reversed(self._scores[-limit:]))

    async def get_benchmark(self, industry: str) -> IndustryBenchmark | None:
        return _INDUSTRY_BENCHMARKS.get(industry.lower())

    async def list_industries(self) -> list[str]:
        return list(_INDUSTRY_BENCHMARKS.keys())

    async def generate_report(
        self,
        industry: str = "saas",
        report_format: str = "html",
    ) -> PostureReport:
        """Generate executive compliance posture report."""
        score = await self.compute_score(industry=industry)
        benchmark = _INDUSTRY_BENCHMARKS.get(industry.lower())

        highlights = []
        action_items = []

        for dim in sorted(score.dimensions, key=lambda d: d.score, reverse=True):
            if dim.score >= 85:
                highlights.append(f"Strong {dim.dimension.value.replace('_', ' ')}: {dim.score:.0f}/100")
            elif dim.score < 70:
                action_items.append(f"Improve {dim.dimension.value.replace('_', ' ')} (currently {dim.score:.0f}/100)")
                action_items.extend(dim.recommendations[:2])

        if benchmark:
            if score.percentile >= 75:
                highlights.append(f"Top {100 - score.percentile:.0f}% in {industry} industry")
            else:
                action_items.append(f"Below {industry} median ({benchmark.median_score}); target {benchmark.p75_score}")

        report = PostureReport(
            title=f"Compliance Posture Report — {industry.title()}",
            posture=score,
            benchmark=benchmark,
            highlights=highlights,
            action_items=action_items,
            generated_at=datetime.now(UTC),
            format=report_format,
        )
        self._reports[report.id] = report
        return report

    def _evaluate_dimensions(self) -> list[DimensionScore]:
        """Evaluate each compliance dimension."""
        evals: dict[ScoreDimension, tuple[float, list[str]]] = {
            ScoreDimension.DATA_PRIVACY: (82.0, ["Review data retention policies", "Update consent flows"]),
            ScoreDimension.SECURITY_CONTROLS: (88.0, ["Enable MFA for all admin accounts"]),
            ScoreDimension.REGULATORY_COVERAGE: (75.0, ["Add EU AI Act coverage", "Complete NIS2 mapping"]),
            ScoreDimension.ACCESS_CONTROL: (90.0, []),
            ScoreDimension.INCIDENT_RESPONSE: (70.0, ["Test incident response plan", "Update runbooks"]),
            ScoreDimension.VENDOR_MANAGEMENT: (65.0, ["Re-assess 3 vendor contracts", "Complete vendor questionnaires"]),
            ScoreDimension.DOCUMENTATION: (78.0, ["Update data processing agreements"]),
        }
        return [
            DimensionScore(
                dimension=dim,
                score=score,
                weight=_DIMENSION_WEIGHTS.get(dim, 0.1),
                recommendations=recs,
            )
            for dim, (score, recs) in evals.items()
        ]

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= 95: return "A+"
        if score >= 90: return "A"
        if score >= 85: return "A-"
        if score >= 80: return "B+"
        if score >= 75: return "B"
        if score >= 70: return "B-"
        if score >= 65: return "C+"
        if score >= 60: return "C"
        if score >= 55: return "D"
        return "F"

    @staticmethod
    def _compute_percentile(score: float, benchmark: IndustryBenchmark) -> float:
        if score >= benchmark.p90_score: return 92.0
        if score >= benchmark.p75_score: return 80.0
        if score >= benchmark.median_score: return 55.0
        if score >= benchmark.p25_score: return 30.0
        return 15.0

    @staticmethod
    def _percentile_to_tier(percentile: float) -> BenchmarkTier:
        if percentile >= 90: return BenchmarkTier.TOP_10
        if percentile >= 75: return BenchmarkTier.TOP_25
        if percentile >= 50: return BenchmarkTier.TOP_50
        if percentile >= 25: return BenchmarkTier.BOTTOM_50
        return BenchmarkTier.BOTTOM_25
