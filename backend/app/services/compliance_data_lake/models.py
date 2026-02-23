"""Multi-Tenant Compliance Data Lake models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EventCategory(str, Enum):
    SCORE_CHANGE = "score_change"
    VIOLATION = "violation"
    REMEDIATION = "remediation"
    SCAN = "scan"
    AUDIT = "audit"
    REGULATION_CHANGE = "regulation_change"
    POLICY_UPDATE = "policy_update"


class AggregationPeriod(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class ComplianceEvent:
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    category: EventCategory = EventCategory.SCORE_CHANGE
    source_service: str = ""
    repo: str = ""
    framework: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass
class TimeSeriesPoint:
    timestamp: str = ""
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class AnalyticsQuery:
    id: UUID = field(default_factory=uuid4)
    category: EventCategory | None = None
    tenant_id: str = ""
    framework: str = ""
    period: AggregationPeriod = AggregationPeriod.DAY
    start_date: str = ""
    end_date: str = ""


@dataclass
class AnalyticsResult:
    query_id: UUID = field(default_factory=uuid4)
    time_series: list[TimeSeriesPoint] = field(default_factory=list)
    aggregations: dict[str, Any] = field(default_factory=dict)
    total_events: int = 0
    execution_time_ms: float = 0.0


@dataclass
class DataLakeStats:
    total_events: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_tenant: dict[str, int] = field(default_factory=dict)
    oldest_event: datetime | None = None
    newest_event: datetime | None = None
    storage_size_mb: float = 0.0
