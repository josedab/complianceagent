"""Compliance Data Export models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class ExportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportDataType(str, Enum):
    POSTURE_SCORES = "posture_scores"
    VIOLATIONS = "violations"
    AUDIT_TRAIL = "audit_trail"
    REGULATIONS = "regulations"
    COMPLIANCE_ACTIONS = "compliance_actions"
    FULL_REPORT = "full_report"


class BIConnector(str, Enum):
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"
    LOOKER = "looker"
    POWERBI = "powerbi"
    TABLEAU = "tableau"


@dataclass
class ExportJob:
    id: UUID = field(default_factory=uuid4)
    data_type: ExportDataType = ExportDataType.FULL_REPORT
    format: ExportFormat = ExportFormat.JSON
    status: ExportStatus = ExportStatus.PENDING
    filters: dict[str, Any] = field(default_factory=dict)
    row_count: int = 0
    file_size_bytes: int = 0
    download_url: str = ""
    error_message: str = ""
    created_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass
class ScheduledExport:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    data_type: ExportDataType = ExportDataType.FULL_REPORT
    format: ExportFormat = ExportFormat.JSON
    schedule_cron: str = "0 0 * * 1"
    destination: str = ""
    connector: BIConnector | None = None
    is_active: bool = True
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime | None = None


@dataclass
class BIConnectorConfig:
    connector: BIConnector = BIConnector.SNOWFLAKE
    connection_string: str = ""
    database: str = ""
    schema: str = "compliance"
    table_prefix: str = "ca_"
    sync_frequency: str = "daily"
    last_sync_at: datetime | None = None
    status: str = "configured"


@dataclass
class ExportSummary:
    total_exports: int = 0
    by_format: dict[str, int] = field(default_factory=dict)
    by_data_type: dict[str, int] = field(default_factory=dict)
    total_rows_exported: int = 0
    total_bytes_exported: int = 0
    active_schedules: int = 0
    configured_connectors: int = 0
