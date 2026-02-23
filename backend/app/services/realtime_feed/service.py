"""Real-Time Regulatory Change Feed Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.realtime_feed.models import (
    FeedItem,
    FeedItemType,
    FeedPriority,
    FeedStats,
    FeedSubscription,
    NotificationChannel,
    SlackCard,
)


logger = structlog.get_logger()

_SEED_FEED: list[FeedItem] = [
    FeedItem(item_type=FeedItemType.REGULATION_CHANGE, priority=FeedPriority.URGENT, title="EU AI Act Article 6 — High-Risk AI Systems Classification Effective", summary="New classification criteria for high-risk AI systems now enforceable. Organizations must classify and document all AI systems.", regulation="EU AI Act", jurisdiction="EU", impact_score=9.2, published_at=datetime(2026, 2, 21, 8, 0, tzinfo=UTC)),
    FeedItem(item_type=FeedItemType.ENFORCEMENT_ACTION, priority=FeedPriority.HIGH, title="GDPR: €20M Fine for Insufficient Consent Mechanism", summary="Irish DPC fines tech company €20M for non-compliant cookie consent implementation.", regulation="GDPR", jurisdiction="EU", impact_score=7.8, published_at=datetime(2026, 2, 20, 14, 30, tzinfo=UTC)),
    FeedItem(item_type=FeedItemType.GUIDANCE_UPDATE, priority=FeedPriority.NORMAL, title="HIPAA: Updated Telehealth PHI Guidance", summary="HHS releases updated guidance on PHI handling for telehealth platforms.", regulation="HIPAA", jurisdiction="US", impact_score=6.5, published_at=datetime(2026, 2, 19, 10, 0, tzinfo=UTC)),
    FeedItem(item_type=FeedItemType.DEADLINE_REMINDER, priority=FeedPriority.HIGH, title="PCI-DSS v4.0.1: March 2026 Compliance Deadline", summary="All organizations must be fully compliant with PCI-DSS v4.0.1 by March 31, 2026.", regulation="PCI-DSS", jurisdiction="Global", impact_score=8.5, published_at=datetime(2026, 2, 18, 9, 0, tzinfo=UTC)),
    FeedItem(item_type=FeedItemType.CONSULTATION, priority=FeedPriority.NORMAL, title="NIS2: ENISA Publishes Supply Chain Security Consultation", summary="ENISA seeks industry input on NIS2 supply chain security implementation guidance.", regulation="NIS2", jurisdiction="EU", impact_score=5.5, published_at=datetime(2026, 2, 17, 11, 0, tzinfo=UTC)),
]


class RealtimeFeedService:
    """Real-time regulatory change feed with notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._items: list[FeedItem] = list(_SEED_FEED)
        self._subscriptions: dict[str, FeedSubscription] = {}
        self._notifications_sent = 0

    async def publish_item(self, item: FeedItem) -> FeedItem:
        item.published_at = item.published_at or datetime.now(UTC)
        self._items.append(item)
        await self._notify_subscribers(item)
        logger.info("Feed item published", title=item.title[:50], priority=item.priority.value)
        return item

    async def _notify_subscribers(self, item: FeedItem) -> None:
        priority_order = {"low": 0, "normal": 1, "high": 2, "urgent": 3}
        for sub in self._subscriptions.values():
            if priority_order.get(item.priority.value, 0) < priority_order.get(sub.min_priority.value, 0):
                continue
            if sub.jurisdictions and item.jurisdiction not in sub.jurisdictions:
                continue
            if sub.frameworks and item.regulation not in sub.frameworks:
                continue
            self._notifications_sent += 1

    def get_feed(
        self,
        item_type: FeedItemType | None = None,
        priority: FeedPriority | None = None,
        jurisdiction: str | None = None,
        limit: int = 20,
    ) -> list[FeedItem]:
        results = list(self._items)
        if item_type:
            results = [i for i in results if i.item_type == item_type]
        if priority:
            results = [i for i in results if i.priority == priority]
        if jurisdiction:
            results = [i for i in results if i.jurisdiction == jurisdiction]
        return sorted(results, key=lambda i: i.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    async def subscribe(
        self,
        user_id: str,
        channels: list[str] | None = None,
        min_priority: str = "normal",
        jurisdictions: list[str] | None = None,
        frameworks: list[str] | None = None,
        digest_enabled: bool = False,
    ) -> FeedSubscription:
        sub = FeedSubscription(
            user_id=user_id,
            channels=[NotificationChannel(c) for c in (channels or ["websocket"])],
            min_priority=FeedPriority(min_priority),
            jurisdictions=jurisdictions or [],
            frameworks=frameworks or [],
            digest_enabled=digest_enabled,
            created_at=datetime.now(UTC),
        )
        self._subscriptions[user_id] = sub
        logger.info("Feed subscription created", user=user_id)
        return sub

    async def unsubscribe(self, user_id: str) -> bool:
        return self._subscriptions.pop(user_id, None) is not None

    def generate_slack_card(self, item: FeedItem) -> SlackCard:
        color_map = {"urgent": "#FF0000", "high": "#FF8C00", "normal": "#36a64f", "low": "#808080"}
        return SlackCard(
            title=item.title,
            text=item.summary,
            color=color_map.get(item.priority.value, "#36a64f"),
            fields=[
                {"title": "Regulation", "value": item.regulation},
                {"title": "Jurisdiction", "value": item.jurisdiction},
                {"title": "Impact", "value": f"{item.impact_score}/10"},
                {"title": "Priority", "value": item.priority.value.upper()},
            ],
            action_url=item.source_url,
        )

    def get_stats(self) -> FeedStats:
        by_type: dict[str, int] = {}
        by_jur: dict[str, int] = {}
        today = datetime.now(UTC).date()
        items_today = 0
        for item in self._items:
            by_type[item.item_type.value] = by_type.get(item.item_type.value, 0) + 1
            by_jur[item.jurisdiction] = by_jur.get(item.jurisdiction, 0) + 1
            if item.published_at and item.published_at.date() == today:
                items_today += 1
        return FeedStats(
            total_items=len(self._items),
            items_today=items_today,
            subscribers=len(self._subscriptions),
            by_type=by_type,
            by_jurisdiction=by_jur,
            notifications_sent=self._notifications_sent,
        )
