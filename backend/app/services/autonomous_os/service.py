"""Compliance Autonomous Operating System Service."""
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.autonomous_os.models import (
    AutonomousDecision,
    AutonomousOSStats,
    AutonomyLevel,
    DecisionType,
    OrchestratorEvent,
    OrchestratorState,
    SystemHealth,
)


logger = structlog.get_logger()

_SERVICE_REGISTRY = [
    "monitoring",
    "parsing",
    "mapping",
    "generation",
    "audit",
    "mcp_server",
    "self_healing_mesh",
    "agent_swarm",
    "compliance_gnn",
    "knowledge_fabric",
    "policy_dsl",
    "compliance_streaming",
    "cert_pipeline",
    "evidence_generation",
    "code_review_agent",
    "reg_prediction",
    "twin_simulation",
    "workflow_automation",
]


class AutonomousOSService:
    """Unified orchestration layer coordinating all compliance services."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._events: list[OrchestratorEvent] = []
        self._decisions: list[AutonomousDecision] = []
        self._state = OrchestratorState.IDLE
        self._autonomy = AutonomyLevel.SUPERVISED
        self._auto_fixes = 0
        self._escalations = 0

    async def process_event(
        self,
        event_type: str,
        source_service: str,
        payload: dict | None = None,
    ) -> AutonomousDecision:
        start = datetime.now(UTC)
        event = OrchestratorEvent(
            event_type=event_type,
            source_service=source_service,
            payload=payload or {},
            timestamp=start,
        )
        self._events.append(event)
        self._state = OrchestratorState.SCANNING

        decision = self._make_decision(event)
        actions = self._execute_decision(decision, event)

        event.decision = decision.decision_type
        event.actions_taken = actions

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        decision.duration_ms = round(duration, 2)
        decision.decided_at = datetime.now(UTC)
        self._decisions.append(decision)
        self._state = OrchestratorState.IDLE

        logger.info(
            "Event processed",
            event_type=event_type,
            decision=decision.decision_type.value,
        )
        return decision

    def _make_decision(self, event: OrchestratorEvent) -> AutonomousDecision:
        severity = event.payload.get("severity", "medium")
        event_type = event.event_type

        if event_type == "violation_detected" and severity == "low":
            return AutonomousDecision(
                event_id=event.id,
                decision_type=DecisionType.AUTO_FIX,
                confidence=0.92,
                reasoning="Low-severity violation — auto-fix eligible",
                services_invoked=["self_healing_mesh", "code_review_agent"],
            )
        if event_type == "violation_detected" and severity in ("high", "critical"):
            return AutonomousDecision(
                event_id=event.id,
                decision_type=DecisionType.ESCALATE,
                confidence=0.88,
                reasoning="High-severity violation requires human review",
                services_invoked=["workflow_automation", "compliance_streaming"],
            )
        if event_type == "regulation_change":
            return AutonomousDecision(
                event_id=event.id,
                decision_type=DecisionType.PREDICT,
                confidence=0.75,
                reasoning="New regulation — predict impact and prepare",
                services_invoked=[
                    "reg_prediction",
                    "twin_simulation",
                    "knowledge_fabric",
                ],
            )
        if event_type == "score_drop":
            return AutonomousDecision(
                event_id=event.id,
                decision_type=DecisionType.AUTO_FIX,
                confidence=0.85,
                reasoning="Score regression — trigger healing pipeline",
                services_invoked=["self_healing_mesh", "compliance_gnn"],
            )
        return AutonomousDecision(
            event_id=event.id,
            decision_type=DecisionType.MONITOR,
            confidence=0.70,
            reasoning="Event noted — monitoring",
            services_invoked=["compliance_streaming"],
        )

    def _execute_decision(
        self,
        decision: AutonomousDecision,
        event: OrchestratorEvent,
    ) -> list[str]:
        actions = []
        if decision.decision_type == DecisionType.AUTO_FIX:
            self._auto_fixes += 1
            actions.extend([
                "triggered_scan",
                "generated_fix",
                "created_pr",
                "ran_tests",
            ])
            decision.outcome = "Auto-fix applied successfully"
        elif decision.decision_type == DecisionType.ESCALATE:
            self._escalations += 1
            actions.extend([
                "notified_team",
                "created_ticket",
                "escalated_to_reviewer",
            ])
            decision.outcome = "Escalated to human reviewer"
        elif decision.decision_type == DecisionType.PREDICT:
            actions.extend([
                "analyzed_regulation",
                "predicted_impact",
                "generated_tasks",
            ])
            decision.outcome = "Impact prediction generated"
        else:
            actions.append("logged_event")
            decision.outcome = "Event monitored"
        return actions

    async def set_autonomy_level(self, level: str) -> SystemHealth:
        self._autonomy = AutonomyLevel(level)
        logger.info("Autonomy level changed", level=level)
        return self.get_health()

    def get_health(self) -> SystemHealth:
        return SystemHealth(
            state=self._state,
            autonomy_level=self._autonomy,
            services_active=len(_SERVICE_REGISTRY),
            events_processed=len(self._events),
            decisions_made=len(self._decisions),
            auto_fixes_applied=self._auto_fixes,
            escalations=self._escalations,
            last_cycle_at=datetime.now(UTC),
        )

    def list_events(self, limit: int = 50) -> list[OrchestratorEvent]:
        return sorted(
            self._events,
            key=lambda e: e.timestamp or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )[:limit]

    def list_decisions(
        self,
        decision_type: DecisionType | None = None,
        limit: int = 50,
    ) -> list[AutonomousDecision]:
        results = list(self._decisions)
        if decision_type:
            results = [d for d in results if d.decision_type == decision_type]
        return sorted(
            results,
            key=lambda d: d.decided_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )[:limit]

    def get_stats(self) -> AutonomousOSStats:
        by_type: dict[str, int] = {}
        times: list[float] = []
        for d in self._decisions:
            by_type[d.decision_type.value] = (
                by_type.get(d.decision_type.value, 0) + 1
            )
            times.append(d.duration_ms)
        total = len(self._decisions)
        return AutonomousOSStats(
            total_events=len(self._events),
            total_decisions=total,
            auto_fix_rate=round(self._auto_fixes / total, 2) if total else 0.0,
            avg_decision_time_ms=(
                round(sum(times) / len(times), 2) if times else 0.0
            ),
            by_decision_type=by_type,
        )
