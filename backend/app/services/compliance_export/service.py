"""Compliance Data Export Service."""

import json
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_export.models import (
    BIConnector,
    BIConnectorConfig,
    ExportDataType,
    ExportFormat,
    ExportJob,
    ExportStatus,
    ExportSummary,
    ScheduledExport,
)


logger = structlog.get_logger()


class ComplianceExportService:
    """Service for exporting compliance data and BI integration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._jobs: dict[str, ExportJob] = {}
        self._schedules: dict[str, ScheduledExport] = {}
        self._connectors: dict[str, BIConnectorConfig] = {}

    async def create_export(
        self,
        data_type: str,
        format: str = "json",
        filters: dict | None = None,
    ) -> ExportJob:
        """Create a new export job."""
        now = datetime.now(UTC)
        job = ExportJob(
            data_type=ExportDataType(data_type),
            format=ExportFormat(format),
            status=ExportStatus.PROCESSING,
            filters=filters or {},
            created_at=now,
        )

        # Generate export data
        data = self._generate_export_data(job.data_type, job.filters)
        job.row_count = len(data)
        job.file_size_bytes = len(json.dumps(data).encode())
        job.download_url = f"/api/v1/compliance-export/download/{job.id}"
        job.status = ExportStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        job.expires_at = now + timedelta(hours=24)

        self._jobs[str(job.id)] = job
        logger.info("Export created", data_type=data_type, format=format, rows=job.row_count)
        return job

    def _generate_export_data(self, data_type: ExportDataType, filters: dict) -> list[dict]:
        """Generate sample export data based on type."""
        generators = {
            ExportDataType.POSTURE_SCORES: self._gen_posture_data,
            ExportDataType.VIOLATIONS: self._gen_violations_data,
            ExportDataType.AUDIT_TRAIL: self._gen_audit_data,
            ExportDataType.REGULATIONS: self._gen_regulations_data,
            ExportDataType.COMPLIANCE_ACTIONS: self._gen_actions_data,
            ExportDataType.FULL_REPORT: self._gen_full_report,
        }
        generator = generators.get(data_type, self._gen_full_report)
        return generator(filters)

    def _gen_posture_data(self, filters: dict) -> list[dict]:
        return [
            {"repo": "org/api-service", "framework": "GDPR", "score": 88.0, "grade": "B+", "date": "2026-02-21"},
            {"repo": "org/api-service", "framework": "HIPAA", "score": 82.0, "grade": "B", "date": "2026-02-21"},
            {"repo": "org/web-app", "framework": "GDPR", "score": 91.0, "grade": "A-", "date": "2026-02-21"},
        ]

    def _gen_violations_data(self, filters: dict) -> list[dict]:
        return [
            {"id": "v-001", "file": "src/api/users.py", "rule": "gdpr-consent", "severity": "high", "framework": "GDPR"},
            {"id": "v-002", "file": "src/payments.py", "rule": "pci-tokenization", "severity": "critical", "framework": "PCI-DSS"},
        ]

    def _gen_audit_data(self, filters: dict) -> list[dict]:
        return [
            {"id": "a-001", "event": "compliance_verified", "actor": "system", "timestamp": "2026-02-21T10:00:00Z"},
            {"id": "a-002", "event": "code_generated", "actor": "copilot", "timestamp": "2026-02-21T11:00:00Z"},
        ]

    def _gen_regulations_data(self, filters: dict) -> list[dict]:
        return [
            {"id": "GDPR", "name": "General Data Protection Regulation", "jurisdiction": "EU", "articles": 99},
            {"id": "HIPAA", "name": "Health Insurance Portability Act", "jurisdiction": "US", "articles": 45},
        ]

    def _gen_actions_data(self, filters: dict) -> list[dict]:
        return [
            {"id": "ca-001", "type": "fix_applied", "repo": "org/api", "framework": "GDPR", "status": "completed"},
        ]

    def _gen_full_report(self, filters: dict) -> list[dict]:
        return (
            self._gen_posture_data(filters)
            + self._gen_violations_data(filters)
            + self._gen_audit_data(filters)
        )

    def get_export(self, job_id: str) -> ExportJob | None:
        return self._jobs.get(job_id)

    def list_exports(self, status: ExportStatus | None = None, limit: int = 50) -> list[ExportJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    async def create_schedule(
        self,
        name: str,
        data_type: str,
        format: str = "json",
        schedule_cron: str = "0 0 * * 1",
        destination: str = "",
        connector: str | None = None,
    ) -> ScheduledExport:
        now = datetime.now(UTC)
        sched = ScheduledExport(
            name=name,
            data_type=ExportDataType(data_type),
            format=ExportFormat(format),
            schedule_cron=schedule_cron,
            destination=destination,
            connector=BIConnector(connector) if connector else None,
            is_active=True,
            created_at=now,
        )
        self._schedules[str(sched.id)] = sched
        logger.info("Export schedule created", name=name, cron=schedule_cron)
        return sched

    def list_schedules(self, active_only: bool = True) -> list[ScheduledExport]:
        scheds = list(self._schedules.values())
        if active_only:
            scheds = [s for s in scheds if s.is_active]
        return scheds

    async def configure_connector(
        self,
        connector: str,
        connection_string: str = "",
        database: str = "",
        schema: str = "compliance",
    ) -> BIConnectorConfig:
        config = BIConnectorConfig(
            connector=BIConnector(connector),
            connection_string=connection_string,
            database=database,
            schema=schema,
            status="configured",
        )
        self._connectors[connector] = config
        logger.info("BI connector configured", connector=connector)
        return config

    def list_connectors(self) -> list[BIConnectorConfig]:
        return list(self._connectors.values())

    def get_summary(self) -> ExportSummary:
        by_format: dict[str, int] = {}
        by_type: dict[str, int] = {}
        total_rows = 0
        total_bytes = 0
        for j in self._jobs.values():
            by_format[j.format.value] = by_format.get(j.format.value, 0) + 1
            by_type[j.data_type.value] = by_type.get(j.data_type.value, 0) + 1
            total_rows += j.row_count
            total_bytes += j.file_size_bytes

        return ExportSummary(
            total_exports=len(self._jobs),
            by_format=by_format,
            by_data_type=by_type,
            total_rows_exported=total_rows,
            total_bytes_exported=total_bytes,
            active_schedules=sum(1 for s in self._schedules.values() if s.is_active),
            configured_connectors=len(self._connectors),
        )
