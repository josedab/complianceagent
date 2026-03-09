"""Cross-Organization Compliance Benchmarking Service."""

import hashlib
import math
import random
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cross_org_benchmark.models import (
    AnonymizedProfile,
    BenchmarkResult,
    BenchmarkStats,
    BenchmarkSubmission,
    BenchmarkTrend,
    DifferentialPrivacyConfig,
    ImprovementPriority,
    Industry,
    InsightsDashboard,
    OrgSize,
    PeerGroup,
    PeerRecommendation,
    PercentileRanking,
    PrivacyLevel,
)


logger = structlog.get_logger()

MIN_ORG_THRESHOLD = 50

# Seed anonymized benchmark data (simulating differential privacy aggregates)
_INDUSTRY_BENCHMARKS: dict[str, dict] = {
    "fintech": {
        "avg": 82.5,
        "median": 84.0,
        "top_q": 92.0,
        "bot_q": 73.0,
        "std": 8.5,
        "count": 340,
    },
    "healthtech": {
        "avg": 78.0,
        "median": 79.5,
        "top_q": 89.0,
        "bot_q": 68.0,
        "std": 9.0,
        "count": 210,
    },
    "saas": {"avg": 76.0, "median": 77.0, "top_q": 88.0, "bot_q": 65.0, "std": 9.5, "count": 520},
    "ecommerce": {
        "avg": 74.5,
        "median": 75.0,
        "top_q": 86.0,
        "bot_q": 63.0,
        "std": 10.0,
        "count": 180,
    },
    "insurtech": {
        "avg": 80.0,
        "median": 81.0,
        "top_q": 90.0,
        "bot_q": 70.0,
        "std": 8.0,
        "count": 95,
    },
    "edtech": {"avg": 71.0, "median": 72.0, "top_q": 84.0, "bot_q": 60.0, "std": 10.5, "count": 75},
    "ai_ml": {"avg": 68.5, "median": 69.0, "top_q": 82.0, "bot_q": 57.0, "std": 11.0, "count": 150},
    "government": {
        "avg": 85.0,
        "median": 86.0,
        "top_q": 94.0,
        "bot_q": 76.0,
        "std": 7.5,
        "count": 60,
    },
}

# Seed data for size-based benchmarks
_SIZE_BENCHMARKS: dict[str, dict] = {
    "startup": {
        "avg": 65.0,
        "median": 66.0,
        "top_q": 78.0,
        "bot_q": 54.0,
        "std": 12.0,
        "count": 280,
    },
    "small": {"avg": 71.0, "median": 72.0, "top_q": 83.0, "bot_q": 60.0, "std": 10.0, "count": 350},
    "medium": {"avg": 77.0, "median": 78.0, "top_q": 88.0, "bot_q": 67.0, "std": 9.0, "count": 420},
    "large": {"avg": 82.0, "median": 83.0, "top_q": 91.0, "bot_q": 73.0, "std": 8.0, "count": 310},
    "enterprise": {
        "avg": 86.0,
        "median": 87.0,
        "top_q": 95.0,
        "bot_q": 78.0,
        "std": 7.0,
        "count": 270,
    },
}

# Seed data for framework-specific benchmarks
_FRAMEWORK_BENCHMARKS: dict[str, dict] = {
    "GDPR": {"avg": 79.0, "median": 80.0, "top_q": 90.0, "std": 9.0, "count": 680},
    "HIPAA": {"avg": 76.0, "median": 77.0, "top_q": 88.0, "std": 9.5, "count": 310},
    "PCI-DSS": {"avg": 81.0, "median": 82.0, "top_q": 92.0, "std": 8.5, "count": 420},
    "SOC2": {"avg": 78.0, "median": 79.0, "top_q": 89.0, "std": 9.0, "count": 550},
    "ISO27001": {"avg": 80.0, "median": 81.0, "top_q": 91.0, "std": 8.0, "count": 390},
    "NIST": {"avg": 74.0, "median": 75.0, "top_q": 86.0, "std": 10.0, "count": 260},
}

# Control area benchmarks for peer recommendations
_CONTROL_AREA_BENCHMARKS: dict[str, dict] = {
    "access_control": {"avg": 78.0, "adoption": 0.92},
    "encryption": {"avg": 81.0, "adoption": 0.88},
    "incident_response": {"avg": 72.0, "adoption": 0.79},
    "data_retention": {"avg": 69.0, "adoption": 0.74},
    "vendor_management": {"avg": 67.0, "adoption": 0.71},
    "security_training": {"avg": 74.0, "adoption": 0.83},
    "audit_logging": {"avg": 76.0, "adoption": 0.86},
    "change_management": {"avg": 73.0, "adoption": 0.80},
}


def _apply_laplace_noise(
    value: float,
    epsilon: float = 1.0,
    sensitivity: float = 1.0,
    seed: int | None = None,
) -> float:
    """Apply calibrated Laplace noise for differential privacy.

    Uses the Laplace mechanism: noise ~ Lap(sensitivity / epsilon).
    When seed is provided, noise is deterministic for reproducibility.
    """
    scale = sensitivity / epsilon
    if seed is not None:
        rng = random.Random(seed)
    else:
        hash_val = int(hashlib.sha256(str(value).encode()).hexdigest()[:8], 16)
        rng = random.Random(hash_val)

    # Sample from Laplace distribution via inverse CDF
    u = rng.random() - 0.5
    noise = -scale * _sign(u) * math.log(1 - 2 * abs(u))
    return round(value + noise, 1)


def _sign(x: float) -> float:
    return 1.0 if x >= 0 else -1.0


def _compute_percentile(score: float, avg: float, std_dev: float) -> float:
    """Compute percentile using normal distribution approximation."""
    if std_dev <= 0:
        return 50.0
    z_score = (score - avg) / std_dev
    percentile = 50 * (1 + math.erf(z_score / math.sqrt(2)))
    return round(min(99.0, max(1.0, percentile)), 1)


def _meets_threshold(count: int) -> bool:
    """Check if sample size meets minimum threshold for meaningful benchmarks."""
    return count >= MIN_ORG_THRESHOLD


class CrossOrgBenchmarkService:
    """Anonymous cross-organization compliance benchmarking."""

    def __init__(
        self,
        db: AsyncSession,
        privacy_config: DifferentialPrivacyConfig | None = None,
    ):
        self.db = db
        self._profiles: list[AnonymizedProfile] = []
        self._submissions: list[BenchmarkSubmission] = []
        self._privacy_config = privacy_config or DifferentialPrivacyConfig()
        self._epsilon = self._privacy_config.epsilon

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
            framework_scores={
                k: _apply_laplace_noise(v, self._epsilon)
                for k, v in (framework_scores or {}).items()
            },
            frameworks=list((framework_scores or {}).keys()),
            privacy_level=PrivacyLevel(privacy_level),
            contributed_at=datetime.now(UTC),
        )
        self._profiles.append(profile)
        logger.info("Benchmark data contributed", industry=industry)
        return profile

    async def submit_benchmark(
        self,
        industry: str,
        org_size: str,
        overall_score: float,
        framework_scores: dict[str, float] | None = None,
        control_area_scores: dict[str, float] | None = None,
        privacy_config: DifferentialPrivacyConfig | None = None,
    ) -> BenchmarkSubmission:
        """Submit anonymized benchmark data with differential privacy."""
        config = privacy_config or self._privacy_config
        noised = _apply_laplace_noise(overall_score, config.epsilon, config.sensitivity)
        noised_fw = {
            k: _apply_laplace_noise(v, config.epsilon, config.sensitivity)
            for k, v in (framework_scores or {}).items()
        }
        noised_ca = {
            k: _apply_laplace_noise(v, config.epsilon, config.sensitivity)
            for k, v in (control_area_scores or {}).items()
        }

        submission = BenchmarkSubmission(
            industry=Industry(industry),
            org_size=OrgSize(org_size),
            frameworks=list((framework_scores or {}).keys()),
            overall_score=overall_score,
            framework_scores=noised_fw,
            control_area_scores=noised_ca,
            privacy_config=config,
            noised_score=noised,
            submitted_at=datetime.now(UTC),
        )
        self._submissions.append(submission)
        logger.info("Benchmark submission received", industry=industry, org_size=org_size)
        return submission

    async def get_benchmark(
        self,
        your_score: float,
        industry: str,
        org_size: str = "medium",
    ) -> BenchmarkResult:
        ind = Industry(industry)
        bench = _INDUSTRY_BENCHMARKS.get(
            industry, {"avg": 75.0, "median": 76.0, "top_q": 88.0, "count": 50}
        )

        # Calculate percentile
        avg = bench["avg"]
        std_dev = bench.get("std", (bench["top_q"] - avg) / 1.5)
        z_score = (your_score - avg) / std_dev if std_dev > 0 else 0
        percentile = min(99, max(1, round(50 * (1 + math.erf(z_score / math.sqrt(2))), 1)))

        suggestions = []
        if your_score < avg:
            suggestions.append(
                f"Your score ({your_score}) is below the {industry} average ({avg}). Focus on closing critical gaps."
            )
        if your_score < bench["median"]:
            suggestions.append("Prioritize the top 3 findings to reach the industry median.")
        if your_score >= bench["top_q"]:
            suggestions.append(
                "Excellent! You're in the top quartile. Consider contributing best practices."
            )

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

    async def compute_percentile_rankings(
        self,
        your_score: float,
        industry: str,
        org_size: str,
        framework_scores: dict[str, float] | None = None,
    ) -> PercentileRanking:
        """Compute percentile rankings across industry, size, and framework dimensions."""
        ind_bench = _INDUSTRY_BENCHMARKS.get(industry, {"avg": 75.0, "std": 10.0, "count": 50})
        size_bench = _SIZE_BENCHMARKS.get(org_size, {"avg": 77.0, "std": 9.0, "count": 300})

        # Global percentile across all participants
        global_avg = sum(v["avg"] * v["count"] for v in _INDUSTRY_BENCHMARKS.values()) / max(
            1, sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values())
        )
        global_std = 10.0
        overall_pct = _compute_percentile(your_score, global_avg, global_std)

        industry_pct = _compute_percentile(your_score, ind_bench["avg"], ind_bench.get("std", 10.0))
        size_pct = _compute_percentile(your_score, size_bench["avg"], size_bench.get("std", 9.0))

        # Framework percentiles
        fw_pcts: dict[str, float] = {}
        for fw, score in (framework_scores or {}).items():
            fw_bench = _FRAMEWORK_BENCHMARKS.get(fw, {"avg": 75.0, "std": 10.0})
            fw_pcts[fw] = _compute_percentile(score, fw_bench["avg"], fw_bench.get("std", 10.0))

        # Peer group (intersection of industry + size)
        peer_count = min(ind_bench.get("count", 0), size_bench.get("count", 0)) // 3
        peer_avg = (ind_bench["avg"] + size_bench["avg"]) / 2
        peer_std = (ind_bench.get("std", 10.0) + size_bench.get("std", 9.0)) / 2
        peer_pct = _compute_percentile(your_score, peer_avg, peer_std)

        sample_sizes = {
            "overall": sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values()),
            "industry": ind_bench.get("count", 0),
            "size": size_bench.get("count", 0),
            "peer_group": peer_count,
        }
        for fw in framework_scores or {}:
            fb = _FRAMEWORK_BENCHMARKS.get(fw, {"count": 0})
            sample_sizes[f"framework_{fw}"] = fb.get("count", 0)

        significant = all(
            _meets_threshold(sample_sizes.get(k, 0)) for k in ["industry", "size", "peer_group"]
        )

        return PercentileRanking(
            overall_percentile=overall_pct,
            industry_percentile=industry_pct,
            size_percentile=size_pct,
            framework_percentiles=fw_pcts,
            peer_group_percentile=peer_pct,
            sample_sizes=sample_sizes,
            is_statistically_significant=significant,
        )

    async def get_peer_group(
        self,
        industry: str,
        org_size: str,
        frameworks: list[str] | None = None,
    ) -> PeerGroup:
        """Find peer group ('companies like you') based on industry, size, and frameworks."""
        ind_bench = _INDUSTRY_BENCHMARKS.get(
            industry,
            {"avg": 75.0, "median": 76.0, "top_q": 88.0, "bot_q": 64.0, "std": 10.0, "count": 50},
        )
        size_bench = _SIZE_BENCHMARKS.get(
            org_size,
            {"avg": 77.0, "median": 78.0, "top_q": 88.0, "bot_q": 67.0, "std": 9.0, "count": 300},
        )

        # Peer group is the intersection — estimate count and blend stats
        peer_count = min(ind_bench.get("count", 0), size_bench.get("count", 0)) // 3
        # Adjust peer count upward if shared frameworks increase overlap
        if frameworks:
            matching_fw = sum(1 for f in frameworks if f in _FRAMEWORK_BENCHMARKS)
            peer_count = max(peer_count, peer_count + matching_fw * 5)

        avg = round((ind_bench["avg"] + size_bench["avg"]) / 2, 1)
        median = round((ind_bench["median"] + size_bench["median"]) / 2, 1)
        top_q = round((ind_bench["top_q"] + size_bench["top_q"]) / 2, 1)
        bot_q = round((ind_bench.get("bot_q", 64.0) + size_bench.get("bot_q", 67.0)) / 2, 1)
        std = round((ind_bench.get("std", 10.0) + size_bench.get("std", 9.0)) / 2, 1)

        return PeerGroup(
            industry=Industry(industry),
            org_size=OrgSize(org_size),
            frameworks=frameworks or [],
            peer_count=peer_count,
            avg_score=avg,
            median_score=median,
            top_quartile_score=top_q,
            bottom_quartile_score=bot_q,
            score_std_dev=std,
            meets_minimum_threshold=_meets_threshold(peer_count),
        )

    async def get_peer_recommendations(
        self,
        your_score: float,
        industry: str,
        org_size: str,
        control_area_scores: dict[str, float] | None = None,
    ) -> list[PeerRecommendation]:
        """Generate anonymized recommendations from peer group analysis."""
        recommendations: list[PeerRecommendation] = []

        for area, bench in _CONTROL_AREA_BENCHMARKS.items():
            your_area_score = (control_area_scores or {}).get(area, your_score * 0.95)
            peer_avg = bench["avg"]
            gap = round(peer_avg - your_area_score, 1)

            if gap <= 0:
                continue

            if gap > 15:
                priority = ImprovementPriority.CRITICAL
            elif gap > 10:
                priority = ImprovementPriority.HIGH
            elif gap > 5:
                priority = ImprovementPriority.MEDIUM
            else:
                priority = ImprovementPriority.LOW

            area_label = area.replace("_", " ").title()
            recommendations.append(
                PeerRecommendation(
                    area=area,
                    priority=priority,
                    your_score=round(your_area_score, 1),
                    peer_avg_score=peer_avg,
                    gap=gap,
                    recommendation=f"Improve {area_label}: your score ({your_area_score:.0f}) is {gap:.0f} points below peer average ({peer_avg:.0f}). "
                    f"{bench['adoption'] * 100:.0f}% of similar organizations have implemented stronger controls here.",
                    peer_adoption_rate=bench["adoption"],
                )
            )

        # Sort by gap descending (biggest improvement opportunities first)
        recommendations.sort(key=lambda r: r.gap, reverse=True)
        return recommendations

    async def get_insights_dashboard(
        self,
        your_score: float,
        industry: str,
        org_size: str,
        framework_scores: dict[str, float] | None = None,
        control_area_scores: dict[str, float] | None = None,
    ) -> InsightsDashboard:
        """Generate a full insights dashboard with rankings, peer group, and recommendations."""
        rankings = await self.compute_percentile_rankings(
            your_score,
            industry,
            org_size,
            framework_scores,
        )
        peer_group = await self.get_peer_group(
            industry, org_size, list((framework_scores or {}).keys())
        )
        recommendations = await self.get_peer_recommendations(
            your_score,
            industry,
            org_size,
            control_area_scores,
        )

        # Classify strengths and weaknesses
        strengths: list[str] = []
        weaknesses: list[str] = []

        if rankings.industry_percentile >= 75:
            strengths.append(
                f"Top quartile in {industry} industry (P{rankings.industry_percentile:.0f})"
            )
        elif rankings.industry_percentile < 25:
            weaknesses.append(
                f"Bottom quartile in {industry} industry (P{rankings.industry_percentile:.0f})"
            )

        if rankings.size_percentile >= 75:
            strengths.append(f"Top quartile among {org_size}-sized organizations")
        elif rankings.size_percentile < 25:
            weaknesses.append(f"Below average among {org_size}-sized organizations")

        for fw, pct in rankings.framework_percentiles.items():
            if pct >= 80:
                strengths.append(f"Strong {fw} compliance (P{pct:.0f})")
            elif pct < 30:
                weaknesses.append(f"{fw} compliance needs improvement (P{pct:.0f})")

        # Improvement priorities (top recommendations filtered to actionable)
        improvement_priorities = [
            r
            for r in recommendations
            if r.priority in (ImprovementPriority.CRITICAL, ImprovementPriority.HIGH)
        ]
        if not improvement_priorities:
            improvement_priorities = recommendations[:3]

        # Summary
        data_warning = None
        if not peer_group.meets_minimum_threshold:
            data_warning = (
                f"Peer group has only {peer_group.peer_count} organizations "
                f"(minimum {MIN_ORG_THRESHOLD} required for statistically meaningful benchmarks). "
                "Results should be interpreted with caution."
            )

        summary = (
            f"Your compliance score of {your_score} places you at the "
            f"{rankings.overall_percentile:.0f}th percentile overall and "
            f"{rankings.industry_percentile:.0f}th percentile in {industry}."
        )
        if improvement_priorities:
            top_area = improvement_priorities[0].area.replace("_", " ").title()
            summary += f" Top priority: improve {top_area}."

        return InsightsDashboard(
            org_score=your_score,
            rankings=rankings,
            peer_group=peer_group,
            improvement_priorities=improvement_priorities,
            strengths=strengths,
            weaknesses=weaknesses,
            peer_recommendations=recommendations,
            benchmark_summary=summary,
            data_quality_warning=data_warning,
            generated_at=datetime.now(UTC),
        )

    def get_trend(self, industry: str, period: str = "30d") -> BenchmarkTrend:
        bench = _INDUSTRY_BENCHMARKS.get(industry, {"avg": 75.0})
        avg = bench["avg"]
        data_points = [
            {
                "date": f"2026-02-{15 + i}",
                "industry_avg": round(avg + i * 0.2, 1),
                "your_score": round(85.0 + i * 0.3, 1),
            }
            for i in range(7)
        ]
        return BenchmarkTrend(
            period=period, data_points=data_points, your_trend="improving", industry_trend="stable"
        )

    def list_industries(self) -> list[dict]:
        return [
            {"industry": k, "avg_score": v["avg"], "participants": v["count"]}
            for k, v in _INDUSTRY_BENCHMARKS.items()
        ]

    def get_stats(self) -> BenchmarkStats:
        by_ind: dict[str, int] = {}
        by_size: dict[str, int] = {}
        for p in self._profiles:
            by_ind[p.industry.value] = by_ind.get(p.industry.value, 0) + 1
            by_size[p.org_size.value] = by_size.get(p.org_size.value, 0) + 1
        total_participants = sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values()) + len(
            self._profiles
        )
        global_avg = sum(v["avg"] * v["count"] for v in _INDUSTRY_BENCHMARKS.values()) / max(
            1, sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values())
        )
        return BenchmarkStats(
            total_participants=total_participants,
            by_industry=by_ind,
            by_size=by_size,
            global_avg_score=round(global_avg, 1),
            data_freshness_hours=2.0,
        )

    def check_minimum_threshold(
        self, industry: str | None = None, org_size: str | None = None
    ) -> dict:
        """Check if there are enough organizations for meaningful benchmarks."""
        results: dict[str, Any] = {"minimum_required": MIN_ORG_THRESHOLD}

        if industry:
            ind_bench = _INDUSTRY_BENCHMARKS.get(industry, {"count": 0})
            count = ind_bench.get("count", 0)
            results["industry"] = {
                "name": industry,
                "count": count,
                "meets_threshold": _meets_threshold(count),
            }

        if org_size:
            size_bench = _SIZE_BENCHMARKS.get(org_size, {"count": 0})
            count = size_bench.get("count", 0)
            results["org_size"] = {
                "name": org_size,
                "count": count,
                "meets_threshold": _meets_threshold(count),
            }

        total = sum(v["count"] for v in _INDUSTRY_BENCHMARKS.values()) + len(self._profiles)
        results["total"] = {"count": total, "meets_threshold": _meets_threshold(total)}

        return results
