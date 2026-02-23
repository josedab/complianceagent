"""Scenario planner service for compliance planning and impact analysis."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.scenario_planner.models import (
    ComplianceRequirementSet,
    PlannerStats,
    PlanningReport,
    PlanningScenario,
    RegionGroup,
    ScenarioType,
)


logger = structlog.get_logger()

# Framework determination rules
_REGION_FRAMEWORKS: dict[str, list[str]] = {
    "eu": ["GDPR", "EU AI Act"],
    "us": ["SOC 2", "CCPA"],
    "apac": ["PDPA", "APPI"],
    "latam": ["LGPD"],
    "mena": ["PDPL"],
    "global": ["ISO 27001"],
}

# Effort estimates per framework (hours)
_FRAMEWORK_EFFORT: dict[str, float] = {
    "GDPR": 320.0,
    "HIPAA": 280.0,
    "PCI DSS": 240.0,
    "SOC 2": 200.0,
    "ISO 27001": 360.0,
    "EU AI Act": 180.0,
    "CCPA": 120.0,
    "PDPA": 160.0,
    "APPI": 140.0,
    "LGPD": 200.0,
    "PDPL": 150.0,
}

# Cost per hour estimate
_COST_PER_HOUR = 150.0


class ScenarioPlannerService:
    """Service for compliance scenario planning and impact analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._reports: dict[UUID, PlanningReport] = {}
        self._templates = self._build_templates()

    def _build_templates(self) -> list[dict]:
        """Build scenario templates."""
        return [
            {
                "title": "EU Market Expansion",
                "scenario_type": ScenarioType.market_expansion,
                "description": "Expand operations into the European Union market",
                "target_regions": [RegionGroup.eu],
                "data_types": ["personal_data", "behavioral_data"],
            },
            {
                "title": "Healthcare Product Launch",
                "scenario_type": ScenarioType.product_launch,
                "description": "Launch a healthcare product handling patient data",
                "target_regions": [RegionGroup.us],
                "data_types": ["health_data", "personal_data"],
                "health_data": True,
            },
            {
                "title": "Global Payment Processing",
                "scenario_type": ScenarioType.data_processing,
                "description": "Process payment card data across multiple regions",
                "target_regions": [RegionGroup.global_],
                "data_types": ["payment_data", "personal_data"],
                "payment_data": True,
            },
        ]

    def _determine_frameworks(
        self,
        target_regions: list[RegionGroup],
        ai_features: bool,
        health_data: bool,
        payment_data: bool,
    ) -> list[str]:
        """Determine applicable frameworks from region and data type combinations."""
        frameworks: set[str] = set()
        for region in target_regions:
            region_key = region.value.rstrip("_")
            if region_key in _REGION_FRAMEWORKS:
                frameworks.update(_REGION_FRAMEWORKS[region_key])
        if not ai_features:
            frameworks.discard("EU AI Act")
        if health_data:
            frameworks.add("HIPAA")
        if payment_data:
            frameworks.add("PCI DSS")
        if ai_features and "EU AI Act" not in frameworks:
            frameworks.add("EU AI Act")
        return sorted(frameworks)

    def _estimate_effort(self, frameworks: list[str]) -> tuple[float, float, int]:
        """Estimate effort hours, cost, and timeline for frameworks."""
        total_hours = sum(_FRAMEWORK_EFFORT.get(f, 200.0) for f in frameworks)
        total_cost = total_hours * _COST_PER_HOUR
        # Assume 2 FTEs working, ~160 hours/month each
        timeline = max(1, int(total_hours / 320) + 1)
        return total_hours, total_cost, timeline

    def _generate_priority_actions(self, frameworks: list[str]) -> list[dict]:
        """Generate priority actions based on applicable frameworks."""
        actions = []
        action_map = {
            "GDPR": {"action": "Appoint a Data Protection Officer", "priority": "high", "category": "governance"},
            "HIPAA": {"action": "Conduct PHI risk assessment", "priority": "critical", "category": "risk"},
            "PCI DSS": {"action": "Implement network segmentation for CDE", "priority": "critical", "category": "technical"},
            "SOC 2": {"action": "Document security policies and procedures", "priority": "high", "category": "documentation"},
            "ISO 27001": {"action": "Establish ISMS framework", "priority": "high", "category": "governance"},
            "EU AI Act": {"action": "Classify AI systems by risk level", "priority": "high", "category": "assessment"},
        }
        for framework in frameworks:
            if framework in action_map:
                actions.append(action_map[framework])
        return actions

    def _assess_risk(self, frameworks: list[str], scenario: PlanningScenario) -> str:
        """Generate a risk assessment for the scenario."""
        risk_level = "Low"
        if len(frameworks) >= 4:
            risk_level = "High"
        elif len(frameworks) >= 2:
            risk_level = "Medium"
        if scenario.health_data or scenario.payment_data:
            risk_level = "High"
        return (
            f"Risk Level: {risk_level}. "
            f"This scenario involves {len(frameworks)} regulatory framework(s) "
            f"across {len(scenario.target_regions)} region(s). "
            f"{'Sensitive data types (health/payment) increase regulatory scrutiny. ' if scenario.health_data or scenario.payment_data else ''}"
            f"Recommend engaging legal counsel for cross-border compliance requirements."
        )

    def _generate_recommendations(self, frameworks: list[str], scenario: PlanningScenario) -> list[str]:
        """Generate recommendations for the scenario."""
        recommendations = [
            f"Conduct a gap analysis against {', '.join(frameworks)}",
            "Establish a compliance project timeline with milestones",
            "Assign dedicated compliance ownership for each framework",
        ]
        if len(scenario.target_regions) > 1:
            recommendations.append("Implement a unified compliance management platform for cross-region coordination")
        if scenario.ai_features:
            recommendations.append("Document AI model risk assessments and implement human oversight mechanisms")
        if scenario.health_data:
            recommendations.append("Implement BAA agreements with all vendors processing PHI")
        if scenario.payment_data:
            recommendations.append("Engage a QSA for PCI DSS assessment and certification")
        return recommendations

    async def plan_scenario(
        self,
        title: str,
        scenario_type: ScenarioType,
        description: str,
        target_regions: list[RegionGroup],
        data_types: list[str],
        ai_features: bool = False,
        health_data: bool = False,
        payment_data: bool = False,
    ) -> PlanningReport:
        """Plan a compliance scenario and generate a report."""
        scenario = PlanningScenario(
            id=uuid4(),
            title=title,
            scenario_type=scenario_type,
            description=description,
            target_regions=target_regions,
            data_types=data_types,
            ai_features=ai_features,
            health_data=health_data,
            payment_data=payment_data,
        )

        frameworks = self._determine_frameworks(target_regions, ai_features, health_data, payment_data)
        total_hours, total_cost, timeline = self._estimate_effort(frameworks)
        priority_actions = self._generate_priority_actions(frameworks)

        requirements = ComplianceRequirementSet(
            scenario_id=scenario.id,
            applicable_frameworks=frameworks,
            total_requirements=len(frameworks) * 25,
            estimated_effort_hours=total_hours,
            estimated_cost_usd=total_cost,
            priority_actions=priority_actions,
            timeline_months=timeline,
        )

        report = PlanningReport(
            id=uuid4(),
            scenario=scenario,
            requirements=requirements,
            risk_assessment=self._assess_risk(frameworks, scenario),
            recommendations=self._generate_recommendations(frameworks, scenario),
            generated_at=datetime.now(UTC),
        )

        self._reports[report.id] = report
        logger.info(
            "Scenario planned",
            title=title,
            frameworks=len(frameworks),
            effort_hours=total_hours,
        )
        return report

    async def list_scenarios(self) -> list[PlanningReport]:
        """List all planning reports."""
        return list(self._reports.values())

    async def get_stats(self) -> PlannerStats:
        """Get aggregate planner statistics."""
        reports = list(self._reports.values())
        by_type: dict[str, int] = {}
        by_region: dict[str, int] = {}
        total_frameworks = 0

        for report in reports:
            type_key = report.scenario.scenario_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            for region in report.scenario.target_regions:
                by_region[region.value] = by_region.get(region.value, 0) + 1
            total_frameworks += len(report.requirements.applicable_frameworks)

        avg_frameworks = total_frameworks / len(reports) if reports else 0.0
        return PlannerStats(
            total_scenarios=len(reports),
            by_type=by_type,
            by_region=by_region,
            avg_frameworks_per_scenario=round(avg_frameworks, 2),
        )
