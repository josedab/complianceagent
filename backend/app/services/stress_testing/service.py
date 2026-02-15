"""Regulatory Compliance Stress Testing Service."""

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stress_testing.models import (
    RiskExposure,
    RiskTier,
    ScenarioType,
    SimulationResult,
    SimulationRun,
    StressScenario,
    StressTestReport,
)


logger = structlog.get_logger()


class StressTestingService:
    """Service for regulatory compliance stress testing."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot_client = copilot_client
        self._scenarios: list[StressScenario] = []
        self._simulations: list[SimulationRun] = []
        self._risk_exposures: list[RiskExposure] = []

    async def create_scenario(
        self,
        name: str,
        scenario_type: ScenarioType,
        description: str,
        parameters: dict | None = None,
    ) -> StressScenario:
        """Create a new stress test scenario."""
        scenario = StressScenario(
            name=name,
            scenario_type=scenario_type,
            description=description,
            parameters=parameters or {},
            probability=random.uniform(0.01, 0.3),
            severity=random.choice(list(RiskTier)),
        )
        self._scenarios.append(scenario)
        logger.info("Scenario created", name=name, scenario_type=scenario_type.value)
        return scenario

    async def list_scenarios(self) -> list[StressScenario]:
        """List all stress test scenarios."""
        return list(self._scenarios)

    async def run_simulation(
        self,
        scenario_id: UUID,
        iterations: int = 1000,
        confidence: float = 0.95,
    ) -> SimulationRun:
        """Run a Monte Carlo simulation for a scenario."""
        scenario = next((s for s in self._scenarios if s.id == scenario_id), None)
        if not scenario:
            logger.warning("Scenario not found", scenario_id=str(scenario_id))
            return SimulationRun(scenario_id=scenario_id, status="failed")

        run = SimulationRun(
            scenario_id=scenario_id,
            iterations=iterations,
            confidence_level=confidence,
            status="running",
            started_at=datetime.now(UTC),
        )

        # Generate mock Monte Carlo results
        metrics = [
            "response_time_hours",
            "financial_impact_usd",
            "records_affected",
            "compliance_recovery_days",
        ]
        for metric in metrics:
            values = [random.gauss(100, 30) for _ in range(iterations)]
            values.sort()
            result = SimulationResult(
                run_id=run.id,
                metric=metric,
                p50=round(values[int(iterations * 0.50)], 2),
                p95=round(values[int(iterations * 0.95)], 2),
                p99=round(values[int(iterations * 0.99)], 2),
                mean=round(sum(values) / len(values), 2),
                std_dev=round(
                    (sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values))
                    ** 0.5,
                    2,
                ),
                distribution=[
                    {
                        "bucket": f"{i * 10}-{(i + 1) * 10}",
                        "count": sum(1 for v in values if i * 10 <= v < (i + 1) * 10),
                    }
                    for i in range(20)
                ],
            )
            run.results.append(result)

        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        self._simulations.append(run)

        logger.info(
            "Simulation completed",
            scenario_id=str(scenario_id),
            iterations=iterations,
            metrics=len(run.results),
        )
        return run

    async def get_simulation(self, run_id: UUID) -> SimulationRun | None:
        """Get a simulation run by ID."""
        return next((s for s in self._simulations if s.id == run_id), None)

    async def calculate_risk_exposure(self, regulation: str) -> RiskExposure:
        """Calculate risk exposure based on scenario results."""
        completed = [s for s in self._simulations if s.status == "completed"]
        total_exposure = sum(
            r.p95 for sim in completed for r in sim.results if r.metric == "financial_impact_usd"
        )
        probability = random.uniform(0.05, 0.4)
        expected_loss = total_exposure * probability

        tier_thresholds = [
            (1_000_000, RiskTier.CATASTROPHIC),
            (500_000, RiskTier.SEVERE),
            (100_000, RiskTier.SIGNIFICANT),
            (10_000, RiskTier.MODERATE),
        ]
        risk_tier = RiskTier.MINIMAL
        for threshold, tier in tier_thresholds:
            if expected_loss >= threshold:
                risk_tier = tier
                break

        exposure = RiskExposure(
            regulation=regulation,
            exposure_amount=round(total_exposure, 2),
            probability=round(probability, 4),
            expected_loss=round(expected_loss, 2),
            risk_tier=risk_tier,
            mitigations=[
                "Implement automated incident response",
                "Enhance data encryption at rest",
                "Conduct quarterly compliance audits",
            ],
        )
        self._risk_exposures.append(exposure)
        logger.info("Risk exposure calculated", regulation=regulation, tier=risk_tier.value)
        return exposure

    async def generate_report(self) -> StressTestReport:
        """Generate an aggregate stress test report."""
        aggregate = sum(e.expected_loss for e in self._risk_exposures)
        worst = (
            max(self._risk_exposures, key=lambda e: e.expected_loss).regulation
            if self._risk_exposures
            else "N/A"
        )

        report = StressTestReport(
            total_scenarios=len(self._scenarios),
            total_simulations=len(self._simulations),
            aggregate_exposure=round(aggregate, 2),
            risk_exposures=list(self._risk_exposures),
            worst_case_scenario=worst,
            recommendations=[
                "Prioritize remediation for highest-exposure regulations",
                "Increase simulation frequency for catastrophic scenarios",
                "Review vendor failure contingency plans",
                "Establish regulatory change monitoring pipeline",
            ],
            generated_at=datetime.now(UTC),
        )
        logger.info("Stress test report generated", scenarios=report.total_scenarios)
        return report

    async def list_simulations(self, scenario_id: UUID | None = None) -> list[SimulationRun]:
        """List simulation runs with optional scenario filter."""
        results = list(self._simulations)
        if scenario_id:
            results = [s for s in results if s.scenario_id == scenario_id]
        return results
