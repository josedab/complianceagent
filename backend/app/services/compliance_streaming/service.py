"""Real-Time Compliance Streaming Protocol Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_streaming.models import (
    ConnectionState,
    StreamChannel,
    StreamEvent,
    StreamEventType,
    StreamStats,
    StreamSubscription,
)


logger = structlog.get_logger()

_CHANNELS = [
    StreamChannel(name="compliance.posture", description="Compliance posture score changes"),
    StreamChannel(name="compliance.violations", description="Violation detection and resolution"),
    StreamChannel(name="compliance.scans", description="Scan completion events"),
    StreamChannel(name="compliance.regulations", description="Regulatory change notifications"),
    StreamChannel(name="compliance.drift", description="Compliance drift events"),
    StreamChannel(name="compliance.fixes", description="Auto-fix and merge events"),
    StreamChannel(name="compliance.alerts", description="Alert firing and resolution"),
]


class ComplianceStreamingService:
    """Real-time compliance event streaming via WebSocket/SSE."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._subscriptions: dict[str, StreamSubscription] = {}
        self._events: list[StreamEvent] = []
        self._channels = {c.name: c for c in _CHANNELS}

    async def publish(
        self,
        event_type: str,
        channel: str,
        payload: dict | None = None,
        tenant_id: str = "",
        repo: str = "",
    ) -> StreamEvent:
        event = StreamEvent(
            event_type=StreamEventType(event_type),
            channel=channel,
            payload=payload or {},
            tenant_id=tenant_id,
            repo=repo,
            timestamp=datetime.now(UTC),
        )
        self._events.append(event)

        ch = self._channels.get(channel)
        if ch:
            ch.event_count += 1

        delivered = await self._fan_out(event)
        logger.info("Event published", channel=channel, event_type=event_type, delivered=delivered)
        return event

    async def _fan_out(self, event: StreamEvent) -> int:
        delivered = 0
        for sub in self._subscriptions.values():
            if sub.state != ConnectionState.CONNECTED:
                continue
            if sub.channels and event.channel not in sub.channels:
                continue
            if sub.event_types and event.event_type.value not in sub.event_types:
                continue
            if sub.filters.get("tenant_id") and sub.filters["tenant_id"] != event.tenant_id:
                continue
            sub.events_received += 1
            sub.last_event_at = datetime.now(UTC)
            delivered += 1
        return delivered

    async def subscribe(
        self,
        client_id: str,
        channels: list[str] | None = None,
        event_types: list[str] | None = None,
        filters: dict | None = None,
    ) -> StreamSubscription:
        sub = StreamSubscription(
            client_id=client_id,
            channels=channels or [],
            event_types=event_types or [],
            filters=filters or {},
            state=ConnectionState.CONNECTED,
            connected_at=datetime.now(UTC),
        )
        self._subscriptions[client_id] = sub

        for ch_name in (channels or []):
            ch = self._channels.get(ch_name)
            if ch:
                ch.subscriber_count += 1

        logger.info("Client subscribed", client_id=client_id, channels=channels)
        return sub

    async def unsubscribe(self, client_id: str) -> bool:
        sub = self._subscriptions.get(client_id)
        if not sub:
            return False
        sub.state = ConnectionState.DISCONNECTED
        for ch_name in sub.channels:
            ch = self._channels.get(ch_name)
            if ch and ch.subscriber_count > 0:
                ch.subscriber_count -= 1
        return True

    def get_recent_events(
        self,
        channel: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[StreamEvent]:
        results = list(self._events)
        if channel:
            results = [e for e in results if e.channel == channel]
        if event_type:
            results = [e for e in results if e.event_type.value == event_type]
        return sorted(results, key=lambda e: e.timestamp or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def list_channels(self) -> list[StreamChannel]:
        return list(self._channels.values())

    def list_subscriptions(self, active_only: bool = True) -> list[StreamSubscription]:
        subs = list(self._subscriptions.values())
        if active_only:
            subs = [s for s in subs if s.state == ConnectionState.CONNECTED]
        return subs

    def get_stats(self) -> StreamStats:
        active = sum(1 for s in self._subscriptions.values() if s.state == ConnectionState.CONNECTED)
        by_type: dict[str, int] = {}
        for e in self._events:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
        return StreamStats(
            active_connections=active,
            total_events_published=len(self._events),
            events_per_second=round(len(self._events) / max(1, 60), 2),
            channels=list(self._channels.values()),
            by_event_type=by_type,
        )
