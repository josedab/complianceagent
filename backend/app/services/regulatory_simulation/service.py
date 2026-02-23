"""Regulatory Simulation Service."""
import hashlib
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.regulatory_simulation.models import (
    ImpactForecast,
    RegOutcome,
    SimulationModel,
    SimulationRun,
    SimulationScenario,
    SimulationStats,
)


logger = structlog.get_logger()

_SEED_SCENARIOS = [
    SimulationScenario(
        title="EU AI Act Enforcement",
        regulation="EU AI Act",
        jurisdiction="EU",
        base_probability=0.89,
        factors=[
            {"factor": "political_support", "weight": 0.3, "value": 0.92},
            {"factor": "industry_readiness", "weight": 0.2, "value": 0.65},
            {"factor": "public_pressure", "weight": 0.25, "value": 0.88},
            {"factor": "technical_feasibility", "weight": 0.25, "value": 0.78},
        ],
        predicted_outcome=RegOutcome.ENACTED,
        confidence_interval=(0.82, 0.94),
    ),
    SimulationScenario(
        title="US Federal Privacy Law",
        regulation="American Privacy Rights Act",
        jurisdiction="US",
        base_probability=0.42,
        factors=[
            {"factor": "bipartisan_support", "weight": 0.35, "value": 0.45},
            {"factor": "state_preemption_debate", "weight": 0.25, "value": 0.55},
            {"factor": "industry_lobbying", "weight": 0.2, "value": 0.70},
            {"factor": "election_cycle", "weight": 0.2, "value": 0.30},
        ],
        predicted_outcome=RegOutcome.DELAYED,
        confidence_interval=(0.30, 0.55),
    ),
    SimulationScenario(
        title="DORA Compliance Deadline",
        regulation="Digital Operational Resilience Act",
        jurisdiction="EU",
        base_probability=0.95,
        factors=[
            {"factor": "regulatory_commitment", "weight": 0.4, "value": 0.98},
            {"factor": "financial_sector_prep", "weight": 0.3, "value": 0.72},
            {"factor": "enforcement_resources", "weight": 0.3, "value": 0.85},
        ],
        predicted_outcome=RegOutcome.ENACTED,
        confidence_interval=(0.91, 0.98),
    ),
    SimulationScenario(
        title="India DPDP Act Amendment",
        regulation="Digital Personal Data Protection Act",
        jurisdiction="India",
        base_probability=0.67,
        factors=[
            {"factor": "government_priority", "weight": 0.3, "value": 0.80},
            {"factor": "cross_border_data_flow", "weight": 0.25, "value": 0.55},
            {"factor": "industry_feedback", "weight": 0.25, "value": 0.60},
            {"factor": "implementation_capacity", "weight": 0.2, "value": 0.50},
        ],
        predicted_outcome=RegOutcome.AMENDED,
        confidence_interval=(0.55, 0.78),
    ),
    SimulationScenario(
        title="UK Online Safety Bill Evolution",
        regulation="UK Online Safety Act",
        jurisdiction="UK",
        base_probability=0.73,
        factors=[
            {"factor": "enforcement_guidance", "weight": 0.3, "value": 0.82},
            {"factor": "tech_industry_compliance", "weight": 0.25, "value": 0.60},
            {"factor": "public_sentiment", "weight": 0.25, "value": 0.85},
            {"factor": "ofcom_readiness", "weight": 0.2, "value": 0.70},
        ],
        predicted_outcome=RegOutcome.ENACTED,
        confidence_interval=(0.63, 0.82),
    ),
]


class RegulatorySimulationService:
    """Simulates regulatory outcomes using deterministic models."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._scenarios: list[SimulationScenario] = list(_SEED_SCENARIOS)
        self._runs: list[SimulationRun] = []

    def _deterministic_probability(self, seed: str, base: float) -> float:
        h = hashlib.sha256(seed.encode()).hexdigest()
        noise = (int(h[:8], 16) % 1000) / 10000.0 - 0.05
        return round(max(0.0, min(1.0, base + noise)), 4)

    async def run_simulation(
        self,
        regulation: str,
        jurisdiction: str,
        iterations: int = 1000,
        model: str = "monte_carlo",
    ) -> SimulationRun:
        start = datetime.now(UTC)
        sim_model = SimulationModel(model)

        matching = [
            s for s in self._scenarios
            if s.regulation.lower() == regulation.lower()
            and s.jurisdiction.lower() == jurisdiction.lower()
        ]

        if not matching:
            scenario = SimulationScenario(
                title=f"{regulation} Simulation",
                regulation=regulation,
                jurisdiction=jurisdiction,
                base_probability=0.50,
                predicted_outcome=RegOutcome.ENACTED,
                confidence_interval=(0.35, 0.65),
            )
            self._scenarios.append(scenario)
            matching = [scenario]

        distribution: list[dict] = []
        outcome_counts: dict[str, int] = {}

        for outcome in RegOutcome:
            seed = f"{regulation}:{jurisdiction}:{outcome.value}:{iterations}"
            prob = self._deterministic_probability(seed, matching[0].base_probability)
            if outcome == matching[0].predicted_outcome:
                prob = matching[0].base_probability

            distribution.append({
                "outcome": outcome.value,
                "probability": prob,
                "iterations_favorable": int(prob * iterations),
            })
            outcome_counts[outcome.value] = int(prob * iterations)

        elapsed = (datetime.now(UTC) - start).total_seconds() * 1000

        run = SimulationRun(
            scenarios=matching,
            iterations=iterations,
            model=sim_model,
            results={
                "predicted_outcome": matching[0].predicted_outcome.value,
                "primary_probability": matching[0].base_probability,
                "outcome_counts": outcome_counts,
            },
            probability_distribution=distribution,
            execution_time_ms=round(elapsed, 2),
            run_at=datetime.now(UTC),
        )
        self._runs.append(run)

        logger.info(
            "Simulation completed",
            regulation=regulation,
            jurisdiction=jurisdiction,
            model=model,
            iterations=iterations,
        )
        return run

    def generate_forecast(self, regulation: str) -> ImpactForecast:
        matching = [
            s for s in self._scenarios
            if s.regulation.lower() == regulation.lower()
        ]

        if not matching:
            return ImpactForecast(
                regulation=regulation,
                probability=0.5,
                impact_if_enacted="Unknown — regulation not in scenario database",
                preparation_cost_usd=50000.0,
                non_compliance_risk_usd=500000.0,
                recommended_action="Research and add to monitoring pipeline",
            )

        scenario = matching[0]
        seed = f"forecast:{regulation}:{scenario.jurisdiction}"
        cost_hash = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
        prep_cost = round((cost_hash % 500000) + 25000, 2)
        risk_cost = round(prep_cost * 8.5, 2)

        action_map = {
            RegOutcome.ENACTED: "Begin compliance program immediately",
            RegOutcome.AMENDED: "Monitor amendments and prepare adaptive controls",
            RegOutcome.WITHDRAWN: "Maintain watching brief, reduce active preparation",
            RegOutcome.DELAYED: "Continue monitoring, prepare incrementally",
            RegOutcome.SPLIT: "Track all sub-proposals independently",
        }

        return ImpactForecast(
            regulation=regulation,
            probability=scenario.base_probability,
            impact_if_enacted=f"Affects {scenario.jurisdiction} operations requiring compliance controls for {regulation}",
            preparation_cost_usd=prep_cost,
            non_compliance_risk_usd=risk_cost,
            recommended_action=action_map.get(
                scenario.predicted_outcome,
                "Monitor and assess",
            ),
        )

    def list_runs(self) -> list[SimulationRun]:
        return sorted(
            self._runs,
            key=lambda r: r.run_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

    def get_stats(self) -> SimulationStats:
        by_model: dict[str, int] = {}
        total_iterations = 0
        for r in self._runs:
            by_model[r.model.value] = by_model.get(r.model.value, 0) + 1
            total_iterations += r.iterations
        return SimulationStats(
            total_runs=len(self._runs),
            total_scenarios=len(self._scenarios),
            by_model=by_model,
            avg_iterations=(
                total_iterations // len(self._runs) if self._runs else 0
            ),
            predictions_validated=0,
        )
