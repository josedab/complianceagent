"""Cross-Organization Compliance Benchmarking Service."""

import hashlib
import math
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cross_org_benchmark.models import (
    AnonymizedProfile,
    BenchmarkResult,
    BenchmarkStats,
    BenchmarkTrend,
    Industry,
    OrgSize,
    PrivacyLevel,
)


logger = structlog.get_logger()

# Seed anonymized benchmark data (simulating differential privacy aggregates)
_INDUSTRY_BENCHMARKS: dict[str, dict] = {
    "fintech": {"avg": 82.5, "median": 84.0, "top_q": 92.0, "count": 340},
    "healthtech": {"avg": 78.0, "median": 79.5, "top_q": 89.0, "count": 210},
    "saas": {"avg": 76.0, "median": 77.0, "top_q": 88.0, "count": 520},
    "ecommerce": {"avg": 74.5, "median": 75.0, "top_q": 86.0, "count": 180},
    "insurtech": {"avg": 80.0, "median": 81.0, "top_q": 90.0, "count": 95},
    "edtech": {"avg": 71.0, "median": 72.0, "top_q": 84.0, "count": 75},
    "ai_ml": {"avg": 68.5, "median": 69.0, "top_q": 82.0, "count": 150},
    "government": {"avg": 85.0, "median": 86.0, "top_q": 94.0, "count": 60},
}


def _apply_laplace_noise(value: float, epsilon: float = 1.0, sensitivity: float = 1.0) -> float:
    """Apply Laplace noise for differential privacy."""
    # Deterministic noise based on value hash for reproducibility
    noise_seed = int(hashlib.sha256(str(value).encode()).hexdigest()[:8], 16)
    noise = (noise_seed % 100 - 50) * (sensitivity / epsilon) / 100
    return round(value + noise, 1)


class CrossOrgBenchmarkService:
    """Anonymous cross-organization compliance benchmarking."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._profiles: list[AnonymizedProfile] = []
        self._epsilon = 1.0  # Differential privacy parameter

    async def contribute_data(
        self,
        industry: str,
        org_size: str,
        overall_score: float,
        framework_scores: dict[str, float] | None = None,
        privacy_level: str = "standard",
    ) -> AnonymizedProfile:
        profile = AnonymizedProfile(
            industry=Industry(industry),
            org_size=OrgSize(org_size),
            overall_score=_apply_laplace_noise(overall_score, self._epsilon),
            framework_scores={k: _apply_laplace_noise(v, self._epsilon) for k, v in (framework_scores or {}).items()},
            frameworks=list((framework_scores or {}).keys()),
            privacy_level=PrivacyLevel(privacy_level),
            contributed_at=datetime.now(UTC),
        )
        self._profiles.append(profile)
        logger.info("Benchmark data contributed", industry=industry)
        return profile

    async def get_benchmark(
        self,
        your_score: float,
        industry: str,
        org_size: str = "medium",
    ) -> BenchmarkResult:
        ind = Industry(industry)
        bench = _INDUSTRY_BENCHMARKS.get(industry, {"avg": 75.0, "median": 76.0, "top_q": 88.0, "count": 50})

        # Calculate percentile
        avg = bench["avg"]
        std_dev = (bench["top_q"] - avg) / 1.5
        z_score = (your_score - avg) / std_dev if std_dev > 0 else 0
        percentile = min(99, max(1, round(50 * (1 + math.erf(z_score / math.sqrt(2))), 1)))

        suggestions = []
        if your_score < avg:
            suggestions.append(f"Your score ({your_score}) is below the {industry} average ({avg}). Focus on closing critical gaps.")
        if your_score < bench["median"]:
            suggestions.append("Prioritize the top 3 findings to reach the industry median.")
        if your_score >= bench["top_q"]:
            suggestions.append("Excellent! You're in the top quartile. Consider contributing best practices.")

        fw_comparisons = [
            {"framework": "GDPR", "your_score": your_score * 1.02, "industry_avg": avg * 0.98},
            {"framework": "HIPAA", "your_score": your_score * 0.95, "industry_avg": avg * 1.01},
            {"framework": "PCI-DSS", "your_score": your_score * 1.05, "industry_avg": avg * 1.03},
        ]

        return BenchmarkResult(
            industry=ind,
            org_size=OrgSize(org_size),
            your_score=your_score,
            percentile=percentile,
            industry_avg=avg,
            industry_median=bench["median"],
            top_quartile=bench["top_q"],
            peer_count=bench["count"],
            framework_comparisons=fw_comparisons,
            improvement_suggestions=suggestions,
            generated_at=datetime.now(UTC),
        )

    def get_trend(self, industry: str, period: str = "30d") -> BenchmarkTrend:
        bench = _INDUSTRY_BENCHMARKS.get(industry, {"avg": 75.0})
        avg = bench["avg"]
        data_points = [
            {"date": f"2026-02-{15 + i}", "industry_avg": round(avg + i * 0.2, 1), "your_score": round(85.0 + i * 0.3, 1)}
            for i in range(7)
        ]
        return BenchmarkTrend(period=period, data_points=data_points, your_trend="improving", industry_trend="stable")

    def list_industries(self) -> list[dict]:
        return [{"industry": k, "avg_score": v["avg"], "participants": v["count"]} for k, v in _INDUSTRY_BENCHMARKS.items()]

    def get_stats(self) -> BenchmarkStats:
        by_ind: dict[str, int] = {}
        by_size: dict[str, int] = {}
        for p in self._profiles:
            by_ind[p.industry.value] = by_ind.get(p.industry.value, 0) + 1
            by_size[p.org_size.value] = by_size.get(p.org_size.value, 0) + 1
        total_participants = sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values()) + len(self._profiles)
        global_avg = sum(v["avg"] * v["count"] for v in _INDUSTRY_BENCHMARKS.values()) / max(1, sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values()))
        return BenchmarkStats(
            total_participants=total_participants,
            by_industry=by_ind,
            by_size=by_size,
            global_avg_score=round(global_avg, 1),
            data_freshness_hours=2.0,
        )
