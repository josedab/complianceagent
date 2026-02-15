"""Predictive Compliance Cost Calculator service."""

from __future__ import annotations

import math
from typing import Any
from uuid import uuid4

import structlog

from app.services.cost_calculator.models import (
    ComparableImpl,
    ComplexityLevel,
    CostBreakdownItem,
    CostHistory,
    CostPrediction,
    ExecutiveReport,
    RegulationCategory,
    ROISummary,
    ScenarioComparison,
)


logger = structlog.get_logger()

# Base estimates: (developer_days, cost_multiplier) per regulation
_BASE_ESTIMATES: dict[str, tuple[float, float, RegulationCategory]] = {
    "gdpr": (60.0, 1.0, RegulationCategory.DATA_PRIVACY),
    "ccpa": (35.0, 0.8, RegulationCategory.DATA_PRIVACY),
    "hipaa": (80.0, 1.3, RegulationCategory.HEALTHCARE),
    "eu_ai_act": (90.0, 1.5, RegulationCategory.AI_GOVERNANCE),
    "pci_dss": (50.0, 1.1, RegulationCategory.SECURITY),
    "soc2": (45.0, 1.0, RegulationCategory.SECURITY),
    "sox": (70.0, 1.2, RegulationCategory.FINANCIAL),
    "iso_27001": (55.0, 1.0, RegulationCategory.SECURITY),
    "nist_csf": (40.0, 0.9, RegulationCategory.SECURITY),
    "dora": (65.0, 1.2, RegulationCategory.FINANCIAL),
    "fedramp": (100.0, 1.6, RegulationCategory.SECURITY),
    "lgpd": (30.0, 0.7, RegulationCategory.DATA_PRIVACY),
    "pipeda": (25.0, 0.6, RegulationCategory.DATA_PRIVACY),
    "glba": (45.0, 1.0, RegulationCategory.FINANCIAL),
}

# Industry multipliers applied on top of base estimates
_INDUSTRY_MULTIPLIERS: dict[str, float] = {
    "saas": 1.0,
    "fintech": 1.3,
    "healthtech": 1.4,
    "enterprise": 1.2,
    "startup": 0.7,
    "government": 1.5,
}

_COMPARABLE_DATA: dict[str, list[ComparableImpl]] = {
    "gdpr": [
        ComparableImpl("GDPR", "SaaS", "50-200", 55.0, 412_500.0, 2023),
        ComparableImpl("GDPR", "Fintech", "200-500", 75.0, 750_000.0, 2023),
        ComparableImpl("GDPR", "Enterprise", "500+", 90.0, 1_125_000.0, 2022),
    ],
    "hipaa": [
        ComparableImpl("HIPAA", "HealthTech", "50-200", 85.0, 637_500.0, 2023),
        ComparableImpl("HIPAA", "Enterprise", "500+", 110.0, 1_375_000.0, 2022),
    ],
    "soc2": [
        ComparableImpl("SOC 2", "SaaS", "10-50", 30.0, 225_000.0, 2024),
        ComparableImpl("SOC 2", "SaaS", "50-200", 50.0, 375_000.0, 2023),
    ],
    "pci_dss": [
        ComparableImpl("PCI-DSS", "Fintech", "50-200", 55.0, 412_500.0, 2023),
        ComparableImpl("PCI-DSS", "E-Commerce", "200-500", 65.0, 650_000.0, 2022),
    ],
    "eu_ai_act": [
        ComparableImpl("EU AI Act", "AI/ML", "50-200", 100.0, 750_000.0, 2024),
    ],
}


class CostCalculatorService:
    """Predicts time, cost, and risk for upcoming compliance regulations."""

    def __init__(self, db, copilot_client=None):
        self.db = db
        self.copilot_client = copilot_client

    async def predict_cost(
        self,
        regulation: str,
        org_id: str,
        team_size: int = 10,
        avg_hourly_rate: float = 75.0,
        industry: str = "saas",
    ) -> CostPrediction:
        """Predict compliance implementation cost for a regulation."""
        reg_key = regulation.lower().replace("-", "_").replace(" ", "_")
        category = self._get_category(reg_key)
        complexity = self._estimate_complexity(reg_key)
        base_days, cost_mult = self._get_base_estimates(reg_key, category)
        adjusted_days = self._apply_team_adjustments(base_days, team_size)

        industry_mult = _INDUSTRY_MULTIPLIERS.get(industry.lower(), 1.0)
        total_days = adjusted_days * cost_mult * industry_mult
        cost_usd = total_days * 8 * avg_hourly_rate

        has_comparable = reg_key in _COMPARABLE_DATA
        confidence = self._calculate_confidence(reg_key, has_comparable)

        margin = 1.0 - (confidence / 100.0)
        cost_range_low = cost_usd * (1.0 - margin)
        cost_range_high = cost_usd * (1.0 + margin)

        risk_score = self._calculate_risk_score(complexity, confidence, total_days)
        breakdown = self._build_breakdown(reg_key, total_days, avg_hourly_rate, complexity)
        comparables = self._get_comparable_implementations(reg_key)

        prediction = CostPrediction(
            id=uuid4(),
            regulation=regulation,
            category=category,
            affected_files=int(total_days * 3.5),
            affected_modules=max(2, int(total_days / 10)),
            estimated_developer_days=round(total_days, 1),
            estimated_cost_usd=round(cost_usd, 2),
            confidence_pct=round(confidence, 1),
            cost_range_low=round(cost_range_low, 2),
            cost_range_high=round(cost_range_high, 2),
            risk_score=round(risk_score, 2),
            breakdown=breakdown,
            comparable_implementations=comparables,
        )

        logger.info(
            "cost_prediction_generated",
            regulation=regulation,
            org_id=org_id,
            estimated_days=prediction.estimated_developer_days,
            estimated_cost=prediction.estimated_cost_usd,
            confidence=prediction.confidence_pct,
        )
        return prediction

    async def compare_scenarios(
        self,
        regulations: list[str],
        org_id: str,
        delay_months: int = 0,
        team_size: int = 10,
        avg_hourly_rate: float = 75.0,
        industry: str = "saas",
    ) -> ScenarioComparison:
        """Compare cost scenarios for implementing regulations now vs later."""
        scenarios: list[CostPrediction] = []
        total_cost_now = 0.0

        for reg in regulations:
            prediction = await self.predict_cost(
                regulation=reg,
                org_id=org_id,
                team_size=team_size,
                avg_hourly_rate=avg_hourly_rate,
                industry=industry,
            )
            scenarios.append(prediction)
            total_cost_now += prediction.estimated_cost_usd

        # Delay premium: costs increase ~3% per month of delay
        delay_premium_pct = delay_months * 3.0
        total_cost_delayed = total_cost_now * (1.0 + delay_premium_pct / 100.0)

        if delay_months > 0:
            recommendation = (
                f"Implementing now saves ${total_cost_delayed - total_cost_now:,.0f} "
                f"({delay_premium_pct:.0f}% risk premium). "
                f"Delaying {delay_months} months increases total cost to "
                f"${total_cost_delayed:,.0f}."
            )
        else:
            recommendation = (
                f"Total estimated cost for {len(regulations)} regulation(s): "
                f"${total_cost_now:,.0f}. Implementing now minimises risk exposure."
            )

        comparison = ScenarioComparison(
            id=uuid4(),
            scenarios=scenarios,
            recommendation=recommendation,
            total_cost_now=round(total_cost_now, 2),
            total_cost_delayed=round(total_cost_delayed, 2),
            delay_risk_premium_pct=round(delay_premium_pct, 1),
        )

        logger.info(
            "scenario_comparison_generated",
            org_id=org_id,
            regulations=regulations,
            total_cost_now=comparison.total_cost_now,
            delay_months=delay_months,
        )
        return comparison

    async def calculate_roi(
        self,
        org_id: str,
        industry: str = "saas",
    ) -> ROISummary:
        """Calculate ROI of automated compliance vs manual processes."""
        industry_mult = _INDUSTRY_MULTIPLIERS.get(industry.lower(), 1.0)

        # Industry benchmarks for annual manual compliance cost
        annual_manual_cost = 450_000.0 * industry_mult
        # Automated compliance typically reduces cost by 60-75%
        annual_automated_cost = annual_manual_cost * 0.32
        annual_savings = annual_manual_cost - annual_automated_cost

        # Platform annual license cost assumption
        platform_cost = 120_000.0
        net_savings = annual_savings - platform_cost
        roi_pct = (net_savings / platform_cost) * 100.0 if platform_cost > 0 else 0.0
        payback_months = (platform_cost / (net_savings / 12.0)) if net_savings > 0 else 0.0

        summary = ROISummary(
            annual_manual_cost=round(annual_manual_cost, 2),
            annual_automated_cost=round(annual_automated_cost + platform_cost, 2),
            annual_savings=round(net_savings, 2),
            roi_pct=round(roi_pct, 1),
            payback_months=round(payback_months, 1),
            compared_to="manual",
        )

        logger.info(
            "roi_calculated",
            org_id=org_id,
            industry=industry,
            roi_pct=summary.roi_pct,
            payback_months=summary.payback_months,
        )
        return summary

    async def get_prediction_history(
        self,
        org_id: str,
        limit: int = 20,
    ) -> list[CostHistory]:
        """Get prediction accuracy history for an organization."""
        # Returns demo data; in production this would query the database
        logger.info("prediction_history_requested", org_id=org_id, limit=limit)
        return [
            CostHistory(
                id=uuid4(),
                regulation="GDPR",
                predicted_cost=400_000.0,
                actual_cost=385_000.0,
                accuracy_pct=96.2,
            ),
            CostHistory(
                id=uuid4(),
                regulation="SOC 2",
                predicted_cost=250_000.0,
                actual_cost=270_000.0,
                accuracy_pct=92.6,
            ),
            CostHistory(
                id=uuid4(),
                regulation="HIPAA",
                predicted_cost=550_000.0,
                actual_cost=530_000.0,
                accuracy_pct=96.4,
            ),
        ][:limit]

    async def record_actual_cost(
        self,
        prediction_id: str,
        actual_days: float,
        actual_cost: float,
    ) -> CostHistory:
        """Record actual implementation cost for accuracy tracking."""
        # In production, this would look up the prediction and update the DB
        accuracy_pct = min(100.0, max(0.0, 100.0 - abs(actual_cost - 400_000.0) / 4_000.0))

        record = CostHistory(
            id=uuid4(),
            regulation="recorded",
            predicted_cost=400_000.0,
            actual_cost=actual_cost,
            accuracy_pct=round(accuracy_pct, 1),
        )

        logger.info(
            "actual_cost_recorded",
            prediction_id=prediction_id,
            actual_days=actual_days,
            actual_cost=actual_cost,
            accuracy_pct=record.accuracy_pct,
        )
        return record

    async def generate_executive_report(
        self,
        org_id: str,
        regulations: list[str],
        team_size: int = 10,
        avg_hourly_rate: float = 75.0,
        industry: str = "saas",
    ) -> ExecutiveReport:
        """Generate a CFO-ready executive compliance cost report.

        Includes: total compliance portfolio cost, risk exposure from non-compliance,
        ROI projections, fine avoidance estimates, and priority recommendations.
        """
        # Fine risk estimates per regulation (annual)
        fine_risk_map: dict[str, float] = {
            "gdpr": 20_000_000.0,
            "hipaa": 1_500_000.0,
            "pci_dss": 1_200_000.0,
            "soc2": 500_000.0,
            "ccpa": 7_500.0 * 50_000,  # $7,500 per violation, assume 50K records
            "sox": 5_000_000.0,
            "eu_ai_act": 35_000_000.0,
            "dora": 10_000_000.0,
            "fedramp": 2_000_000.0,
            "iso_27001": 500_000.0,
            "nist_csf": 500_000.0,
            "lgpd": 10_000_000.0,
            "pipeda": 100_000.0,
            "glba": 1_000_000.0,
        }

        cost_by_regulation: dict[str, float] = {}
        priority_regulations: list[dict[str, Any]] = []
        total_portfolio_cost = 0.0
        total_fine_risk = 0.0

        for reg in regulations:
            prediction = await self.predict_cost(
                regulation=reg,
                org_id=org_id,
                team_size=team_size,
                avg_hourly_rate=avg_hourly_rate,
                industry=industry,
            )
            cost_by_regulation[reg] = prediction.estimated_cost_usd
            total_portfolio_cost += prediction.estimated_cost_usd

            reg_key = reg.lower().replace("-", "_").replace(" ", "_")
            fine_risk = fine_risk_map.get(reg_key, 500_000.0)
            total_fine_risk += fine_risk

            priority_regulations.append(
                {
                    "regulation": reg,
                    "cost": prediction.estimated_cost_usd,
                    "risk_score": prediction.risk_score,
                    "fine_risk": fine_risk,
                    "priority_score": round(
                        prediction.risk_score * 0.4 + min(100.0, fine_risk / 200_000.0) * 0.6,
                        1,
                    ),
                }
            )

        # Sort by priority score descending
        priority_regulations.sort(key=lambda r: r["priority_score"], reverse=True)

        # Risk exposure: fines + remediation costs (estimated at 2x implementation)
        total_risk_exposure = round(total_fine_risk + total_portfolio_cost * 2.0, 2)

        # ROI with automation (60% cost reduction)
        automated_cost = total_portfolio_cost * 0.4
        roi_with_automation = round(
            ((total_portfolio_cost - automated_cost) / automated_cost) * 100.0
            if automated_cost > 0
            else 0.0,
            1,
        )

        # Payback: automation platform cost vs savings
        industry_mult = _INDUSTRY_MULTIPLIERS.get(industry.lower(), 1.0)
        platform_cost = 120_000.0 * industry_mult
        monthly_savings = (total_portfolio_cost - automated_cost) / 12.0
        payback_period_months = round(
            platform_cost / monthly_savings if monthly_savings > 0 else 0.0, 1
        )

        # 3-year projection with 8% annual increase
        year1 = round(total_portfolio_cost, 2)
        year2 = round(year1 * 1.08, 2)
        year3 = round(year2 * 1.08, 2)
        three_year_projection = {
            "year_1": year1,
            "year_2": year2,
            "year_3": year3,
            "total": round(year1 + year2 + year3, 2),
        }

        # Prioritized recommendations
        recommendations: list[str] = []
        if priority_regulations:
            top = priority_regulations[0]["regulation"]
            recommendations.append(
                f"Prioritize {top} compliance — highest combined risk and fine exposure."
            )
        if total_fine_risk > total_portfolio_cost * 3:
            recommendations.append(
                "Non-compliance fines significantly exceed implementation costs. "
                "Immediate action recommended."
            )
        if roi_with_automation > 100.0:
            recommendations.append(
                f"Automation yields {roi_with_automation:.0f}% ROI. "
                f"Invest in compliance automation platform."
            )
        if payback_period_months > 0:
            recommendations.append(
                f"Automation investment pays back in {payback_period_months:.0f} months."
            )
        if len(regulations) > 3:
            recommendations.append(
                "Consider a phased rollout — tackle highest-priority regulations first "
                "to reduce risk exposure quickly."
            )

        report = ExecutiveReport(
            org_id=org_id,
            total_portfolio_cost=round(total_portfolio_cost, 2),
            total_risk_exposure=total_risk_exposure,
            annual_fine_risk=round(total_fine_risk, 2),
            roi_with_automation=roi_with_automation,
            payback_period_months=payback_period_months,
            priority_regulations=priority_regulations,
            cost_by_regulation=cost_by_regulation,
            three_year_projection=three_year_projection,
            recommendations=recommendations,
        )

        logger.info(
            "executive_report_generated",
            org_id=org_id,
            regulations=regulations,
            total_portfolio_cost=report.total_portfolio_cost,
            total_risk_exposure=report.total_risk_exposure,
        )
        return report

    # --- Private helpers ---

    def _get_category(self, reg_key: str) -> RegulationCategory:
        """Get the regulation category from base estimates or default."""
        if reg_key in _BASE_ESTIMATES:
            return _BASE_ESTIMATES[reg_key][2]
        return RegulationCategory.INDUSTRY_SPECIFIC

    def _estimate_complexity(self, regulation: str) -> ComplexityLevel:
        """Estimate implementation complexity for a regulation."""
        critical = {"eu_ai_act", "fedramp", "hipaa"}
        high = {"gdpr", "sox", "dora", "pci_dss"}
        medium = {"soc2", "iso_27001", "ccpa", "nist_csf", "glba"}

        reg = regulation.lower().replace("-", "_").replace(" ", "_")
        if reg in critical:
            return ComplexityLevel.CRITICAL
        if reg in high:
            return ComplexityLevel.HIGH
        if reg in medium:
            return ComplexityLevel.MEDIUM
        return ComplexityLevel.LOW

    def _get_base_estimates(
        self,
        regulation: str,
        category: RegulationCategory,
    ) -> tuple[float, float]:
        """Get base developer-days and cost multiplier for a regulation."""
        reg = regulation.lower().replace("-", "_").replace(" ", "_")
        if reg in _BASE_ESTIMATES:
            days, mult, _ = _BASE_ESTIMATES[reg]
            return days, mult

        # Fallback estimates by category
        fallbacks: dict[RegulationCategory, tuple[float, float]] = {
            RegulationCategory.DATA_PRIVACY: (40.0, 0.9),
            RegulationCategory.AI_GOVERNANCE: (70.0, 1.3),
            RegulationCategory.FINANCIAL: (55.0, 1.1),
            RegulationCategory.HEALTHCARE: (65.0, 1.2),
            RegulationCategory.SECURITY: (45.0, 1.0),
            RegulationCategory.INDUSTRY_SPECIFIC: (50.0, 1.0),
        }
        return fallbacks.get(category, (50.0, 1.0))

    def _apply_team_adjustments(self, base_days: float, team_size: int) -> float:
        """Adjust estimated days based on team size (Brooks's law)."""
        if team_size <= 1:
            return base_days
        # Larger teams have communication overhead; diminishing returns
        efficiency = 1.0 / (1.0 + 0.05 * math.log2(max(team_size, 2)))
        return base_days * (1.0 + (1.0 - efficiency))

    def _calculate_confidence(self, regulation: str, has_comparable_data: bool) -> float:
        """Calculate prediction confidence percentage."""
        reg = regulation.lower().replace("-", "_").replace(" ", "_")
        base_confidence = 70.0 if reg in _BASE_ESTIMATES else 45.0
        if has_comparable_data:
            base_confidence += 15.0
        return min(95.0, base_confidence)

    def _calculate_risk_score(
        self,
        complexity: ComplexityLevel,
        confidence: float,
        total_days: float,
    ) -> float:
        """Calculate a 0-100 risk score for the implementation."""
        complexity_weights = {
            ComplexityLevel.LOW: 0.2,
            ComplexityLevel.MEDIUM: 0.4,
            ComplexityLevel.HIGH: 0.7,
            ComplexityLevel.CRITICAL: 0.9,
        }
        complexity_factor = complexity_weights.get(complexity, 0.5)
        confidence_factor = 1.0 - (confidence / 100.0)
        duration_factor = min(1.0, total_days / 120.0)

        return min(100.0, (complexity_factor * 40 + confidence_factor * 30 + duration_factor * 30))

    def _build_breakdown(
        self,
        regulation: str,
        total_days: float,
        hourly_rate: float,
        complexity: ComplexityLevel,
    ) -> list[CostBreakdownItem]:
        """Build a cost breakdown by implementation phase."""
        phases = [
            ("Gap Analysis", "Assess current state vs requirements", 0.15),
            ("Architecture & Design", "Design compliant architecture", 0.10),
            ("Implementation", "Core development work", 0.40),
            ("Testing & Validation", "Compliance testing and QA", 0.15),
            ("Documentation", "Policy docs and evidence artifacts", 0.10),
            ("Training & Rollout", "Team training and deployment", 0.10),
        ]
        items = []
        for category, description, pct in phases:
            days = round(total_days * pct, 1)
            cost = round(days * 8 * hourly_rate, 2)
            items.append(
                CostBreakdownItem(
                    category=category,
                    description=description,
                    developer_days=days,
                    cost_usd=cost,
                    complexity=complexity,
                )
            )
        return items

    def _get_comparable_implementations(self, regulation: str) -> list[ComparableImpl]:
        """Get comparable past implementations for a regulation."""
        reg = regulation.lower().replace("-", "_").replace(" ", "_")
        return _COMPARABLE_DATA.get(reg, [])
