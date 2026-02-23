"""Regulatory Change Stream Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reg_change_stream.models import (
    ChangeSeverity,
    ChangeStatus,
    RegulatoryChange,
    StreamNotification,
    StreamStats,
    StreamSubscription,
    SubscriptionChannel,
)


logger = structlog.get_logger()


class RegChangeStreamService:
    """Real-time regulatory change streaming with subscriber management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._changes: list[RegulatoryChange] = []
        self._subscriptions: dict[str, StreamSubscription] = {}
        self._notifications: list[StreamNotification] = []

    async def publish_change(self, change: RegulatoryChange) -> RegulatoryChange:
        """Publish a new regulatory change to the stream."""
        change.detected_at = change.detected_at or datetime.now(UTC)
        change.status = ChangeStatus.DETECTED
        self._changes.append(change)

        # Classify severity based on content heuristics
        change = self._classify_change(change)

        # Fan out to subscribers
        await self._notify_subscribers(change)

        logger.info(
            "Regulatory change published",
            regulation=change.regulation,
            severity=change.severity.value,
        )
        return change

    def _classify_change(self, change: RegulatoryChange) -> RegulatoryChange:
        """Classify severity of a regulatory change."""
        keywords_critical = ["mandatory", "prohibition", "penalty", "fine", "enforcement"]
        keywords_high = ["requirement", "obligation", "deadline", "effective immediately"]
        text = f"{change.title} {change.summary}".lower()

        if any(k in text for k in keywords_critical):
            change.severity = ChangeSeverity.CRITICAL
        elif any(k in text for k in keywords_high):
            change.severity = ChangeSeverity.HIGH

        change.status = ChangeStatus.CLASSIFIED
        return change

    async def _notify_subscribers(self, change: RegulatoryChange) -> None:
        """Fan out change to matching subscribers."""
        for sub in self._subscriptions.values():
            if not sub.is_active:
                continue
            if not self._matches_subscription(change, sub):
                continue

            notification = StreamNotification(
                subscription_id=sub.id,
                change_id=change.id,
                channel=sub.channel,
                status="sent",
                attempts=1,
                sent_at=datetime.now(UTC),
            )
            self._notifications.append(notification)
            sub.last_notified_at = datetime.now(UTC)

        change.status = ChangeStatus.NOTIFIED
        logger.info("Subscribers notified", change_id=str(change.id))

    def _matches_subscription(self, change: RegulatoryChange, sub: StreamSubscription) -> bool:
        """Check if a change matches subscription filters."""
        severity_order = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        if severity_order.get(change.severity.value, 0) < severity_order.get(sub.severity_threshold.value, 0):
            return False
        if sub.jurisdictions and change.jurisdiction not in sub.jurisdictions:
            return False
        return not (sub.frameworks and not set(change.affected_frameworks) & set(sub.frameworks))

    async def subscribe(
        self,
        subscriber_id: str,
        channel: str,
        endpoint_url: str = "",
        severity_threshold: str = "medium",
        jurisdictions: list[str] | None = None,
        frameworks: list[str] | None = None,
    ) -> StreamSubscription:
        """Create or update a subscription."""
        sub = StreamSubscription(
            subscriber_id=subscriber_id,
            channel=SubscriptionChannel(channel),
            endpoint_url=endpoint_url,
            severity_threshold=ChangeSeverity(severity_threshold),
            jurisdictions=jurisdictions or [],
            frameworks=frameworks or [],
            is_active=True,
            created_at=datetime.now(UTC),
        )
        self._subscriptions[subscriber_id] = sub
        logger.info("Subscription created", subscriber_id=subscriber_id, channel=channel)
        return sub

    async def unsubscribe(self, subscriber_id: str) -> bool:
        sub = self._subscriptions.get(subscriber_id)
        if not sub:
            return False
        sub.is_active = False
        return True

    def list_subscriptions(self, active_only: bool = True) -> list[StreamSubscription]:
        subs = list(self._subscriptions.values())
        if active_only:
            subs = [s for s in subs if s.is_active]
        return subs

    def get_changes(
        self,
        severity: ChangeSeverity | None = None,
        jurisdiction: str | None = None,
        regulation: str | None = None,
        limit: int = 50,
    ) -> list[RegulatoryChange]:
        results = list(self._changes)
        if severity:
            results = [c for c in results if c.severity == severity]
        if jurisdiction:
            results = [c for c in results if c.jurisdiction == jurisdiction]
        if regulation:
            results = [c for c in results if c.regulation == regulation]
        return sorted(
            results, key=lambda c: c.detected_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )[:limit]

    def get_stats(self) -> StreamStats:
        by_severity: dict[str, int] = {}
        by_jurisdiction: dict[str, int] = {}
        for c in self._changes:
            by_severity[c.severity.value] = by_severity.get(c.severity.value, 0) + 1
            by_jurisdiction[c.jurisdiction] = by_jurisdiction.get(c.jurisdiction, 0) + 1

        return StreamStats(
            total_changes=len(self._changes),
            changes_by_severity=by_severity,
            changes_by_jurisdiction=by_jurisdiction,
            active_subscriptions=sum(1 for s in self._subscriptions.values() if s.is_active),
            notifications_sent=len(self._notifications),
        )

    async def acknowledge_change(self, change_id: UUID) -> RegulatoryChange | None:
        for c in self._changes:
            if c.id == change_id:
                c.status = ChangeStatus.ACKNOWLEDGED
                return c
        return None
