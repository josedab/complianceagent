"""Real-Time Compliance Posture API Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.realtime_posture.models import (
    AlertChannel,
    AlertRule,
    PostureEvent,
    PostureSnapshot,
    PostureStreamConfig,
)


logger = structlog.get_logger()


class RealtimePostureService:
    """Service for real-time compliance posture monitoring."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._snapshots: list[PostureSnapshot] = []
        self._events: list[dict] = []
        self._alert_rules: list[AlertRule] = []
        self._config = PostureStreamConfig(
            poll_interval_seconds=30,
            channels=[AlertChannel.EMAIL],
        )

    async def get_current_posture(self, organization_id: str) -> PostureSnapshot:
        """Get the current compliance posture for an organization."""
        existing = [s for s in self._snapshots if s.organization_id == organization_id]
        if existing:
            return existing[-1]

        snapshot = PostureSnapshot(
            organization_id=organization_id,
            score=78.5,
            grade="B",
            violations=12,
            timestamp=datetime.now(UTC),
        )
        self._snapshots.append(snapshot)
        logger.info(
            "Posture snapshot created", organization_id=organization_id, score=snapshot.score
        )
        return snapshot

    async def record_event(
        self,
        organization_id: str,
        event_type: PostureEvent,
        details: dict | None = None,
    ) -> dict:
        """Record a posture event and check alert thresholds."""
        event = {
            "organization_id": organization_id,
            "event_type": event_type.value,
            "details": details or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._events.append(event)

        triggered = await self.check_alerts(organization_id)

        logger.info(
            "Posture event recorded",
            organization_id=organization_id,
            event_type=event_type.value,
            alerts_triggered=len(triggered),
        )
        return event

    async def list_events(
        self,
        organization_id: str | None = None,
        event_type: PostureEvent | None = None,
    ) -> list[dict]:
        """List recorded posture events with optional filters."""
        results = list(self._events)
        if organization_id:
            results = [e for e in results if e["organization_id"] == organization_id]
        if event_type:
            results = [e for e in results if e["event_type"] == event_type.value]
        return results

    async def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Create a new alert rule."""
        self._alert_rules.append(rule)
        logger.info("Alert rule created", rule_name=rule.name, metric=rule.metric)
        return rule

    async def list_alert_rules(self) -> list[AlertRule]:
        """List all configured alert rules."""
        return list(self._alert_rules)

    async def delete_alert_rule(self, rule_id: UUID) -> bool:
        """Delete an alert rule by ID."""
        before = len(self._alert_rules)
        self._alert_rules = [r for r in self._alert_rules if r.id != rule_id]
        deleted = len(self._alert_rules) < before
        if deleted:
            logger.info("Alert rule deleted", rule_id=str(rule_id))
        return deleted

    async def check_alerts(self, organization_id: str) -> list[AlertRule]:
        """Check all alert rules against current posture and return triggered rules."""
        snapshot = await self.get_current_posture(organization_id)
        triggered: list[AlertRule] = []

        for rule in self._alert_rules:
            if not rule.enabled:
                continue
            value = 0.0
            if rule.metric == "score":
                value = snapshot.score
            elif rule.metric == "violations":
                value = float(snapshot.violations)
            if value < rule.threshold:
                triggered.append(rule)
                logger.warning(
                    "Alert triggered",
                    rule_name=rule.name,
                    metric=rule.metric,
                    value=value,
                    threshold=rule.threshold,
                )
        return triggered

    async def get_posture_stream_config(self) -> PostureStreamConfig:
        """Get the current posture stream configuration."""
        return self._config
