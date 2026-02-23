"""API endpoints for Multi-Tenant Compliance Data Lake."""

from typing import Any

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_data_lake import ComplianceDataLakeService


logger = structlog.get_logger()
router = APIRouter()


class IngestEventRequest(BaseModel):
    tenant_id: str = Field(...)
    category: str = Field(default="score_change")
    source_service: str = Field(default="")
    repo: str = Field(default="")
    framework: str = Field(default="")
    data: dict[str, Any] = Field(default_factory=dict)


class EventSchema(BaseModel):
    id: str
    tenant_id: str
    category: str
    source_service: str
    repo: str
    framework: str
    timestamp: str | None


class AnalyticsResultSchema(BaseModel):
    total_events: int
    aggregations: dict[str, Any]
    execution_time_ms: float


class LakeStatsSchema(BaseModel):
    total_events: int
    by_category: dict[str, int]
    by_tenant: dict[str, int]
    storage_size_mb: float


@router.post("/events", response_model=EventSchema, status_code=status.HTTP_201_CREATED, summary="Ingest event")
async def ingest_event(request: IngestEventRequest, db: DB) -> EventSchema:
    service = ComplianceDataLakeService(db=db)
    e = await service.ingest_event(tenant_id=request.tenant_id, category=request.category, source_service=request.source_service, repo=request.repo, framework=request.framework, data=request.data)
    return EventSchema(id=str(e.id), tenant_id=e.tenant_id, category=e.category.value, source_service=e.source_service, repo=e.repo, framework=e.framework, timestamp=e.timestamp.isoformat() if e.timestamp else None)


@router.post("/events/batch", summary="Ingest batch events")
async def ingest_batch(events: list[dict[str, Any]], db: DB) -> dict:
    service = ComplianceDataLakeService(db=db)
    count = await service.ingest_batch(events)
    return {"ingested": count}


@router.get("/analytics", response_model=AnalyticsResultSchema, summary="Query analytics")
async def query_analytics(db: DB, tenant_id: str = "", category: str | None = None, framework: str | None = None) -> AnalyticsResultSchema:
    service = ComplianceDataLakeService(db=db)
    r = await service.query_analytics(tenant_id=tenant_id, category=category, framework=framework)
    return AnalyticsResultSchema(total_events=r.total_events, aggregations=r.aggregations, execution_time_ms=r.execution_time_ms)


@router.get("/stats", response_model=LakeStatsSchema, summary="Get data lake stats")
async def get_stats(db: DB) -> LakeStatsSchema:
    service = ComplianceDataLakeService(db=db)
    s = service.get_stats()
    return LakeStatsSchema(total_events=s.total_events, by_category=s.by_category, by_tenant=s.by_tenant, storage_size_mb=s.storage_size_mb)
