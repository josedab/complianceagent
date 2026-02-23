"""Compliance Observability Pipeline models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class MetricType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"


class ExporterType(str, Enum):
    DATADOG = "datadog"
    GRAFANA = "grafana"
    SPLUNK = "splunk"
    NEW_RELIC = "new_relic"
    PROMETHEUS = "prometheus"
    OTEL_COLLECTOR = "otel_collector"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ComplianceMetric:
    name: str = ""
    metric_type: MetricType = MetricType.GAUGE
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""
    recorded_at: datetime | None = None


@dataclass
class ExporterConfig:
    id: UUID = field(default_factory=uuid4)
    exporter_type: ExporterType = ExporterType.PROMETHEUS
    endpoint: str = ""
    api_key: str = ""
    enabled: bool = True
    labels: dict[str, str] = field(default_factory=dict)
    flush_interval_seconds: int = 60
    configured_at: datetime | None = None


@dataclass
class ComplianceAlert:
    id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    condition: str = ""
    threshold: float = 0.0
    current_value: float = 0.0
    severity: AlertSeverity = AlertSeverity.WARNING
    message: str = ""
    correlated_incidents: list[str] = field(default_factory=list)
    fired_at: datetime | None = None
    resolved_at: datetime | None = None


@dataclass
class ObservabilityDashboard:
    name: str = ""
    exporter_type: ExporterType = ExporterType.GRAFANA
    panels: list[dict[str, Any]] = field(default_factory=list)
    url: str = ""


@dataclass
class PipelineStats:
    metrics_emitted: int = 0
    exporters_configured: int = 0
    active_alerts: int = 0
    metrics_by_type: dict[str, int] = field(default_factory=dict)
    export_errors: int = 0
    last_flush_at: datetime | None = None
