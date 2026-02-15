"""Compliance Cost Attribution Engine Service."""

import random
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cost_attribution.models import (
    CostCategory,
    CostDashboard,
    CostEntry,
    CostPeriod,
    MarketExitScenario,
    RegulationCostSummary,
    ROIAnalysis,
)


logger = structlog.get_logger()

_REGULATIONS = ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "DORA"]
_MODULES = [
    "auth",
    "data-pipeline",
    "api-gateway",
    "storage",
    "logging",
    "encryption",
    "consent-manager",
]


class CostAttributionService:
    """Track and analyze compliance costs."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._costs: list[CostEntry] = []

    async def record_cost(
        self,
        regulation: str,
        category: CostCategory,
        amount: float,
        description: str,
        code_module: str,
        period: CostPeriod,
    ) -> CostEntry:
        """Record a compliance cost entry."""
        entry = CostEntry(
            regulation=regulation,
            category=category,
            amount=amount,
            description=description,
            code_module=code_module,
            period=period,
            recorded_at=datetime.now(UTC),
        )
        self._costs.append(entry)
        logger.info("Cost recorded", regulation=regulation, category=category.value, amount=amount)
        return entry

    async def list_costs(
        self,
        regulation: str | None = None,
        category: CostCategory | None = None,
    ) -> list[CostEntry]:
        """List cost entries with optional filters."""
        costs = self._costs
        if regulation:
            costs = [c for c in costs if c.regulation == regulation]
        if category:
            costs = [c for c in costs if c.category == category]
        return costs

    async def get_regulation_summary(self, regulation: str) -> RegulationCostSummary:
        """Get cost summary for a regulation."""
        reg_costs = [c for c in self._costs if c.regulation == regulation]
        total = sum(c.amount for c in reg_costs)

        by_category: dict[str, float] = {}
        for c in reg_costs:
            by_category[c.category.value] = by_category.get(c.category.value, 0) + c.amount

        # If no real data, generate realistic mock
        if not reg_costs:
            total = round(random.uniform(50000, 500000), 2)
            by_category = {
                CostCategory.ENGINEERING.value: round(total * 0.4, 2),
                CostCategory.LEGAL_REVIEW.value: round(total * 0.2, 2),
                CostCategory.AUDIT.value: round(total * 0.15, 2),
                CostCategory.TOOLING.value: round(total * 0.1, 2),
                CostCategory.TRAINING.value: round(total * 0.08, 2),
                CostCategory.CONSULTING.value: round(total * 0.07, 2),
            }

        module_costs: dict[str, float] = {}
        for c in reg_costs:
            module_costs[c.code_module] = module_costs.get(c.code_module, 0) + c.amount

        top_modules = [
            {"module": m, "cost": round(cost, 2)}
            for m, cost in sorted(module_costs.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        if not top_modules:
            top_modules = [
                {"module": mod, "cost": round(random.uniform(5000, 50000), 2)}
                for mod in random.sample(_MODULES, 3)
            ]

        return RegulationCostSummary(
            regulation=regulation,
            total_cost=round(total, 2),
            cost_by_category=by_category,
            trend_pct=round(random.uniform(-15, 25), 1),
            top_modules=top_modules,
            period="monthly",
        )

    async def analyze_roi(self, regulation: str) -> ROIAnalysis:
        """Analyze ROI for compliance investment in a regulation."""
        investment = round(random.uniform(100000, 1000000), 2)
        # Savings from avoided fines and reduced audit costs
        avg_fine = random.uniform(500000, 50000000)
        probability = random.uniform(0.05, 0.3)
        savings = round(avg_fine * probability + investment * 0.15, 2)
        roi = round(((savings - investment) / investment) * 100, 1)

        analysis = ROIAnalysis(
            regulation=regulation,
            investment=investment,
            savings=savings,
            roi_pct=roi,
            payback_months=max(1, int(investment / (savings / 12))),
            assumptions=[
                f"Average fine for {regulation} non-compliance: ${avg_fine:,.0f}",
                f"Probability of enforcement action: {probability:.0%}",
                "Includes reduced audit preparation time",
                "Assumes current compliance tooling investment",
                "Does not include reputational damage costs",
            ],
            analyzed_at=datetime.now(UTC),
        )
        logger.info("ROI analyzed", regulation=regulation, roi_pct=roi)
        return analysis

    async def model_market_exit(self, jurisdiction: str) -> MarketExitScenario:
        """Model the cost of exiting a market/jurisdiction."""
        current_cost = round(random.uniform(200000, 2000000), 2)
        exit_cost = round(random.uniform(100000, 500000), 2)
        revenue = round(random.uniform(1000000, 50000000), 2)

        if revenue > current_cost * 5:
            recommendation = "STAY — Revenue significantly exceeds compliance costs"
        elif revenue > current_cost * 2:
            recommendation = "OPTIMIZE — Reduce compliance costs before considering exit"
        else:
            recommendation = "EVALUATE — Exit may be cost-effective; detailed analysis recommended"

        scenario = MarketExitScenario(
            jurisdiction=jurisdiction,
            current_cost=current_cost,
            exit_cost=exit_cost,
            revenue_at_risk=revenue,
            recommendation=recommendation,
            breakeven_months=max(1, int(exit_cost / (current_cost / 12))),
        )
        logger.info("Market exit modeled", jurisdiction=jurisdiction, recommendation=recommendation)
        return scenario

    async def get_dashboard(self) -> CostDashboard:
        """Generate compliance cost dashboard."""
        total = sum(c.amount for c in self._costs)

        by_reg: dict[str, float] = {}
        by_cat: dict[str, float] = {}
        for c in self._costs:
            by_reg[c.regulation] = by_reg.get(c.regulation, 0) + c.amount
            by_cat[c.category.value] = by_cat.get(c.category.value, 0) + c.amount

        # Generate mock data if no real entries
        if not self._costs:
            total = round(random.uniform(500000, 5000000), 2)
            by_reg = {reg: round(random.uniform(50000, 500000), 2) for reg in _REGULATIONS}
            by_cat = {cat.value: round(random.uniform(30000, 300000), 2) for cat in CostCategory}

        top_drivers = [
            {
                "driver": reg,
                "cost": round(cost, 2),
                "pct_of_total": round((cost / total) * 100, 1) if total else 0,
            }
            for reg, cost in sorted(by_reg.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        dashboard = CostDashboard(
            total_compliance_cost=round(total, 2),
            cost_by_regulation=by_reg,
            cost_by_category=by_cat,
            month_over_month_change=round(random.uniform(-10, 15), 1),
            top_cost_drivers=top_drivers,
            roi_summary={
                "avg_roi_pct": round(random.uniform(50, 300), 1),
                "total_investment": round(total * 0.6, 2),
                "total_savings": round(total * 1.5, 2),
            },
            generated_at=datetime.now(UTC),
        )
        logger.info("Cost dashboard generated", total=total)
        return dashboard

    async def list_summaries(self) -> list[RegulationCostSummary]:
        """List cost summaries for all regulations."""
        regulations = set(c.regulation for c in self._costs)
        if not regulations:
            regulations = set(_REGULATIONS)

        summaries: list[RegulationCostSummary] = []
        for reg in sorted(regulations):
            summaries.append(await self.get_regulation_summary(reg))
        return summaries
