"""Training simulator service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    DifficultyLevel,
    ScenarioCategory,
    SimStatus,
    SimulationSession,
    SimulatorStats,
    TrainingCertificate,
    TrainingScenario,
)


logger = structlog.get_logger(__name__)


class TrainingSimulatorService:
    """Service for compliance training simulations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._scenarios: list[TrainingScenario] = []
        self._sessions: list[SimulationSession] = []
        self._certificates: list[TrainingCertificate] = []
        self._seed_scenarios()

    def _seed_scenarios(self) -> None:
        """Seed initial training scenarios."""
        self._scenarios = [
            TrainingScenario(
                id="breach-001",
                title="Data Breach Response",
                category=ScenarioCategory.breach_response,
                difficulty=DifficultyLevel.intermediate,
                description="Respond to a simulated data breach affecting customer PII.",
                time_limit_minutes=45,
                steps=[
                    {"step": 1, "action": "Identify the breach scope", "points": 20},
                    {"step": 2, "action": "Contain the breach", "points": 25},
                    {"step": 3, "action": "Notify affected parties", "points": 25},
                    {"step": 4, "action": "Document and remediate", "points": 30},
                ],
                passing_score=70.0,
            ),
            TrainingScenario(
                id="dsar-001",
                title="Data Subject Access Request",
                category=ScenarioCategory.data_request,
                difficulty=DifficultyLevel.beginner,
                description="Handle a GDPR data subject access request within the required timeframe.",
                time_limit_minutes=30,
                steps=[
                    {"step": 1, "action": "Verify requester identity", "points": 25},
                    {"step": 2, "action": "Locate all personal data", "points": 25},
                    {"step": 3, "action": "Compile and deliver response", "points": 25},
                    {"step": 4, "action": "Document the process", "points": 25},
                ],
                passing_score=70.0,
            ),
            TrainingScenario(
                id="vendor-001",
                title="Third-Party Vendor Incident",
                category=ScenarioCategory.vendor_incident,
                difficulty=DifficultyLevel.advanced,
                description="Manage a security incident originating from a third-party vendor.",
                time_limit_minutes=60,
                steps=[
                    {"step": 1, "action": "Assess vendor impact", "points": 20},
                    {"step": 2, "action": "Isolate affected systems", "points": 30},
                    {"step": 3, "action": "Coordinate with vendor", "points": 25},
                    {"step": 4, "action": "Implement corrective actions", "points": 25},
                ],
                passing_score=75.0,
            ),
            TrainingScenario(
                id="audit-001",
                title="Audit Preparation Drill",
                category=ScenarioCategory.audit_prep,
                difficulty=DifficultyLevel.expert,
                description="Prepare for an upcoming SOC 2 Type II audit.",
                time_limit_minutes=90,
                steps=[
                    {"step": 1, "action": "Gather evidence artifacts", "points": 25},
                    {"step": 2, "action": "Review control effectiveness", "points": 25},
                    {"step": 3, "action": "Identify and remediate gaps", "points": 25},
                    {"step": 4, "action": "Prepare audit documentation", "points": 25},
                ],
                passing_score=80.0,
            ),
            TrainingScenario(
                id="policy-001",
                title="Policy Violation Investigation",
                category=ScenarioCategory.policy_violation,
                difficulty=DifficultyLevel.intermediate,
                description="Investigate and resolve an internal policy violation.",
                time_limit_minutes=40,
                steps=[
                    {"step": 1, "action": "Review violation report", "points": 20},
                    {"step": 2, "action": "Interview involved parties", "points": 25},
                    {"step": 3, "action": "Determine root cause", "points": 30},
                    {"step": 4, "action": "Recommend corrective actions", "points": 25},
                ],
                passing_score=70.0,
            ),
        ]

    async def list_scenarios(
        self,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[TrainingScenario]:
        """List training scenarios with optional filters."""
        results = list(self._scenarios)
        if category:
            results = [
                s for s in results if s.category == ScenarioCategory(category)
            ]
        if difficulty:
            results = [
                s for s in results if s.difficulty == DifficultyLevel(difficulty)
            ]
        return results

    async def start_simulation(
        self,
        user_id: str,
        scenario_id: str,
    ) -> SimulationSession:
        """Start a new simulation session for a user."""
        scenario = next(
            (s for s in self._scenarios if s.id == scenario_id), None
        )
        if not scenario:
            msg = f"Scenario {scenario_id} not found"
            raise ValueError(msg)

        session = SimulationSession(
            id=uuid.uuid4(),
            user_id=user_id,
            scenario_id=scenario_id,
            status=SimStatus.in_progress,
            current_step=0,
            score=0.0,
            time_elapsed_seconds=0.0,
            responses=[],
            started_at=datetime.now(UTC),
            completed_at=None,
        )
        self._sessions.append(session)

        await logger.ainfo(
            "simulation_started",
            user_id=user_id,
            scenario_id=scenario_id,
        )
        return session

    async def submit_response(
        self,
        session_id: uuid.UUID,
        step_index: int,
        response: str,
    ) -> SimulationSession:
        """Submit a response for a simulation step."""
        session = next(
            (s for s in self._sessions if s.id == session_id), None
        )
        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        scenario = next(
            (s for s in self._scenarios if s.id == session.scenario_id), None
        )
        if not scenario:
            msg = f"Scenario {session.scenario_id} not found"
            raise ValueError(msg)

        if step_index < len(scenario.steps):
            step = scenario.steps[step_index]
            points = step.get("points", 0)
            # Award points based on response length as a simple heuristic
            earned = points * min(len(response) / 50.0, 1.0)
            session.score += earned

        session.responses.append(
            {
                "step_index": step_index,
                "response": response,
                "submitted_at": datetime.now(UTC).isoformat(),
            }
        )
        session.current_step = step_index + 1
        session.time_elapsed_seconds += 30.0

        await logger.ainfo(
            "response_submitted",
            session_id=str(session_id),
            step_index=step_index,
        )
        return session

    async def complete_simulation(
        self,
        session_id: uuid.UUID,
    ) -> SimulationSession | TrainingCertificate:
        """Complete a simulation and optionally issue a certificate."""
        session = next(
            (s for s in self._sessions if s.id == session_id), None
        )
        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        scenario = next(
            (s for s in self._scenarios if s.id == session.scenario_id), None
        )
        if not scenario:
            msg = f"Scenario {session.scenario_id} not found"
            raise ValueError(msg)

        session.status = SimStatus.completed
        session.completed_at = datetime.now(UTC)

        if session.score >= scenario.passing_score:
            certificate = TrainingCertificate(
                id=uuid.uuid4(),
                user_id=session.user_id,
                scenario_id=session.scenario_id,
                score=session.score,
                issued_at=datetime.now(UTC),
                valid_until=datetime.now(UTC) + timedelta(days=365),
            )
            self._certificates.append(certificate)

            await logger.ainfo(
                "certificate_issued",
                user_id=session.user_id,
                scenario_id=session.scenario_id,
                score=session.score,
            )
            return certificate

        session.status = SimStatus.failed
        await logger.ainfo(
            "simulation_failed",
            user_id=session.user_id,
            score=session.score,
            passing_score=scenario.passing_score,
        )
        return session

    async def get_session(
        self,
        session_id: uuid.UUID,
    ) -> SimulationSession | None:
        """Get a simulation session by ID."""
        return next(
            (s for s in self._sessions if s.id == session_id), None
        )

    async def list_sessions(
        self,
        user_id: str | None = None,
    ) -> list[SimulationSession]:
        """List simulation sessions, optionally filtered by user."""
        if user_id:
            return [s for s in self._sessions if s.user_id == user_id]
        return list(self._sessions)

    async def get_stats(self) -> SimulatorStats:
        """Get aggregate simulator statistics."""
        total = len(self._sessions)
        completed = [
            s for s in self._sessions if s.status == SimStatus.completed
        ]
        scores = [s.score for s in completed]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        passed = sum(1 for s in completed if s.score >= 70.0)
        pass_rate = (passed / len(completed) * 100.0) if completed else 0.0

        by_category: dict[str, int] = {}
        for session in self._sessions:
            scenario = next(
                (s for s in self._scenarios if s.id == session.scenario_id),
                None,
            )
            if scenario:
                cat = scenario.category.value
                by_category[cat] = by_category.get(cat, 0) + 1

        return SimulatorStats(
            total_sessions=total,
            completed=len(completed),
            pass_rate=pass_rate,
            avg_score=avg_score,
            by_category=by_category,
            certificates_issued=len(self._certificates),
        )
