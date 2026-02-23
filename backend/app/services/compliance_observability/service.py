"""Compliance Observability Pipeline Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_observability.models import (
    AlertSeverity,
    ComplianceAlert,
    ComplianceMetric,
    ExporterConfig,
    ExporterType,
    MetricType,
    ObservabilityDashboard,
    PipelineStats,
)


logger = structlog.get_logger()

_COMPLIANCE_METRICS: list[ComplianceMetric] = [
    ComplianceMetric(name="compliance.posture.score", metric_type=MetricType.GAUGE, value=85.0, unit="percent", description="Overall compliance posture score", labels={"org": "default"}),
    ComplianceMetric(name="compliance.violations.total", metric_type=MetricType.COUNTER, value=42, unit="count", description="Total compliance violations detected", labels={"org": "default"}),
    ComplianceMetric(name="compliance.remediation.time", metric_type=MetricType.HISTOGRAM, value=4.2, unit="hours", description="Time to remediate violations", labels={"org": "default"}),
    ComplianceMetric(name="compliance.scan.duration", metric_type=MetricType.HISTOGRAM, value=12.5, unit="seconds", description="Compliance scan duration", labels={"org": "default"}),
    ComplianceMetric(name="compliance.frameworks.covered", metric_type=MetricType.GAUGE, value=8, unit="count", description="Number of compliance frameworks covered", labels={"org": "default"}),
    ComplianceMetric(name="compliance.evidence.freshness", metric_type=MetricType.GAUGE, value=95.0, unit="percent", description="Evidence freshness percentage", labels={"org": "default"}),
    ComplianceMetric(name="compliance.drift.events", metric_type=MetricType.COUNTER, value=7, unit="count", description="Compliance drift events in period", labels={"org": "default"}),
]

_PREBUILT_DASHBOARDS: dict[ExporterType, ObservabilityDashboard] = {
    ExporterType.GRAFANA: ObservabilityDashboard(
        name="ComplianceAgent Overview",
        exporter_type=ExporterType.GRAFANA,
        panels=[
            {"title": "Posture Score", "type": "gauge", "metric": "compliance.posture.score"},
            {"title": "Violations Trend", "type": "timeseries", "metric": "compliance.violations.total"},
            {"title": "Remediation Time", "type": "histogram", "metric": "compliance.remediation.time"},
            {"title": "Framework Coverage", "type": "stat", "metric": "compliance.frameworks.covered"},
        ],
    ),
    ExporterType.DATADOG: ObservabilityDashboard(
        name="ComplianceAgent Overview",
        exporter_type=ExporterType.DATADOG,
        panels=[
            {"title": "Compliance Score", "type": "query_value", "metric": "compliance.posture.score"},
            {"title": "Violation Count", "type": "timeseries", "metric": "compliance.violations.total"},
            {"title": "Drift Events", "type": "event_stream", "metric": "compliance.drift.events"},
        ],
    ),
}


class ComplianceObservabilityService:
    """OTel-native compliance metrics pipeline with exporter integrations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._metrics: list[ComplianceMetric] = list(_COMPLIANCE_METRICS)
        self._exporters: dict[str, ExporterConfig] = {}
        self._alerts: list[ComplianceAlert] = []
        self._emit_count = 0

    async def emit_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "gauge",
        labels: dict[str, str] | None = None,
        unit: str = "",
    ) -> ComplianceMetric:
        metric = ComplianceMetric(
            name=name,
            metric_type=MetricType(metric_type),
            value=value,
            labels=labels or {},
            unit=unit,
            recorded_at=datetime.now(UTC),
        )
        self._metrics.append(metric)
        self._emit_count += 1
        await self._check_alert_thresholds(metric)
        return metric

    async def _check_alert_thresholds(self, metric: ComplianceMetric) -> None:
        if metric.name == "compliance.posture.score" and metric.value < 70:
            self._alerts.append(ComplianceAlert(
                metric_name=metric.name,
                condition="score < 70",
                threshold=70.0,
                current_value=metric.value,
                severity=AlertSeverity.CRITICAL,
                message=f"Compliance posture score dropped to {metric.value}%",
                fired_at=datetime.now(UTC),
            ))
        elif metric.name == "compliance.violations.total" and metric.value > 100:
            self._alerts.append(ComplianceAlert(
                metric_name=metric.name,
                condition="violations > 100",
                threshold=100,
                current_value=metric.value,
                severity=AlertSeverity.WARNING,
                message=f"Violation count exceeded threshold: {int(metric.value)}",
                fired_at=datetime.now(UTC),
            ))

    def list_metrics(self, name_prefix: str | None = None) -> list[ComplianceMetric]:
        if name_prefix:
            return [m for m in self._metrics if m.name.startswith(name_prefix)]
        return list(self._metrics)

    async def configure_exporter(
        self,
        exporter_type: str,
        endpoint: str = "",
        api_key: str = "",
        labels: dict[str, str] | None = None,
        flush_interval: int = 60,
    ) -> ExporterConfig:
        config = ExporterConfig(
            exporter_type=ExporterType(exporter_type),
            endpoint=endpoint,
            api_key=api_key,
            labels=labels or {},
            flush_interval_seconds=flush_interval,
            configured_at=datetime.now(UTC),
        )
        self._exporters[exporter_type] = config
        logger.info("Exporter configured", exporter_type=exporter_type, endpoint=endpoint)
        return config

    def list_exporters(self) -> list[ExporterConfig]:
        return list(self._exporters.values())

    def get_dashboard(self, exporter_type: str) -> ObservabilityDashboard | None:
        return _PREBUILT_DASHBOARDS.get(ExporterType(exporter_type))

    def list_dashboards(self) -> list[ObservabilityDashboard]:
        return list(_PREBUILT_DASHBOARDS.values())

    def list_alerts(self, active_only: bool = True) -> list[ComplianceAlert]:
        if active_only:
            return [a for a in self._alerts if not a.resolved_at]
        return list(self._alerts)

    async def resolve_alert(self, alert_id: UUID) -> ComplianceAlert | None:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved_at = datetime.now(UTC)
                return alert
        return None

    def get_stats(self) -> PipelineStats:
        by_type: dict[str, int] = {}
        for m in self._metrics:
            by_type[m.metric_type.value] = by_type.get(m.metric_type.value, 0) + 1
        return PipelineStats(
            metrics_emitted=self._emit_count,
            exporters_configured=len(self._exporters),
            active_alerts=sum(1 for a in self._alerts if not a.resolved_at),
            metrics_by_type=by_type,
            last_flush_at=datetime.now(UTC),
        )
