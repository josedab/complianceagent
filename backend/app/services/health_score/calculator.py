"""Health score calculation engine."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4
import random

from app.services.health_score.models import (
    CategoryScore,
    DEFAULT_WEIGHTS,
    HealthScore,
    ScoreCategory,
    ScoreGrade,
    ScoreHistory,
    TrendDirection,
    score_to_grade,
)


class ScoreCalculator:
    """Calculates compliance health scores."""
    
    def __init__(self):
        self._scores: dict[UUID, HealthScore] = {}
        self._history: dict[UUID, list[ScoreHistory]] = {}
        self._weights = DEFAULT_WEIGHTS.copy()
    
    async def calculate_score(
        self,
        repository_id: UUID,
        regulations: list[str] | None = None,
        force_refresh: bool = False,
    ) -> HealthScore:
        """Calculate comprehensive health score for a repository."""
        # Check cache (unless force refresh)
        if not force_refresh and repository_id in self._scores:
            cached = self._scores[repository_id]
            if (datetime.utcnow() - cached.calculated_at) < timedelta(hours=1):
                return cached
        
        # Get previous score for trend
        previous = self._scores.get(repository_id)
        
        # Calculate each category
        category_scores = await self._calculate_all_categories(
            repository_id, regulations or []
        )
        
        # Compute overall score
        overall_score = sum(cs.weighted_score for cs in category_scores.values())
        overall_score = min(100, max(0, overall_score))
        
        # Determine trend
        trend, trend_delta = self._calculate_trend(
            overall_score,
            previous.overall_score if previous else None,
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(category_scores)
        
        # Control stats from category details
        control_stats = category_scores.get(
            ScoreCategory.CONTROL_IMPLEMENTATION.value,
            CategoryScore(
                category=ScoreCategory.CONTROL_IMPLEMENTATION,
                score=0,
                weight=0,
            ),
        ).details
        
        score = HealthScore(
            id=uuid4(),
            repository_id=repository_id,
            overall_score=overall_score,
            grade=score_to_grade(overall_score),
            category_scores=category_scores,
            calculated_at=datetime.utcnow(),
            trend=trend,
            trend_delta=trend_delta,
            previous_score=previous.overall_score if previous else None,
            regulations_checked=regulations or [],
            total_controls=control_stats.get("total", 0),
            passing_controls=control_stats.get("passing", 0),
            failing_controls=control_stats.get("failing", 0),
            not_applicable_controls=control_stats.get("not_applicable", 0),
            recommendations=recommendations,
        )
        
        # Cache and record history
        self._scores[repository_id] = score
        self._record_history(score)
        
        return score
    
    async def _calculate_all_categories(
        self,
        repository_id: UUID,
        regulations: list[str],
    ) -> dict[str, CategoryScore]:
        """Calculate scores for all categories."""
        return {
            ScoreCategory.REGULATORY_COVERAGE.value: await self._calc_regulatory_coverage(
                repository_id, regulations
            ),
            ScoreCategory.CONTROL_IMPLEMENTATION.value: await self._calc_control_implementation(
                repository_id, regulations
            ),
            ScoreCategory.EVIDENCE_FRESHNESS.value: await self._calc_evidence_freshness(
                repository_id
            ),
            ScoreCategory.ISSUE_MANAGEMENT.value: await self._calc_issue_management(
                repository_id
            ),
            ScoreCategory.SECURITY_POSTURE.value: await self._calc_security_posture(
                repository_id
            ),
            ScoreCategory.POLICY_COMPLIANCE.value: await self._calc_policy_compliance(
                repository_id
            ),
        }
    
    async def _calc_regulatory_coverage(
        self,
        repository_id: UUID,
        regulations: list[str],
    ) -> CategoryScore:
        """Calculate regulatory coverage score."""
        # Simulate coverage analysis
        covered = len(regulations) if regulations else 0
        target_regulations = ["SOC2", "HIPAA", "GDPR", "PCI-DSS", "ISO27001"]
        total = len(target_regulations)
        
        coverage_pct = min(100, (covered / max(total, 1)) * 100 + random.uniform(20, 40))
        
        recommendations = []
        if covered < 3:
            recommendations.append("Consider expanding regulatory coverage to additional frameworks")
        
        return CategoryScore(
            category=ScoreCategory.REGULATORY_COVERAGE,
            score=coverage_pct,
            weight=self._weights[ScoreCategory.REGULATORY_COVERAGE],
            details={
                "covered_regulations": regulations,
                "total_target": total,
                "coverage_percentage": coverage_pct,
            },
            recommendations=recommendations,
        )
    
    async def _calc_control_implementation(
        self,
        repository_id: UUID,
        regulations: list[str],
    ) -> CategoryScore:
        """Calculate control implementation score."""
        # Simulate control analysis
        total = random.randint(80, 150)
        passing = int(total * random.uniform(0.7, 0.95))
        failing = int((total - passing) * random.uniform(0.3, 0.7))
        not_applicable = total - passing - failing
        
        score = (passing / max(total - not_applicable, 1)) * 100
        
        recommendations = []
        if failing > 5:
            recommendations.append(f"Address {failing} failing controls to improve compliance")
        
        return CategoryScore(
            category=ScoreCategory.CONTROL_IMPLEMENTATION,
            score=score,
            weight=self._weights[ScoreCategory.CONTROL_IMPLEMENTATION],
            details={
                "total": total,
                "passing": passing,
                "failing": failing,
                "not_applicable": not_applicable,
            },
            recommendations=recommendations,
        )
    
    async def _calc_evidence_freshness(
        self,
        repository_id: UUID,
    ) -> CategoryScore:
        """Calculate evidence freshness score."""
        # Simulate evidence age analysis
        total_evidence = random.randint(50, 100)
        fresh_count = int(total_evidence * random.uniform(0.6, 0.9))
        stale_count = total_evidence - fresh_count
        
        avg_age_days = random.randint(10, 60)
        score = max(0, 100 - (avg_age_days * 0.5) - (stale_count * 2))
        
        recommendations = []
        if stale_count > 10:
            recommendations.append(f"Refresh {stale_count} stale evidence items")
        
        return CategoryScore(
            category=ScoreCategory.EVIDENCE_FRESHNESS,
            score=score,
            weight=self._weights[ScoreCategory.EVIDENCE_FRESHNESS],
            details={
                "total_evidence": total_evidence,
                "fresh_items": fresh_count,
                "stale_items": stale_count,
                "average_age_days": avg_age_days,
            },
            recommendations=recommendations,
        )
    
    async def _calc_issue_management(
        self,
        repository_id: UUID,
    ) -> CategoryScore:
        """Calculate issue management score."""
        # Simulate issue tracking
        total_issues = random.randint(5, 30)
        open_issues = int(total_issues * random.uniform(0.1, 0.4))
        critical_open = int(open_issues * random.uniform(0, 0.3))
        resolved_issues = total_issues - open_issues
        
        avg_resolution_days = random.randint(3, 21)
        
        score = 100 - (open_issues * 3) - (critical_open * 10) - (avg_resolution_days * 0.5)
        score = max(0, min(100, score))
        
        recommendations = []
        if critical_open > 0:
            recommendations.append(f"Resolve {critical_open} critical issues immediately")
        if avg_resolution_days > 14:
            recommendations.append("Improve issue resolution time (currently averaging {avg_resolution_days} days)")
        
        return CategoryScore(
            category=ScoreCategory.ISSUE_MANAGEMENT,
            score=score,
            weight=self._weights[ScoreCategory.ISSUE_MANAGEMENT],
            details={
                "total_issues": total_issues,
                "open_issues": open_issues,
                "critical_open": critical_open,
                "resolved_issues": resolved_issues,
                "avg_resolution_days": avg_resolution_days,
            },
            recommendations=recommendations,
        )
    
    async def _calc_security_posture(
        self,
        repository_id: UUID,
    ) -> CategoryScore:
        """Calculate security posture score."""
        # Simulate security analysis
        checks_passed = random.randint(15, 25)
        checks_total = 25
        vulnerabilities = random.randint(0, 10)
        high_vulns = int(vulnerabilities * random.uniform(0, 0.3))
        
        score = (checks_passed / checks_total) * 100 - (vulnerabilities * 2) - (high_vulns * 5)
        score = max(0, min(100, score))
        
        recommendations = []
        if high_vulns > 0:
            recommendations.append(f"Address {high_vulns} high-severity vulnerabilities")
        if checks_passed < checks_total:
            recommendations.append(f"Fix {checks_total - checks_passed} failing security checks")
        
        return CategoryScore(
            category=ScoreCategory.SECURITY_POSTURE,
            score=score,
            weight=self._weights[ScoreCategory.SECURITY_POSTURE],
            details={
                "security_checks_passed": checks_passed,
                "security_checks_total": checks_total,
                "vulnerabilities_found": vulnerabilities,
                "high_severity_vulns": high_vulns,
            },
            recommendations=recommendations,
        )
    
    async def _calc_policy_compliance(
        self,
        repository_id: UUID,
    ) -> CategoryScore:
        """Calculate policy compliance score."""
        # Simulate policy checks
        policies_total = random.randint(5, 15)
        policies_passing = int(policies_total * random.uniform(0.7, 1.0))
        violations = policies_total - policies_passing
        
        score = (policies_passing / max(policies_total, 1)) * 100
        
        recommendations = []
        if violations > 0:
            recommendations.append(f"Resolve {violations} policy violations")
        
        return CategoryScore(
            category=ScoreCategory.POLICY_COMPLIANCE,
            score=score,
            weight=self._weights[ScoreCategory.POLICY_COMPLIANCE],
            details={
                "policies_total": policies_total,
                "policies_passing": policies_passing,
                "violations": violations,
            },
            recommendations=recommendations,
        )
    
    def _calculate_trend(
        self,
        current: float,
        previous: float | None,
    ) -> tuple[TrendDirection, float]:
        """Determine trend direction and delta."""
        if previous is None:
            return TrendDirection.STABLE, 0.0
        
        delta = current - previous
        
        if abs(delta) < 1:
            return TrendDirection.STABLE, delta
        elif delta > 0:
            return TrendDirection.IMPROVING, delta
        else:
            return TrendDirection.DECLINING, delta
    
    def _generate_recommendations(
        self,
        category_scores: dict[str, CategoryScore],
    ) -> list[str]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Sort categories by score (lowest first)
        sorted_cats = sorted(
            category_scores.values(),
            key=lambda c: c.score,
        )
        
        # Take recommendations from lowest-scoring categories
        for cat in sorted_cats[:3]:
            recommendations.extend(cat.recommendations[:2])
        
        return recommendations[:5]
    
    def _record_history(self, score: HealthScore):
        """Record score in history."""
        if score.repository_id not in self._history:
            self._history[score.repository_id] = []
        
        record = ScoreHistory(
            id=uuid4(),
            repository_id=score.repository_id,
            score=score.overall_score,
            grade=score.grade,
            recorded_at=score.calculated_at,
            metadata={
                "category_scores": {
                    k: v.score for k, v in score.category_scores.items()
                },
            },
        )
        
        self._history[score.repository_id].append(record)
        
        # Keep only last 100 records
        if len(self._history[score.repository_id]) > 100:
            self._history[score.repository_id] = self._history[score.repository_id][-100:]
    
    async def get_history(
        self,
        repository_id: UUID,
        days: int = 30,
    ) -> list[ScoreHistory]:
        """Get score history for a repository."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        history = self._history.get(repository_id, [])
        return [h for h in history if h.recorded_at >= cutoff]
    
    def set_category_weight(
        self,
        category: ScoreCategory,
        weight: float,
    ):
        """Customize category weight."""
        if 0 <= weight <= 1:
            self._weights[category] = weight
            # Renormalize
            total = sum(self._weights.values())
            if total > 0:
                for cat in self._weights:
                    self._weights[cat] /= total


# Singleton instance
_calculator: ScoreCalculator | None = None


def get_score_calculator() -> ScoreCalculator:
    """Get singleton calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = ScoreCalculator()
    return _calculator
