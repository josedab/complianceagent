"""Multi-Tenant Compliance Data Lake Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_data_lake.models import (
    AnalyticsResult,
    ComplianceEvent,
    DataLakeStats,
    EventCategory,
    TimeSeriesPoint,
)


logger = structlog.get_logger()


class ComplianceDataLakeService:
    """Centralized time-series store for compliance metrics and events."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._events: list[ComplianceEvent] = []

    async def ingest_event(
        self,
        tenant_id: str,
        category: str,
        source_service: str = "",
        repo: str = "",
        framework: str = "",
        data: dict | None = None,
    ) -> ComplianceEvent:
        event = ComplianceEvent(
            tenant_id=tenant_id,
            category=EventCategory(category),
            source_service=source_service,
            repo=repo,
            framework=framework,
            data=data or {},
            timestamp=datetime.now(UTC),
        )
        self._events.append(event)
        logger.info("Event ingested", tenant=tenant_id, category=category)
        return event

    async def ingest_batch(self, events: list[dict]) -> int:
        count = 0
        for e in events:
            await self.ingest_event(
                tenant_id=e.get("tenant_id", ""),
                category=e.get("category", "score_change"),
                source_service=e.get("source_service", ""),
                repo=e.get("repo", ""),
                framework=e.get("framework", ""),
                data=e.get("data"),
            )
            count += 1
        return count

    async def query_analytics(
        self,
        tenant_id: str,
        category: str | None = None,
        framework: str | None = None,
        period: str = "day",
        limit: int = 100,
    ) -> AnalyticsResult:
        start = datetime.now(UTC)
        filtered = [e for e in self._events if e.tenant_id == tenant_id]
        if category:
            filtered = [e for e in filtered if e.category.value == category]
        if framework:
            filtered = [e for e in filtered if e.framework == framework]
        filtered = filtered[:limit]

        # Build time series
        ts_points: list[TimeSeriesPoint] = []
        for e in filtered:
            ts_points.append(TimeSeriesPoint(
                timestamp=e.timestamp.isoformat() if e.timestamp else "",
                value=e.data.get("score", e.data.get("value", 1.0)),
                labels={"category": e.category.value, "framework": e.framework},
            ))

        # Aggregations
        aggs: dict = {
            "count": len(filtered),
            "by_category": {},
            "by_framework": {},
        }
        for e in filtered:
            aggs["by_category"][e.category.value] = aggs["by_category"].get(e.category.value, 0) + 1
            if e.framework:
                aggs["by_framework"][e.framework] = aggs["by_framework"].get(e.framework, 0) + 1

        duration = (datetime.now(UTC) - start).total_seconds() * 1000
        return AnalyticsResult(
            time_series=ts_points,
            aggregations=aggs,
            total_events=len(filtered),
            execution_time_ms=round(duration, 2),
        )

    def get_stats(self) -> DataLakeStats:
        by_cat: dict[str, int] = {}
        by_tenant: dict[str, int] = {}
        for e in self._events:
            by_cat[e.category.value] = by_cat.get(e.category.value, 0) + 1
            by_tenant[e.tenant_id] = by_tenant.get(e.tenant_id, 0) + 1

        timestamps = [e.timestamp for e in self._events if e.timestamp]
        return DataLakeStats(
            total_events=len(self._events),
            by_category=by_cat,
            by_tenant=by_tenant,
            oldest_event=min(timestamps) if timestamps else None,
            newest_event=max(timestamps) if timestamps else None,
            storage_size_mb=round(len(self._events) * 0.001, 3),
        )
