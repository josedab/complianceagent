"""Regulatory Change Simulator Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reg_simulator.models import (
    PreparationMilestone,
    PreparationRoadmap,
    SimulationImpact,
    SimulationScenario,
)


logger = structlog.get_logger()

_BUILTIN_SCENARIOS = [
    SimulationScenario(
        regulation="GDPR",
        change_description="New requirements for automated decision-making transparency under Article 22",
        affected_articles=["Article 22", "Article 13", "Article 14"],
        severity="high",
    ),
    SimulationScenario(
        regulation="HIPAA",
        change_description="Expanded definition of PHI to include genomic data and wearable device data",
        affected_articles=["164.501", "164.502", "164.514"],
        severity="high",
    ),
    SimulationScenario(
        regulation="EU AI Act",
        change_description="High-risk AI system classification expanded to include code review automation",
        affected_articles=["Article 6", "Article 9", "Annex III"],
        severity="critical",
    ),
    SimulationScenario(
        regulation="PCI-DSS",
        change_description="PCI DSS v4.1 requires multi-factor authentication for all access to cardholder data",
        affected_articles=["Req 8.4", "Req 8.5", "Req 8.6"],
        severity="medium",
    ),
    SimulationScenario(
        regulation="NIS2",
        change_description="Mandatory incident reporting within 24 hours for essential and important entities",
        affected_articles=["Article 23", "Article 21", "Article 32"],
        severity="high",
    ),
]


class RegulatorySimulatorService:
    """Service for simulating regulatory changes and their impact."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._scenarios: list[SimulationScenario] = list(_BUILTIN_SCENARIOS)
        self._results: dict[str, SimulationImpact] = {}
        self._roadmaps: dict[str, PreparationRoadmap] = {}

    async def create_scenario(self, scenario: SimulationScenario) -> SimulationScenario:
        """Create a new regulatory change scenario."""
        self._scenarios.append(scenario)
        logger.info("Scenario created", regulation=scenario.regulation, severity=scenario.severity)
        return scenario

    async def run_simulation(self, scenario_id: UUID) -> SimulationImpact:
        """Run a simulation for a given scenario."""
        scenario = next((s for s in self._scenarios if s.id == scenario_id), None)
        if not scenario:
            return SimulationImpact(scenario_id=scenario_id)

        severity_multipliers = {"low": 1.0, "medium": 2.0, "high": 3.5, "critical": 5.0}
        multiplier = severity_multipliers.get(scenario.severity, 2.0)
        article_count = len(scenario.affected_articles)

        impact = SimulationImpact(
            scenario_id=scenario_id,
            affected_repos=[
                "org/auth-service",
                "org/payment-api",
                "org/data-pipeline",
                "org/user-portal",
            ],
            affected_files_count=int(article_count * multiplier * 12),
            remediation_hours=round(article_count * multiplier * 40.0, 1),
            risk_score=round(min(100.0, multiplier * 20.0), 1),
            affected_frameworks=[scenario.regulation],
        )
        self._results[str(scenario_id)] = impact

        logger.info(
            "Simulation completed",
            regulation=scenario.regulation,
            risk_score=impact.risk_score,
            remediation_hours=impact.remediation_hours,
        )
        return impact

    async def get_simulation_result(self, scenario_id: UUID) -> SimulationImpact | None:
        """Get a previously computed simulation result."""
        return self._results.get(str(scenario_id))

    async def generate_roadmap(self, scenario_id: UUID) -> PreparationRoadmap:
        """Generate a preparation roadmap for a scenario."""
        scenario = next((s for s in self._scenarios if s.id == scenario_id), None)
        regulation = scenario.regulation if scenario else "Unknown"

        milestones = [
            PreparationMilestone(
                title="Impact Assessment",
                description=f"Assess {regulation} change impact on codebase",
                deadline_weeks=2,
                team="compliance",
                status="pending",
            ),
            PreparationMilestone(
                title="Gap Analysis",
                description=f"Identify gaps against new {regulation} requirements",
                deadline_weeks=4,
                team="security",
                status="pending",
            ),
            PreparationMilestone(
                title="Remediation Planning",
                description="Create detailed remediation plan with resource allocation",
                deadline_weeks=6,
                team="engineering",
                status="pending",
            ),
            PreparationMilestone(
                title="Implementation",
                description=f"Implement changes to meet new {regulation} requirements",
                deadline_weeks=12,
                team="engineering",
                status="pending",
            ),
            PreparationMilestone(
                title="Testing & Validation",
                description="Validate compliance through testing and evidence collection",
                deadline_weeks=14,
                team="qa",
                status="pending",
            ),
            PreparationMilestone(
                title="Audit Readiness",
                description="Prepare documentation and evidence for audit",
                deadline_weeks=16,
                team="compliance",
                status="pending",
            ),
        ]

        roadmap = PreparationRoadmap(
            scenario_id=scenario_id,
            milestones=milestones,
            total_effort_hours=sum(m.deadline_weeks * 8.0 for m in milestones),
            recommended_start=datetime.now(UTC),
        )
        self._roadmaps[str(scenario_id)] = roadmap

        logger.info("Roadmap generated", regulation=regulation, milestones=len(milestones))
        return roadmap

    async def list_scenarios(self, regulation: str | None = None) -> list[SimulationScenario]:
        """List all simulation scenarios with optional regulation filter."""
        results = list(self._scenarios)
        if regulation:
            results = [s for s in results if s.regulation.lower() == regulation.lower()]
        return results

    async def compare_scenarios(self, scenario_ids: list[UUID]) -> list[dict]:
        """Compare impact across multiple scenarios."""
        comparisons: list[dict] = []
        for sid in scenario_ids:
            scenario = next((s for s in self._scenarios if s.id == sid), None)
            impact = self._results.get(str(sid))
            comparisons.append(
                {
                    "scenario_id": str(sid),
                    "regulation": scenario.regulation if scenario else "Unknown",
                    "severity": scenario.severity if scenario else "unknown",
                    "remediation_hours": impact.remediation_hours if impact else 0.0,
                    "risk_score": impact.risk_score if impact else 0.0,
                    "affected_files": impact.affected_files_count if impact else 0,
                }
            )
        return sorted(comparisons, key=lambda c: c["risk_score"], reverse=True)
