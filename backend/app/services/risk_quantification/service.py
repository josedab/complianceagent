"""Compliance Risk Quantification (CRQ) Service."""

import math
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.risk_quantification.models import (
    OrganizationRiskDashboard,
    REGULATION_FINES,
    RepositoryRiskProfile,
    RiskCategory,
    RiskReport,
    RiskSeverity,
    RiskTrend,
    ViolationRisk,
    WhatIfScenario,
)


logger = structlog.get_logger()


class RiskQuantificationService:
    """Service for Compliance Risk Quantification.

    Provides ML-powered dollar-value estimation of compliance risk exposure,
    mapping violations to potential fines and estimating financial impact.
    """

    def __init__(
        self,
        db: AsyncSession,
        organization_id: UUID,
    ):
        self.db = db
        self.organization_id = organization_id

        # Organization context (would be fetched from DB)
        self._org_context: dict[str, Any] = {
            "annual_revenue": 10_000_000,  # Default $10M
            "employee_count": 50,
            "data_subject_count": 100_000,
            "jurisdictions": ["US", "EU"],
        }

        # Historical data (would be from DB)
        self._historical_exposure: list[dict[str, Any]] = []
        self._violation_risks: dict[UUID, ViolationRisk] = {}
        self._repo_profiles: dict[UUID, RepositoryRiskProfile] = {}

    def set_organization_context(
        self,
        annual_revenue: float | None = None,
        employee_count: int | None = None,
        data_subject_count: int | None = None,
        jurisdictions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Set organization context for risk calculations."""
        if annual_revenue is not None:
            self._org_context["annual_revenue"] = annual_revenue
        if employee_count is not None:
            self._org_context["employee_count"] = employee_count
        if data_subject_count is not None:
            self._org_context["data_subject_count"] = data_subject_count
        if jurisdictions is not None:
            self._org_context["jurisdictions"] = jurisdictions

        return self._org_context

    def get_organization_context(self) -> dict[str, Any]:
        """Get current organization context."""
        return self._org_context.copy()

    # ========================================================================
    # Violation Risk Assessment
    # ========================================================================

    def assess_violation_risk(
        self,
        rule_id: str,
        regulation: str,
        severity: str,
        file_path: str | None = None,
        affected_records: int | None = None,
        aggravating_factors: list[str] | None = None,
        mitigating_factors: list[str] | None = None,
    ) -> ViolationRisk:
        """Assess the financial risk of a single violation."""
        # Get fine structure for regulation
        fine_structure = REGULATION_FINES.get(regulation)

        # Calculate base exposure
        if fine_structure:
            # Calculate maximum potential fine
            revenue_based_fine = self._org_context["annual_revenue"] * fine_structure.max_fine_percent_revenue
            max_fine = max(fine_structure.max_fine_absolute, revenue_based_fine)

            # Per-record calculations if applicable
            if fine_structure.per_record_fine and affected_records:
                record_fine = fine_structure.per_record_fine * affected_records
                max_fine = min(max_fine, record_fine)  # Cap at regulation max

            min_fine = fine_structure.min_fine
        else:
            # Default estimates for unknown regulations
            max_fine = 100_000
            min_fine = 1_000

        # Calculate likelihood based on severity
        severity_enum = RiskSeverity(severity.lower()) if severity else RiskSeverity.MEDIUM
        likelihood = self._calculate_likelihood(severity_enum)

        # Apply aggravating/mitigating factors
        factor_multiplier = self._calculate_factor_multiplier(
            aggravating_factors or [],
            mitigating_factors or [],
        )

        # Calculate expected exposure
        # Using triangular distribution approximation
        expected = (min_fine + max_fine * factor_multiplier + max_fine) / 3
        expected *= likelihood

        # Determine risk category
        category = self._determine_risk_category(rule_id, regulation)

        # Calculate confidence based on available data
        confidence = self._calculate_confidence(
            has_fine_structure=fine_structure is not None,
            has_affected_records=affected_records is not None,
            has_factors=bool(aggravating_factors or mitigating_factors),
        )

        risk = ViolationRisk(
            rule_id=rule_id,
            regulation=regulation,
            severity=severity_enum,
            category=category,
            min_exposure=min_fine,
            max_exposure=max_fine * factor_multiplier,
            expected_exposure=expected,
            confidence=confidence,
            likelihood=likelihood,
            impact_multiplier=factor_multiplier,
            aggravating_factors=aggravating_factors or [],
            mitigating_factors=mitigating_factors or [],
            file_path=file_path,
        )

        self._violation_risks[risk.id] = risk

        logger.info(
            "Violation risk assessed",
            rule_id=rule_id,
            regulation=regulation,
            expected_exposure=expected,
            confidence=confidence,
        )

        return risk

    def _calculate_likelihood(self, severity: RiskSeverity) -> float:
        """Calculate likelihood of enforcement based on severity."""
        likelihood_map = {
            RiskSeverity.CRITICAL: 0.8,
            RiskSeverity.HIGH: 0.6,
            RiskSeverity.MEDIUM: 0.4,
            RiskSeverity.LOW: 0.2,
            RiskSeverity.NEGLIGIBLE: 0.05,
        }
        return likelihood_map.get(severity, 0.4)

    def _calculate_factor_multiplier(
        self,
        aggravating: list[str],
        mitigating: list[str],
    ) -> float:
        """Calculate multiplier based on aggravating/mitigating factors."""
        # Each aggravating factor adds 20%, each mitigating reduces by 15%
        aggravating_effect = 1.0 + (len(aggravating) * 0.2)
        mitigating_effect = 1.0 - (len(mitigating) * 0.15)

        # Combine effects, floor at 0.1, cap at 3.0
        multiplier = aggravating_effect * mitigating_effect
        return max(0.1, min(3.0, multiplier))

    def _determine_risk_category(self, rule_id: str, regulation: str) -> RiskCategory:
        """Determine risk category based on rule and regulation."""
        rule_lower = rule_id.lower()

        if "breach" in rule_lower or "leak" in rule_lower:
            return RiskCategory.DATA_BREACH
        if "pii" in rule_lower or "privacy" in rule_lower or regulation in ["GDPR", "CCPA", "HIPAA"]:
            return RiskCategory.REGULATORY_FINE
        if "vendor" in rule_lower or "third" in rule_lower:
            return RiskCategory.THIRD_PARTY
        if "audit" in rule_lower or "sox" in regulation:
            return RiskCategory.OPERATIONAL

        return RiskCategory.REGULATORY_FINE

    def _calculate_confidence(
        self,
        has_fine_structure: bool,
        has_affected_records: bool,
        has_factors: bool,
    ) -> float:
        """Calculate confidence score for the estimate."""
        confidence = 0.3  # Base confidence

        if has_fine_structure:
            confidence += 0.3
        if has_affected_records:
            confidence += 0.2
        if has_factors:
            confidence += 0.2

        return min(1.0, confidence)

    # ========================================================================
    # Repository Risk Profile
    # ========================================================================

    def generate_repository_profile(
        self,
        repository_id: UUID,
        repository_name: str,
        violations: list[dict[str, Any]],
    ) -> RepositoryRiskProfile:
        """Generate a risk profile for a repository."""
        profile = RepositoryRiskProfile(
            repository_id=repository_id,
            repository_name=repository_name,
        )

        # Process each violation
        for violation in violations:
            risk = self.assess_violation_risk(
                rule_id=violation.get("rule_id", "UNKNOWN"),
                regulation=violation.get("regulation", "Unknown"),
                severity=violation.get("severity", "medium"),
                file_path=violation.get("file_path"),
                affected_records=violation.get("affected_records"),
            )

            # Update counts
            profile.total_violations += 1
            if risk.severity == RiskSeverity.CRITICAL:
                profile.critical_violations += 1
            elif risk.severity == RiskSeverity.HIGH:
                profile.high_violations += 1
            elif risk.severity == RiskSeverity.MEDIUM:
                profile.medium_violations += 1
            else:
                profile.low_violations += 1

            # Accumulate exposure
            profile.total_min_exposure += risk.min_exposure
            profile.total_max_exposure += risk.max_exposure
            profile.total_expected_exposure += risk.expected_exposure

            # Track by regulation
            reg = risk.regulation
            profile.exposure_by_regulation[reg] = (
                profile.exposure_by_regulation.get(reg, 0) + risk.expected_exposure
            )

            # Track by category
            cat = risk.category.value
            profile.exposure_by_category[cat] = (
                profile.exposure_by_category.get(cat, 0) + risk.expected_exposure
            )

        # Calculate risk scores
        profile.overall_risk_score = self._calculate_risk_score(
            profile.total_expected_exposure,
            profile.total_violations,
            profile.critical_violations,
        )

        # Calculate sub-scores
        privacy_regs = ["GDPR", "CCPA", "HIPAA"]
        privacy_exposure = sum(
            profile.exposure_by_regulation.get(r, 0) for r in privacy_regs
        )
        profile.data_privacy_score = 100 - min(100, (privacy_exposure / 100_000) * 10)

        security_cats = [RiskCategory.DATA_BREACH.value, RiskCategory.OPERATIONAL.value]
        security_exposure = sum(
            profile.exposure_by_category.get(c, 0) for c in security_cats
        )
        profile.security_score = 100 - min(100, (security_exposure / 100_000) * 10)

        profile.compliance_score = 100 - min(100, (profile.total_violations * 5))

        self._repo_profiles[repository_id] = profile

        return profile

    def _calculate_risk_score(
        self,
        expected_exposure: float,
        total_violations: int,
        critical_violations: int,
    ) -> float:
        """Calculate overall risk score (0-100, higher = more risk)."""
        # Base score from exposure (log scale)
        if expected_exposure > 0:
            exposure_score = min(50, 10 * math.log10(expected_exposure + 1))
        else:
            exposure_score = 0

        # Violation count contribution
        violation_score = min(30, total_violations * 2)

        # Critical violation penalty
        critical_penalty = min(20, critical_violations * 10)

        return min(100, exposure_score + violation_score + critical_penalty)

    # ========================================================================
    # Organization Dashboard
    # ========================================================================

    def generate_organization_dashboard(
        self,
        repository_profiles: list[RepositoryRiskProfile] | None = None,
    ) -> OrganizationRiskDashboard:
        """Generate organization-wide risk dashboard."""
        profiles = repository_profiles or list(self._repo_profiles.values())

        dashboard = OrganizationRiskDashboard(
            organization_id=self.organization_id,
            annual_revenue=self._org_context["annual_revenue"],
            employee_count=self._org_context["employee_count"],
            data_subject_count=self._org_context["data_subject_count"],
            jurisdictions=self._org_context["jurisdictions"],
        )

        # Aggregate from repository profiles
        for profile in profiles:
            dashboard.total_min_exposure += profile.total_min_exposure
            dashboard.total_max_exposure += profile.total_max_exposure
            dashboard.total_expected_exposure += profile.total_expected_exposure

            # By repository
            dashboard.exposure_by_repository[profile.repository_name] = profile.total_expected_exposure

            # By regulation (merge)
            for reg, exp in profile.exposure_by_regulation.items():
                if reg not in dashboard.exposure_by_regulation:
                    dashboard.exposure_by_regulation[reg] = {"expected": 0, "min": 0, "max": 0}
                dashboard.exposure_by_regulation[reg]["expected"] += exp

            # By severity
            dashboard.exposure_by_severity["critical"] = (
                dashboard.exposure_by_severity.get("critical", 0) +
                profile.critical_violations * 50_000  # Rough estimate
            )
            dashboard.exposure_by_severity["high"] = (
                dashboard.exposure_by_severity.get("high", 0) +
                profile.high_violations * 20_000
            )
            dashboard.exposure_by_severity["medium"] = (
                dashboard.exposure_by_severity.get("medium", 0) +
                profile.medium_violations * 5_000
            )

        # Calculate overall risk score
        total_violations = sum(p.total_violations for p in profiles)
        total_critical = sum(p.critical_violations for p in profiles)
        dashboard.overall_risk_score = self._calculate_risk_score(
            dashboard.total_expected_exposure,
            total_violations,
            total_critical,
        )

        # Assign grade
        dashboard.risk_grade = self._score_to_grade(dashboard.overall_risk_score)

        # Get top risks
        all_risks = list(self._violation_risks.values())
        all_risks.sort(key=lambda r: r.expected_exposure, reverse=True)
        dashboard.top_risks = all_risks[:10]

        # Generate recommendations
        dashboard.recommended_actions = self._generate_recommendations(
            dashboard.exposure_by_regulation,
            total_critical,
            dashboard.total_expected_exposure,
        )

        # Trend analysis (simplified)
        dashboard.risk_trend = self._calculate_trend()

        # Industry benchmark (simulated)
        dashboard.industry_benchmark = 500_000  # Industry average exposure
        if dashboard.total_expected_exposure < dashboard.industry_benchmark:
            dashboard.percentile_rank = 25  # Better than 75%
        elif dashboard.total_expected_exposure < dashboard.industry_benchmark * 2:
            dashboard.percentile_rank = 50
        else:
            dashboard.percentile_rank = 75  # Worse than 75%

        return dashboard

    def _score_to_grade(self, score: float) -> str:
        """Convert risk score to letter grade."""
        if score <= 20:
            return "A"
        if score <= 40:
            return "B"
        if score <= 60:
            return "C"
        if score <= 80:
            return "D"
        return "F"

    def _calculate_trend(self) -> RiskTrend:
        """Calculate risk trend from historical data."""
        if len(self._historical_exposure) < 2:
            return RiskTrend.STABLE

        recent = self._historical_exposure[-1].get("value", 0)
        previous = self._historical_exposure[-2].get("value", 0)

        if recent > previous * 1.1:
            return RiskTrend.INCREASING
        if recent < previous * 0.9:
            return RiskTrend.DECREASING
        return RiskTrend.STABLE

    def _generate_recommendations(
        self,
        exposure_by_regulation: dict[str, dict[str, float]],
        critical_count: int,
        total_exposure: float,
    ) -> list[dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Critical violations
        if critical_count > 0:
            recommendations.append({
                "priority": "critical",
                "action": f"Address {critical_count} critical violations immediately",
                "impact": "Could reduce exposure by up to 50%",
                "estimated_reduction": total_exposure * 0.5,
            })

        # Top regulation exposure
        sorted_regs = sorted(
            exposure_by_regulation.items(),
            key=lambda x: x[1].get("expected", 0),
            reverse=True,
        )

        for reg, exposure in sorted_regs[:3]:
            exp_value = exposure.get("expected", 0)
            recommendations.append({
                "priority": "high",
                "action": f"Focus on {reg} compliance - highest exposure",
                "impact": f"${exp_value:,.0f} potential exposure",
                "estimated_reduction": exp_value * 0.7,
            })

        return recommendations

    # ========================================================================
    # What-If Scenarios
    # ========================================================================

    def run_what_if_scenario(
        self,
        scenario_type: str,
        parameters: dict[str, Any],
    ) -> WhatIfScenario:
        """Run a what-if scenario analysis."""
        # Get current baseline
        current_risks = list(self._violation_risks.values())
        baseline_exposure = sum(r.expected_exposure for r in current_risks)

        scenario = WhatIfScenario(
            name=f"What-If: {scenario_type}",
            scenario_type=scenario_type,
            parameters=parameters,
            baseline_exposure=baseline_exposure,
        )

        if scenario_type == "fix_violations":
            # What if we fix specific violations?
            fix_ids = parameters.get("violation_ids", [])
            fixed_exposure = sum(
                r.expected_exposure for r in current_risks
                if str(r.id) not in fix_ids
            )
            scenario.scenario_exposure = fixed_exposure
            scenario.affected_violations = [UUID(v) for v in fix_ids if v]
            scenario.description = f"Scenario: Fix {len(fix_ids)} violations"
            scenario.recommendation = "Implement fixes to reduce exposure"

        elif scenario_type == "data_breach":
            # What if a data breach occurs?
            breach_records = parameters.get("affected_records", 10000)
            breach_regulation = parameters.get("regulation", "GDPR")

            # Estimate breach cost
            fine_structure = REGULATION_FINES.get(breach_regulation)
            if fine_structure and fine_structure.per_record_fine:
                breach_cost = fine_structure.per_record_fine * breach_records
            else:
                breach_cost = breach_records * 150  # Average cost per record

            scenario.scenario_exposure = baseline_exposure + breach_cost
            scenario.description = f"Scenario: Data breach affecting {breach_records:,} records"
            scenario.affected_regulations = [breach_regulation]
            scenario.recommendation = "Implement breach prevention measures"
            scenario.priority = "critical"

        elif scenario_type == "new_regulation":
            # What if a new regulation applies?
            new_reg = parameters.get("regulation", "EU AI Act")
            estimated_violations = parameters.get("estimated_violations", 5)

            new_exposure = 0
            fine_structure = REGULATION_FINES.get(new_reg)
            if fine_structure:
                avg_fine = fine_structure.max_fine_absolute * 0.1  # 10% of max
                new_exposure = avg_fine * estimated_violations

            scenario.scenario_exposure = baseline_exposure + new_exposure
            scenario.description = f"Scenario: {new_reg} now applies to your organization"
            scenario.affected_regulations = [new_reg]
            scenario.recommendation = f"Prepare for {new_reg} compliance"

        elif scenario_type == "revenue_change":
            # What if revenue changes (affects percentage-based fines)?
            new_revenue = parameters.get("new_revenue", self._org_context["annual_revenue"] * 2)
            multiplier = new_revenue / self._org_context["annual_revenue"]

            # Recalculate exposure with new revenue
            scenario.scenario_exposure = baseline_exposure * multiplier
            scenario.description = f"Scenario: Revenue changes to ${new_revenue:,.0f}"
            scenario.recommendation = "Review compliance as business scales"

        # Calculate delta
        scenario.exposure_delta = scenario.scenario_exposure - baseline_exposure
        if baseline_exposure > 0:
            scenario.exposure_delta_percent = (
                (scenario.exposure_delta / baseline_exposure) * 100
            )

        return scenario

    # ========================================================================
    # Executive Reports
    # ========================================================================

    def generate_executive_report(
        self,
        report_type: str = "monthly",
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> RiskReport:
        """Generate an executive risk report."""
        dashboard = self.generate_organization_dashboard()

        report = RiskReport(
            organization_id=self.organization_id,
            report_type=report_type,
            title=f"Compliance Risk Report - {report_type.capitalize()}",
            total_exposure=dashboard.total_expected_exposure,
            risk_score=dashboard.overall_risk_score,
            risk_grade=dashboard.risk_grade,
            exposure_by_regulation={
                k: v.get("expected", 0) for k, v in dashboard.exposure_by_regulation.items()
            },
            exposure_by_category=dashboard.exposure_by_severity,
            period_start=period_start or datetime.now(UTC),
            period_end=period_end or datetime.now(UTC),
        )

        # Generate summary
        report.summary = self._generate_executive_summary(dashboard)

        # Key findings
        report.key_findings = [
            f"Total compliance risk exposure: ${dashboard.total_expected_exposure:,.0f}",
            f"Risk grade: {dashboard.risk_grade} (score: {dashboard.overall_risk_score:.1f}/100)",
            f"Top risk area: {max(dashboard.exposure_by_regulation.keys(), key=lambda k: dashboard.exposure_by_regulation[k].get('expected', 0), default='N/A')}",
        ]

        if dashboard.risk_trend == RiskTrend.INCREASING:
            report.key_findings.append("WARNING: Risk exposure is increasing")

        # Key recommendations
        report.key_recommendations = [
            r["action"] for r in dashboard.recommended_actions[:5]
        ]

        # Historical data
        report.historical_exposure = self._historical_exposure[-12:]  # Last 12 periods

        # Remediation roadmap
        report.remediation_roadmap = self._generate_remediation_roadmap(dashboard)

        # Calculate projected exposure after remediation
        total_reduction = sum(
            r.get("estimated_reduction", 0) for r in report.remediation_roadmap
        )
        report.projected_exposure_after_remediation = max(
            0, dashboard.total_expected_exposure - total_reduction
        )

        # Industry comparison
        report.industry_comparison = {
            "industry_average": dashboard.industry_benchmark,
            "your_exposure": dashboard.total_expected_exposure,
            "percentile_rank": dashboard.percentile_rank,
            "comparison": "below" if dashboard.total_expected_exposure < (dashboard.industry_benchmark or 0) else "above",
        }

        return report

    def _generate_executive_summary(
        self,
        dashboard: OrganizationRiskDashboard,
    ) -> str:
        """Generate executive summary text."""
        grade_descriptions = {
            "A": "excellent compliance posture with minimal risk",
            "B": "good compliance posture with manageable risk",
            "C": "moderate compliance posture requiring attention",
            "D": "concerning compliance posture requiring immediate action",
            "F": "critical compliance issues requiring urgent remediation",
        }

        summary = f"""
Your organization's compliance risk exposure is estimated at ${dashboard.total_expected_exposure:,.0f}
(range: ${dashboard.total_min_exposure:,.0f} - ${dashboard.total_max_exposure:,.0f}).

Overall risk grade: {dashboard.risk_grade} - {grade_descriptions.get(dashboard.risk_grade, '')}

Risk trend: {dashboard.risk_trend.value.capitalize()}

Key areas of concern:
{chr(10).join(f"- {k}: ${v.get('expected', 0):,.0f}" for k, v in sorted(dashboard.exposure_by_regulation.items(), key=lambda x: x[1].get('expected', 0), reverse=True)[:3])}
""".strip()

        return summary

    def _generate_remediation_roadmap(
        self,
        dashboard: OrganizationRiskDashboard,
    ) -> list[dict[str, Any]]:
        """Generate a prioritized remediation roadmap."""
        roadmap = []

        # Sort regulations by exposure
        sorted_regs = sorted(
            dashboard.exposure_by_regulation.items(),
            key=lambda x: x[1].get("expected", 0),
            reverse=True,
        )

        priority = 1
        for reg, exposure in sorted_regs[:5]:
            exp_value = exposure.get("expected", 0)
            roadmap.append({
                "priority": priority,
                "area": reg,
                "current_exposure": exp_value,
                "estimated_reduction": exp_value * 0.6,  # 60% reduction target
                "actions": [
                    f"Review all {reg} violations",
                    f"Implement automated compliance checks for {reg}",
                    f"Update data handling procedures for {reg}",
                ],
                "estimated_effort": "medium" if exp_value < 100000 else "high",
            })
            priority += 1

        return roadmap


def get_risk_quantification_service(
    db: AsyncSession,
    organization_id: UUID,
) -> RiskQuantificationService:
    """Factory function to create Risk Quantification service."""
    return RiskQuantificationService(db=db, organization_id=organization_id)
