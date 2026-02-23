"""ESG Sustainability Service."""

from datetime import UTC, datetime
from uuid import UUID  # noqa: TC003

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.esg_sustainability.models import (
    CarbonFootprint,
    ESGCategory,
    ESGFramework,
    ESGMetric,
    ESGReport,
    ESGStats,
)


logger = structlog.get_logger()


class ESGSustainabilityService:
    """ESG metrics tracking, carbon footprint analysis, and reporting."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._metrics: dict[UUID, ESGMetric] = {}
        self._reports: dict[UUID, ESGReport] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed ESG metrics across environmental, social, and governance categories."""
        metrics = [
            # Environmental metrics
            ESGMetric(
                category=ESGCategory.ENVIRONMENTAL,
                framework=ESGFramework.TCFD,
                metric_name="Scope 1 GHG Emissions",
                value=1250.0,
                unit="tCO2e",
                period="2024-Q4",
                target=1100.0,
                on_track=False,
            ),
            ESGMetric(
                category=ESGCategory.ENVIRONMENTAL,
                framework=ESGFramework.TCFD,
                metric_name="Scope 2 GHG Emissions",
                value=3400.0,
                unit="tCO2e",
                period="2024-Q4",
                target=3000.0,
                on_track=False,
            ),
            ESGMetric(
                category=ESGCategory.ENVIRONMENTAL,
                framework=ESGFramework.GRI,
                metric_name="Renewable Energy Percentage",
                value=62.0,
                unit="%",
                period="2024-Q4",
                target=75.0,
                on_track=True,
            ),
            ESGMetric(
                category=ESGCategory.ENVIRONMENTAL,
                framework=ESGFramework.CSRD,
                metric_name="Water Consumption",
                value=45000.0,
                unit="m³",
                period="2024-Q4",
                target=40000.0,
                on_track=False,
            ),
            # Social metrics
            ESGMetric(
                category=ESGCategory.SOCIAL,
                framework=ESGFramework.GRI,
                metric_name="Employee Diversity Index",
                value=0.72,
                unit="index",
                period="2024-Q4",
                target=0.80,
                on_track=True,
            ),
            ESGMetric(
                category=ESGCategory.SOCIAL,
                framework=ESGFramework.SDG,
                metric_name="Training Hours per Employee",
                value=32.5,
                unit="hours",
                period="2024-Q4",
                target=40.0,
                on_track=True,
            ),
            ESGMetric(
                category=ESGCategory.SOCIAL,
                framework=ESGFramework.CSRD,
                metric_name="Gender Pay Gap",
                value=4.2,
                unit="%",
                period="2024-Q4",
                target=3.0,
                on_track=True,
            ),
            # Governance metrics
            ESGMetric(
                category=ESGCategory.GOVERNANCE,
                framework=ESGFramework.GRI,
                metric_name="Board Independence Ratio",
                value=0.75,
                unit="ratio",
                period="2024-Q4",
                target=0.80,
                on_track=True,
            ),
            ESGMetric(
                category=ESGCategory.GOVERNANCE,
                framework=ESGFramework.SEC_CLIMATE,
                metric_name="Climate Risk Disclosure Score",
                value=85.0,
                unit="score",
                period="2024-Q4",
                target=90.0,
                on_track=True,
            ),
            ESGMetric(
                category=ESGCategory.GOVERNANCE,
                framework=ESGFramework.CSRD,
                metric_name="Anti-Corruption Training Completion",
                value=94.0,
                unit="%",
                period="2024-Q4",
                target=100.0,
                on_track=True,
            ),
        ]

        for metric in metrics:
            self._metrics[metric.id] = metric

        logger.info("ESG sustainability seeded", metric_count=len(self._metrics))

    async def record_metric(
        self,
        category: str,
        framework: str,
        metric_name: str,
        value: float,
        unit: str,
        period: str,
        target: float | None = None,
    ) -> ESGMetric:
        """Record a new ESG metric."""
        on_track = True
        if target is not None:
            if (unit == "%" and "gap" in metric_name.lower()) or unit in ("tCO2e", "m³"):
                on_track = value <= target
            else:
                on_track = value >= target

        metric = ESGMetric(
            category=ESGCategory(category),
            framework=ESGFramework(framework),
            metric_name=metric_name,
            value=value,
            unit=unit,
            period=period,
            target=target,
            on_track=on_track,
        )
        self._metrics[metric.id] = metric

        logger.info("ESG metric recorded", metric_name=metric_name, value=value, unit=unit)
        return metric

    async def get_carbon_footprint(self, period: str) -> CarbonFootprint:
        """Get carbon footprint data with realistic Scope 1/2/3 breakdown."""
        scope_1 = 1250.0
        scope_2 = 3400.0
        scope_3 = 12800.0
        total = scope_1 + scope_2 + scope_3

        return CarbonFootprint(
            total_emissions_tons=total,
            by_scope={
                "scope_1": scope_1,
                "scope_2": scope_2,
                "scope_3": scope_3,
            },
            by_source={
                "data_centers": 8500.0,
                "office_operations": 1250.0,
                "employee_commuting": 2100.0,
                "business_travel": 1800.0,
                "supply_chain": 3200.0,
                "cloud_infrastructure": 600.0,
            },
            reduction_target_pct=30.0,
            reduction_achieved_pct=12.5,
            reporting_period=period,
        )

    async def generate_report(
        self,
        title: str,
        frameworks: list[str],
    ) -> ESGReport:
        """Generate an ESG report for specified frameworks."""
        fw_enums = [ESGFramework(f) for f in frameworks]

        matching_metrics = [
            m for m in self._metrics.values()
            if m.framework in fw_enums
        ]

        carbon = await self.get_carbon_footprint("2024-Q4")

        on_track_count = sum(1 for m in matching_metrics if m.on_track)

        highlights = [
            f"{on_track_count}/{len(matching_metrics)} metrics on track to meet targets",
            f"Total carbon footprint: {carbon.total_emissions_tons:,.0f} tCO2e",
            f"Reduction achieved: {carbon.reduction_achieved_pct}% of {carbon.reduction_target_pct}% target",
        ]

        recommendations = [
            "Accelerate renewable energy transition to meet 75% target",
            "Implement Scope 3 supply chain engagement programme",
            "Enhance water recycling infrastructure at primary facilities",
            "Expand diversity and inclusion programmes to reach 0.80 index target",
            "Increase climate risk scenario analysis coverage",
        ]

        report = ESGReport(
            title=title,
            frameworks=fw_enums,
            metrics=matching_metrics,
            carbon_footprint=carbon,
            highlights=highlights,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )
        self._reports[report.id] = report

        logger.info(
            "ESG report generated",
            report_id=str(report.id),
            title=title,
            metric_count=len(matching_metrics),
        )
        return report

    async def list_metrics(
        self,
        category: ESGCategory | None = None,
        framework: ESGFramework | None = None,
    ) -> list[ESGMetric]:
        """List ESG metrics with optional filters."""
        metrics = list(self._metrics.values())

        if category is not None:
            metrics = [m for m in metrics if m.category == category]
        if framework is not None:
            metrics = [m for m in metrics if m.framework == framework]

        return metrics

    async def get_stats(self) -> ESGStats:
        """Get ESG sustainability statistics."""
        metrics = list(self._metrics.values())

        by_category: dict[str, int] = {}
        for m in metrics:
            by_category[m.category.value] = by_category.get(m.category.value, 0) + 1

        frameworks_tracked = len({m.framework for m in metrics})

        return ESGStats(
            total_metrics=len(metrics),
            frameworks_tracked=frameworks_tracked,
            by_category=by_category,
            carbon_tracked=True,
            reports_generated=len(self._reports),
        )
