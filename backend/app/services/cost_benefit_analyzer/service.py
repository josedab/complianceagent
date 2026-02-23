"""Compliance Cost-Benefit Analyzer Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cost_benefit_analyzer.models import (
    ComplianceInvestment,
    CostBenefitStats,
    CostBreakdown,
    CostCategory,
    ExecutiveReport,
    InvestmentStatus,
    ROICalculation,
)


logger = structlog.get_logger()

# Fine exposure by framework (estimates)
_FINE_EXPOSURE: dict[str, float] = {
    "GDPR": 20_000_000,
    "HIPAA": 1_500_000,
    "PCI-DSS": 500_000,
    "SOC2": 250_000,
    "CCPA": 7_500,
    "EU AI Act": 35_000_000,
    "SOX": 5_000_000,
    "NIS2": 10_000_000,
}


class CostBenefitAnalyzerService:
    """Compliance investment ROI analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._investments: list[ComplianceInvestment] = []

    async def add_investment(
        self,
        name: str,
        framework: str,
        category: str = "engineering",
        cost_usd: float = 0.0,
        engineering_hours: float = 0.0,
        score_impact: float = 0.0,
    ) -> ComplianceInvestment:
        risk_reduction = self._estimate_risk_reduction(framework, score_impact)
        inv = ComplianceInvestment(
            name=name,
            framework=framework,
            category=CostCategory(category),
            cost_usd=cost_usd,
            engineering_hours=engineering_hours,
            status=InvestmentStatus.PLANNED,
            score_impact=score_impact,
            risk_reduction_usd=risk_reduction,
            started_at=datetime.now(UTC),
        )
        self._investments.append(inv)
        logger.info("Investment recorded", name=name, cost=cost_usd, framework=framework)
        return inv

    def _estimate_risk_reduction(self, framework: str, score_impact: float) -> float:
        max_fine = _FINE_EXPOSURE.get(framework, 100_000)
        # Each point of compliance improvement reduces risk proportionally
        return round(max_fine * (score_impact / 100) * 0.1, 2)

    async def calculate_roi(self, investment_id: UUID) -> ROICalculation | None:
        inv = next((i for i in self._investments if i.id == investment_id), None)
        if not inv:
            return None
        net = inv.risk_reduction_usd - inv.cost_usd
        roi = round((net / inv.cost_usd) * 100, 1) if inv.cost_usd > 0 else 0
        payback = round(inv.cost_usd / (inv.risk_reduction_usd / 12), 1) if inv.risk_reduction_usd > 0 else 999
        return ROICalculation(
            investment_id=inv.id,
            investment_name=inv.name,
            total_cost=inv.cost_usd,
            risk_reduction=inv.risk_reduction_usd,
            roi_pct=roi,
            payback_months=payback,
            net_benefit=round(net, 2),
            score_improvement=inv.score_impact,
        )

    def get_cost_breakdown(self, framework: str | None = None) -> list[CostBreakdown]:
        fw_groups: dict[str, list[ComplianceInvestment]] = {}
        for inv in self._investments:
            if framework and inv.framework != framework:
                continue
            fw_groups.setdefault(inv.framework, []).append(inv)

        breakdowns = []
        for fw, investments in fw_groups.items():
            by_cat: dict[str, float] = {}
            total = 0.0
            hours = 0.0
            score_pts = 0.0
            for inv in investments:
                by_cat[inv.category.value] = by_cat.get(inv.category.value, 0) + inv.cost_usd
                total += inv.cost_usd
                hours += inv.engineering_hours
                score_pts += inv.score_impact
            cpp = round(total / score_pts, 2) if score_pts > 0 else 0
            breakdowns.append(CostBreakdown(framework=fw, total_cost=total, by_category=by_cat, engineering_hours=hours, cost_per_point=cpp))
        return breakdowns

    async def generate_executive_report(self, period: str = "Q1 2026") -> ExecutiveReport:
        total_inv = sum(i.cost_usd for i in self._investments)
        total_risk = sum(i.risk_reduction_usd for i in self._investments)
        overall_roi = round(((total_risk - total_inv) / total_inv) * 100, 1) if total_inv > 0 else 0

        top = sorted(self._investments, key=lambda i: i.risk_reduction_usd, reverse=True)[:5]
        top_calcs = []
        for inv in top:
            roi = await self.calculate_roi(inv.id)
            if roi:
                top_calcs.append(roi)

        breakdowns = self.get_cost_breakdown()
        highlights = []
        if total_risk > total_inv:
            highlights.append(f"Net positive ROI: ${total_risk - total_inv:,.0f} in risk reduction exceeds ${total_inv:,.0f} investment")
        highlights.append(f"{len(self._investments)} compliance investments tracked across {len({i.framework for i in self._investments})} frameworks")

        recommendations = []
        if total_inv == 0:
            recommendations.append("Start tracking compliance investments to demonstrate ROI")
        else:
            low_roi = [i for i in self._investments if i.risk_reduction_usd < i.cost_usd]
            if low_roi:
                recommendations.append(f"Review {len(low_roi)} investments with negative ROI")
            recommendations.append("Consider increasing investment in highest-fine-exposure frameworks")

        report = ExecutiveReport(
            period=period,
            total_investment=total_inv,
            total_risk_reduction=total_risk,
            overall_roi_pct=overall_roi,
            framework_breakdown=breakdowns,
            top_investments=top_calcs,
            highlights=highlights,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )
        logger.info("Executive report generated", period=period, roi=overall_roi)
        return report

    def list_investments(self, framework: str | None = None, limit: int = 50) -> list[ComplianceInvestment]:
        results = list(self._investments)
        if framework:
            results = [i for i in results if i.framework == framework]
        return results[:limit]

    def get_stats(self) -> CostBenefitStats:
        by_fw: dict[str, float] = {}
        by_cat: dict[str, float] = {}
        total_spend = 0.0
        total_risk = 0.0
        rois = []
        for inv in self._investments:
            by_fw[inv.framework] = by_fw.get(inv.framework, 0) + inv.cost_usd
            by_cat[inv.category.value] = by_cat.get(inv.category.value, 0) + inv.cost_usd
            total_spend += inv.cost_usd
            total_risk += inv.risk_reduction_usd
            if inv.cost_usd > 0:
                rois.append((inv.risk_reduction_usd - inv.cost_usd) / inv.cost_usd * 100)
        return CostBenefitStats(
            total_investments=len(self._investments),
            total_spend=total_spend,
            total_risk_reduction=total_risk,
            avg_roi_pct=round(sum(rois) / len(rois), 1) if rois else 0.0,
            by_framework=by_fw,
            by_category=by_cat,
        )
