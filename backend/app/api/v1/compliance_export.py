"""API endpoints for Compliance Data Export."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_export import ComplianceExportService, ExportStatus


logger = structlog.get_logger()
router = APIRouter()


class CreateExportRequest(BaseModel):
    data_type: str = Field(default="full_report")
    format: str = Field(default="json")
    filters: dict[str, Any] = Field(default_factory=dict)

class ExportJobSchema(BaseModel):
    id: str
    data_type: str
    format: str
    status: str
    row_count: int
    file_size_bytes: int
    download_url: str
    created_at: str | None
    completed_at: str | None

class CreateScheduleRequest(BaseModel):
    name: str = Field(...)
    data_type: str = Field(default="full_report")
    format: str = Field(default="json")
    schedule_cron: str = Field(default="0 0 * * 1")
    destination: str = Field(default="")
    connector: str | None = Field(default=None)

class ScheduleSchema(BaseModel):
    id: str
    name: str
    data_type: str
    format: str
    schedule_cron: str
    destination: str
    is_active: bool
    created_at: str | None

class ConfigureConnectorRequest(BaseModel):
    connector: str = Field(...)
    connection_string: str = Field(default="")
    database: str = Field(default="")
    schema_name: str = Field(default="compliance")

class ConnectorSchema(BaseModel):
    connector: str
    database: str
    schema_name: str
    status: str

class ExportSummarySchema(BaseModel):
    total_exports: int
    by_format: dict[str, int]
    by_data_type: dict[str, int]
    total_rows_exported: int
    total_bytes_exported: int
    active_schedules: int
    configured_connectors: int


@router.post("/exports", response_model=ExportJobSchema, status_code=status.HTTP_201_CREATED, summary="Create export")
async def create_export(request: CreateExportRequest, db: DB) -> ExportJobSchema:
    service = ComplianceExportService(db=db)
    job = await service.create_export(data_type=request.data_type, format=request.format, filters=request.filters)
    return ExportJobSchema(
        id=str(job.id), data_type=job.data_type.value, format=job.format.value,
        status=job.status.value, row_count=job.row_count,
        file_size_bytes=job.file_size_bytes, download_url=job.download_url,
        created_at=job.created_at.isoformat() if job.created_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )

@router.get("/exports", response_model=list[ExportJobSchema], summary="List exports")
async def list_exports(db: DB, export_status: str | None = None, limit: int = 50) -> list[ExportJobSchema]:
    service = ComplianceExportService(db=db)
    s = ExportStatus(export_status) if export_status else None
    jobs = service.list_exports(status=s, limit=limit)
    return [
        ExportJobSchema(
            id=str(j.id), data_type=j.data_type.value, format=j.format.value,
            status=j.status.value, row_count=j.row_count,
            file_size_bytes=j.file_size_bytes, download_url=j.download_url,
            created_at=j.created_at.isoformat() if j.created_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
        ) for j in jobs
    ]

@router.get("/exports/{job_id}", response_model=ExportJobSchema, summary="Get export")
async def get_export(job_id: str, db: DB) -> ExportJobSchema:
    service = ComplianceExportService(db=db)
    job = service.get_export(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    return ExportJobSchema(
        id=str(job.id), data_type=job.data_type.value, format=job.format.value,
        status=job.status.value, row_count=job.row_count,
        file_size_bytes=job.file_size_bytes, download_url=job.download_url,
        created_at=job.created_at.isoformat() if job.created_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )

@router.post("/schedules", response_model=ScheduleSchema, status_code=status.HTTP_201_CREATED, summary="Create schedule")
async def create_schedule(request: CreateScheduleRequest, db: DB) -> ScheduleSchema:
    service = ComplianceExportService(db=db)
    sched = await service.create_schedule(
        name=request.name, data_type=request.data_type, format=request.format,
        schedule_cron=request.schedule_cron, destination=request.destination,
        connector=request.connector,
    )
    return ScheduleSchema(
        id=str(sched.id), name=sched.name, data_type=sched.data_type.value,
        format=sched.format.value, schedule_cron=sched.schedule_cron,
        destination=sched.destination, is_active=sched.is_active,
        created_at=sched.created_at.isoformat() if sched.created_at else None,
    )

@router.get("/schedules", response_model=list[ScheduleSchema], summary="List schedules")
async def list_schedules(db: DB, active_only: bool = True) -> list[ScheduleSchema]:
    service = ComplianceExportService(db=db)
    scheds = service.list_schedules(active_only=active_only)
    return [
        ScheduleSchema(
            id=str(s.id), name=s.name, data_type=s.data_type.value,
            format=s.format.value, schedule_cron=s.schedule_cron,
            destination=s.destination, is_active=s.is_active,
            created_at=s.created_at.isoformat() if s.created_at else None,
        ) for s in scheds
    ]

@router.post("/connectors", response_model=ConnectorSchema, status_code=status.HTTP_201_CREATED, summary="Configure BI connector")
async def configure_connector(request: ConfigureConnectorRequest, db: DB) -> ConnectorSchema:
    service = ComplianceExportService(db=db)
    config = await service.configure_connector(
        connector=request.connector, connection_string=request.connection_string,
        database=request.database, schema=request.schema_name,
    )
    return ConnectorSchema(connector=config.connector.value, database=config.database, schema_name=config.schema, status=config.status)

@router.get("/connectors", response_model=list[ConnectorSchema], summary="List connectors")
async def list_connectors(db: DB) -> list[ConnectorSchema]:
    service = ComplianceExportService(db=db)
    conns = service.list_connectors()
    return [ConnectorSchema(connector=c.connector.value, database=c.database, schema_name=c.schema, status=c.status) for c in conns]

@router.get("/summary", response_model=ExportSummarySchema, summary="Get export summary")
async def get_summary(db: DB) -> ExportSummarySchema:
    service = ComplianceExportService(db=db)
    s = service.get_summary()
    return ExportSummarySchema(
        total_exports=s.total_exports, by_format=s.by_format, by_data_type=s.by_data_type,
        total_rows_exported=s.total_rows_exported, total_bytes_exported=s.total_bytes_exported,
        active_schedules=s.active_schedules, configured_connectors=s.configured_connectors,
    )
