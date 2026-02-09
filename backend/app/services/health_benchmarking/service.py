"""Compliance Health Score Benchmarking service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.health_benchmarking.models import (
    BenchmarkComparison,
    BoardReport,
    CompanySize,
    ComplianceGrade,
    HealthScore,
    ImprovementSuggestion,
    LeaderboardEntry,
    PeerBenchmark,
    ScoreHistory,
)


logger = structlog.get_logger()

# Realistic benchmark data for industries
_INDUSTRY_BENCHMARKS: dict[str, PeerBenchmark] = {
    "saas": PeerBenchmark(
        peer_group="saas_all", company_size=CompanySize.MEDIUM, industry="saas",
        sample_size=520, avg_score=74.8, median_score=76.0,
        p25=62.0, p50=76.0, p75=86.0, p90=93.0,
        grade_distribution={"A+": 8, "A": 35, "A-": 52, "B+": 78, "B": 105, "B-": 82, "C+": 65, "C": 48, "D": 30, "F": 17},
        top_gaps=["vendor_management", "incident_response", "documentation"],
    ),
    "fintech": PeerBenchmark(
        peer_group="fintech_all", company_size=CompanySize.MEDIUM, industry="fintech",
        sample_size=280, avg_score=79.2, median_score=81.0,
        p25=68.0, p50=81.0, p75=89.0, p90=95.0,
        grade_distribution={"A+": 12, "A": 28, "A-": 40, "B+": 55, "B": 62, "B-": 35, "C+": 22, "C": 14, "D": 8, "F": 4},
        top_gaps=["regulatory_coverage", "documentation", "data_privacy"],
    ),
    "healthtech": PeerBenchmark(
        peer_group="healthtech_all", company_size=CompanySize.MEDIUM, industry="healthtech",
        sample_size=195, avg_score=72.4, median_score=74.0,
        p25=58.0, p50=74.0, p75=84.0, p90=91.0,
        grade_distribution={"A+": 5, "A": 18, "A-": 28, "B+": 38, "B": 42, "B-": 28, "C+": 18, "C": 10, "D": 5, "F": 3},
        top_gaps=["access_control", "vendor_management", "incident_response"],
    ),
    "ecommerce": PeerBenchmark(
        peer_group="ecommerce_all", company_size=CompanySize.MEDIUM, industry="ecommerce",
        sample_size=340, avg_score=69.5, median_score=71.0,
        p25=55.0, p50=71.0, p75=82.0, p90=89.0,
        grade_distribution={"A+": 6, "A": 22, "A-": 34, "B+": 48, "B": 72, "B-": 58, "C+": 45, "C": 30, "D": 16, "F": 9},
        top_gaps=["data_privacy", "security_controls", "regulatory_coverage"],
    ),
    "govtech": PeerBenchmark(
        peer_group="govtech_all", company_size=CompanySize.LARGE, industry="govtech",
        sample_size=110, avg_score=76.8, median_score=78.0,
        p25=64.0, p50=78.0, p75=87.0, p90=93.0,
        grade_distribution={"A+": 4, "A": 12, "A-": 18, "B+": 22, "B": 24, "B-": 14, "C+": 8, "C": 5, "D": 2, "F": 1},
        top_gaps=["vendor_management", "documentation", "incident_response"],
    ),
    "edtech": PeerBenchmark(
        peer_group="edtech_all", company_size=CompanySize.SMALL, industry="edtech",
        sample_size=150, avg_score=66.2, median_score=68.0,
        p25=52.0, p50=68.0, p75=79.0, p90=87.0,
        grade_distribution={"A+": 3, "A": 10, "A-": 16, "B+": 24, "B": 32, "B-": 25, "C+": 18, "C": 12, "D": 7, "F": 3},
        top_gaps=["security_controls", "access_control", "regulatory_coverage"],
    ),
}

# Dimension weights for scoring
_DIMENSION_WEIGHTS: dict[str, float] = {
    "data_privacy": 0.20,
    "security_controls": 0.20,
    "regulatory_coverage": 0.15,
    "access_control": 0.15,
    "incident_response": 0.10,
    "vendor_management": 0.10,
    "documentation": 0.10,
}

# Simulated dimension scores per org (fallback)
_DEFAULT_DIMENSIONS: dict[str, float] = {
    "data_privacy": 82.0,
    "security_controls": 88.0,
    "regulatory_coverage": 75.0,
    "access_control": 90.0,
    "incident_response": 70.0,
    "vendor_management": 65.0,
    "documentation": 78.0,
}

_DEFAULT_FRAMEWORK_SCORES: dict[str, float] = {
    "gdpr": 88.0,
    "hipaa": 76.0,
    "pci_dss": 92.0,
    "soc2": 81.0,
    "eu_ai_act": 68.0,
    "iso_27001": 84.0,
}


class HealthBenchmarkingService:
    """Compliance health score benchmarking with peer comparison and gamification."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._score_cache: dict[str, list[HealthScore]] = {}

    async def compute_health_score(
        self,
        org_id: str,
        industry: str = "saas",
        company_size: str = "medium",
    ) -> HealthScore:
        """Compute the current compliance health score for an organization."""
        dimensions = dict(_DEFAULT_DIMENSIONS)
        overall = sum(
            dimensions[dim] * _DIMENSION_WEIGHTS.get(dim, 0.1)
            for dim in dimensions
        )
        overall = round(overall, 1)
        grade = self._grade_from_score(overall)

        benchmark = _INDUSTRY_BENCHMARKS.get(industry.lower())
        percentile = self._compute_percentile(overall, benchmark) if benchmark else 50.0
        peer_group = f"{industry}_{company_size}"

        score = HealthScore(
            org_id=org_id,
            overall_score=overall,
            grade=grade,
            dimensions=dimensions,
            framework_scores=dict(_DEFAULT_FRAMEWORK_SCORES),
            percentile=round(percentile, 1),
            peer_group=peer_group,
            computed_at=datetime.now(UTC),
        )

        self._score_cache.setdefault(org_id, []).append(score)
        logger.info(
            "Health score computed",
            org_id=org_id,
            score=score.overall_score,
            grade=grade.value,
            percentile=percentile,
        )
        return score

    async def get_peer_benchmark(
        self,
        industry: str,
        company_size: str | None = None,
    ) -> PeerBenchmark:
        """Get aggregated benchmark data for an industry peer group."""
        benchmark = _INDUSTRY_BENCHMARKS.get(industry.lower())
        if not benchmark:
            raise ValueError(f"No benchmark data for industry: {industry}")

        if company_size:
            benchmark = PeerBenchmark(
                peer_group=f"{industry}_{company_size}",
                company_size=CompanySize(company_size),
                industry=benchmark.industry,
                sample_size=benchmark.sample_size // 3,
                avg_score=benchmark.avg_score + 1.5,
                median_score=benchmark.median_score + 1.0,
                p25=benchmark.p25 + 1.0,
                p50=benchmark.p50 + 1.0,
                p75=benchmark.p75 + 0.5,
                p90=benchmark.p90 + 0.5,
                grade_distribution=benchmark.grade_distribution,
                top_gaps=benchmark.top_gaps,
            )

        logger.info("Peer benchmark retrieved", industry=industry, company_size=company_size)
        return benchmark

    async def compare_to_peers(
        self,
        org_id: str,
        industry: str,
        company_size: str | None = None,
    ) -> BenchmarkComparison:
        """Compare an organization's health score against its peer group."""
        score = await self.compute_health_score(org_id, industry, company_size or "medium")
        benchmark = await self.get_peer_benchmark(industry, company_size)

        gap_to_median = round(score.overall_score - benchmark.median_score, 1)
        gap_to_p75 = round(score.overall_score - benchmark.p75, 1)

        rank_position = max(1, int(benchmark.sample_size * (1 - score.percentile / 100)))

        suggestions = await self.get_improvement_plan(org_id, target_grade="A")

        comparison = BenchmarkComparison(
            org_score=score,
            benchmark=benchmark,
            rank_position=rank_position,
            total_in_group=benchmark.sample_size,
            gap_to_median=gap_to_median,
            gap_to_p75=gap_to_p75,
            improvement_suggestions=suggestions[:3],
        )
        logger.info(
            "Peer comparison computed",
            org_id=org_id,
            rank=rank_position,
            total=benchmark.sample_size,
            gap_to_median=gap_to_median,
        )
        return comparison

    async def get_score_history(self, org_id: str, days: int = 90) -> ScoreHistory:
        """Get historical health scores with trend analysis."""
        cached = self._score_cache.get(org_id, [])

        if not cached:
            score = await self.compute_health_score(org_id)
            cached = [score]

        if len(cached) >= 2:
            first = cached[0].overall_score
            last = cached[-1].overall_score
            trend_pct = round(((last - first) / first) * 100, 1) if first > 0 else 0.0
            if trend_pct > 1.0:
                direction = "up"
            elif trend_pct < -1.0:
                direction = "down"
            else:
                direction = "stable"
        else:
            trend_pct = 0.0
            direction = "stable"

        return ScoreHistory(
            scores=list(reversed(cached)),
            trend_direction=direction,
            trend_pct=trend_pct,
            period_days=days,
        )

    async def get_leaderboard(
        self,
        industry: str,
        limit: int = 20,
    ) -> list[LeaderboardEntry]:
        """Get anonymized industry leaderboard for gamification."""
        benchmark = _INDUSTRY_BENCHMARKS.get(industry.lower())
        if not benchmark:
            raise ValueError(f"No benchmark data for industry: {industry}")

        _LEADERBOARD_SEEDS = [
            (96.2, ComplianceGrade.A_PLUS, "up"),
            (94.1, ComplianceGrade.A, "stable"),
            (92.8, ComplianceGrade.A, "up"),
            (91.0, ComplianceGrade.A, "down"),
            (89.5, ComplianceGrade.A_MINUS, "up"),
            (88.2, ComplianceGrade.A_MINUS, "stable"),
            (86.7, ComplianceGrade.A_MINUS, "up"),
            (85.1, ComplianceGrade.A_MINUS, "down"),
            (83.4, ComplianceGrade.B_PLUS, "stable"),
            (81.9, ComplianceGrade.B_PLUS, "up"),
            (80.2, ComplianceGrade.B_PLUS, "stable"),
            (78.6, ComplianceGrade.B, "down"),
            (76.3, ComplianceGrade.B, "up"),
            (74.8, ComplianceGrade.B, "stable"),
            (73.1, ComplianceGrade.B_MINUS, "down"),
            (71.5, ComplianceGrade.B_MINUS, "stable"),
            (69.8, ComplianceGrade.C_PLUS, "up"),
            (67.2, ComplianceGrade.C_PLUS, "down"),
            (64.5, ComplianceGrade.C, "stable"),
            (61.0, ComplianceGrade.C, "down"),
        ]

        entries = []
        for i, (score, grade, trend) in enumerate(_LEADERBOARD_SEEDS[:limit], start=1):
            entries.append(LeaderboardEntry(
                rank=i,
                org_name_anonymized=f"Company-{industry[:3].upper()}-{i:03d}",
                industry=industry,
                score=score,
                grade=grade,
                trend=trend,
            ))

        logger.info("Leaderboard generated", industry=industry, entries=len(entries))
        return entries

    async def generate_board_report(
        self,
        org_id: str,
        industry: str,
        format: str = "pdf",
    ) -> BoardReport:
        """Generate an executive board-ready compliance health report."""
        score = await self.compute_health_score(org_id, industry)
        benchmark = await self.get_peer_benchmark(industry)

        highlights: list[str] = []
        risks: list[str] = []
        action_items: list[str] = []

        # Identify strong dimensions
        for dim, val in sorted(score.dimensions.items(), key=lambda x: x[1], reverse=True):
            label = dim.replace("_", " ").title()
            if val >= 85:
                highlights.append(f"Strong {label}: {val:.0f}/100")
            elif val < 70:
                risks.append(f"{label} score below threshold ({val:.0f}/100)")

        # Peer position
        if score.percentile >= 75:
            highlights.append(
                f"Top {100 - score.percentile:.0f}% in {industry} industry "
                f"({benchmark.sample_size} peers)"
            )
        else:
            action_items.append(
                f"Below {industry} P75 ({benchmark.p75}); "
                f"close {benchmark.p75 - score.overall_score:.1f}-pt gap to reach top quartile"
            )

        # Grade-based messaging
        if score.grade in (ComplianceGrade.D, ComplianceGrade.F):
            risks.append("Overall grade requires immediate executive attention")

        # Improvement actions
        suggestions = await self.get_improvement_plan(org_id, target_grade="A")
        for s in suggestions[:3]:
            action_items.append(
                f"Improve {s.dimension.replace('_', ' ')} "
                f"from {s.current_score:.0f} → {s.target_score:.0f} ({s.effort} effort)"
            )

        report = BoardReport(
            title=f"Compliance Health Dashboard — {industry.title()} — Board Report",
            org_score=score,
            benchmark=benchmark,
            highlights=highlights,
            risks=risks,
            action_items=action_items,
            generated_at=datetime.now(UTC),
            format=format,
        )
        logger.info("Board report generated", org_id=org_id, industry=industry, format=format)
        return report

    async def get_improvement_plan(
        self,
        org_id: str,
        target_grade: str = "A",
    ) -> list[ImprovementSuggestion]:
        """Generate a personalized improvement plan to reach a target grade."""
        target_min = {
            "A+": 95, "A": 90, "A-": 85, "B+": 80, "B": 75,
        }.get(target_grade, 90)

        suggestions: list[ImprovementSuggestion] = []
        for dim, current in sorted(_DEFAULT_DIMENSIONS.items(), key=lambda x: x[1]):
            if current >= target_min:
                continue

            target = min(target_min, current + 15)
            gap = target - current
            effort = "low" if gap <= 5 else ("medium" if gap <= 12 else "high")

            actions = _IMPROVEMENT_ACTIONS.get(dim, [f"Review and improve {dim} controls"])

            impact = f"+{gap * _DIMENSION_WEIGHTS.get(dim, 0.1):.1f} pts overall"

            suggestions.append(ImprovementSuggestion(
                dimension=dim,
                current_score=current,
                target_score=target,
                impact_on_grade=impact,
                effort=effort,
                actions=actions,
            ))

        suggestions.sort(
            key=lambda s: (s.target_score - s.current_score) * _DIMENSION_WEIGHTS.get(s.dimension, 0.1),
            reverse=True,
        )
        logger.info("Improvement plan generated", org_id=org_id, target_grade=target_grade, items=len(suggestions))
        return suggestions

    @staticmethod
    def _grade_from_score(score: float) -> ComplianceGrade:
        if score >= 95:
            return ComplianceGrade.A_PLUS
        if score >= 90:
            return ComplianceGrade.A
        if score >= 85:
            return ComplianceGrade.A_MINUS
        if score >= 80:
            return ComplianceGrade.B_PLUS
        if score >= 75:
            return ComplianceGrade.B
        if score >= 70:
            return ComplianceGrade.B_MINUS
        if score >= 65:
            return ComplianceGrade.C_PLUS
        if score >= 60:
            return ComplianceGrade.C
        if score >= 55:
            return ComplianceGrade.D
        return ComplianceGrade.F

    @staticmethod
    def _compute_percentile(score: float, benchmark: PeerBenchmark) -> float:
        if score >= benchmark.p90:
            return 92.0 + min(7.0, (score - benchmark.p90) / 2)
        if score >= benchmark.p75:
            return 75.0 + 15.0 * (score - benchmark.p75) / max(1, benchmark.p90 - benchmark.p75)
        if score >= benchmark.p50:
            return 50.0 + 25.0 * (score - benchmark.p50) / max(1, benchmark.p75 - benchmark.p50)
        if score >= benchmark.p25:
            return 25.0 + 25.0 * (score - benchmark.p25) / max(1, benchmark.p50 - benchmark.p25)
        return max(1.0, 25.0 * score / max(1, benchmark.p25))


# Dimension-specific improvement actions
_IMPROVEMENT_ACTIONS: dict[str, list[str]] = {
    "vendor_management": [
        "Complete vendor security questionnaires for all Tier-1 vendors",
        "Implement continuous vendor risk monitoring",
        "Establish vendor SLA compliance tracking",
    ],
    "incident_response": [
        "Conduct quarterly incident response tabletop exercises",
        "Update and test incident response runbooks",
        "Implement automated incident detection and escalation",
    ],
    "documentation": [
        "Update data processing agreements with all processors",
        "Complete policy documentation review cycle",
        "Implement automated compliance documentation generation",
    ],
    "regulatory_coverage": [
        "Map controls to EU AI Act requirements",
        "Complete NIS2 directive gap analysis",
        "Add DORA compliance coverage for financial operations",
    ],
    "data_privacy": [
        "Review and update data retention policies",
        "Implement automated consent management",
        "Conduct data protection impact assessments for new processing",
    ],
    "security_controls": [
        "Enable MFA for all administrative accounts",
        "Implement zero-trust network architecture",
        "Deploy runtime application security monitoring",
    ],
    "access_control": [
        "Implement just-in-time privileged access",
        "Complete quarterly access reviews for all systems",
        "Deploy attribute-based access control for sensitive resources",
    ],
}
