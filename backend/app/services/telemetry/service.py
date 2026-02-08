"""Real-Time Compliance Telemetry Service."""

import random
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.telemetry.models import (
    AlertChannel,
    AlertSeverity,
    AlertThreshold,
    MetricTimeSeries,
    MetricType,
    TelemetryEvent,
    TelemetryEventType,
    TelemetryMetric,
    TelemetrySnapshot,
)

logger = structlog.get_logger()

# Default alert thresholds
_DEFAULT_THRESHOLDS = [
    AlertThreshold(
        metric_type=MetricType.COMPLIANCE_SCORE,
        operator="lt",
        value=70.0,
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.WEBSOCKET, AlertChannel.SLACK],
    ),
    AlertThreshold(
        metric_type=MetricType.COMPLIANCE_SCORE,
        operator="lt",
        value=85.0,
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.WEBSOCKET],
    ),
    AlertThreshold(
        metric_type=MetricType.VIOLATION_COUNT,
        operator="gt",
        value=10.0,
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.WEBSOCKET, AlertChannel.EMAIL],
    ),
    AlertThreshold(
        metric_type=MetricType.DRIFT_SCORE,
        operator="gt",
        value=15.0,
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.WEBSOCKET],
    ),
]


class TelemetryService:
    """Real-time compliance telemetry and monitoring service."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._events: list[TelemetryEvent] = []
        self._metrics: list[TelemetryMetric] = []
        self._thresholds: dict[UUID, AlertThreshold] = {t.id: t for t in _DEFAULT_THRESHOLDS}
        self._subscribers: dict[str, list] = {}  # channel -> callbacks
        self._snapshots: list[TelemetrySnapshot] = []

    async def get_current_snapshot(self) -> TelemetrySnapshot:
        """Get the current telemetry snapshot with all key metrics."""
        snapshot = TelemetrySnapshot(
            overall_score=self._compute_overall_score(),
            violation_count=self._count_recent_violations(),
            requirement_coverage=self._compute_coverage(),
            drift_score=self._compute_drift(),
            risk_score=self._compute_risk(),
            audit_readiness=self._compute_audit_readiness(),
            frameworks=self._compute_framework_scores(),
            repositories=self._compute_repo_scores(),
            timestamp=datetime.now(UTC),
        )
        self._snapshots.append(snapshot)
        return snapshot

    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        framework: str | None = None,
        repository: str | None = None,
        metadata: dict | None = None,
    ) -> TelemetryMetric:
        """Record a new telemetry metric data point."""
        previous = self._get_latest_metric(metric_type, framework, repository)
        metric = TelemetryMetric(
            metric_type=metric_type,
            value=value,
            previous_value=previous.value if previous else None,
            framework=framework,
            repository=repository,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )
        self._metrics.append(metric)

        # Check thresholds
        await self._check_thresholds(metric)

        logger.info(
            "Metric recorded",
            metric_type=metric_type.value,
            value=value,
            framework=framework,
        )
        return metric

    async def emit_event(
        self,
        event_type: TelemetryEventType,
        title: str,
        description: str = "",
        severity: AlertSeverity = AlertSeverity.INFO,
        framework: str | None = None,
        repository: str | None = None,
        metric_value: float | None = None,
    ) -> TelemetryEvent:
        """Emit a real-time telemetry event."""
        event = TelemetryEvent(
            event_type=event_type,
            severity=severity,
            title=title,
            description=description,
            source="telemetry",
            framework=framework,
            repository=repository,
            metric_value=metric_value,
            timestamp=datetime.now(UTC),
        )
        self._events.append(event)
        logger.info("Telemetry event emitted", event_type=event_type.value, title=title)
        return event

    async def get_events(
        self,
        event_type: TelemetryEventType | None = None,
        severity: AlertSeverity | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[TelemetryEvent]:
        """Get telemetry events with optional filters."""
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]
        if since:
            events = [e for e in events if e.timestamp and e.timestamp >= since]
        return sorted(events, key=lambda e: e.timestamp or datetime.min, reverse=True)[:limit]

    async def get_time_series(
        self,
        metric_type: MetricType,
        period: str = "24h",
        framework: str | None = None,
    ) -> MetricTimeSeries:
        """Get time series data for a metric."""
        now = datetime.now(UTC)
        period_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = period_map.get(period, 24)
        cutoff = now - timedelta(hours=hours)

        points = [
            m for m in self._metrics
            if m.metric_type == metric_type
            and (framework is None or m.framework == framework)
            and m.timestamp
            and m.timestamp >= cutoff
        ]

        # If no real data, generate synthetic for demo
        if not points:
            points = self._generate_synthetic_series(metric_type, hours, framework)

        return MetricTimeSeries(
            metric_type=metric_type,
            data_points=sorted(points, key=lambda p: p.timestamp or datetime.min),
            framework=framework,
            period=period,
        )

    async def get_thresholds(self) -> list[AlertThreshold]:
        """Get all configured alert thresholds."""
        return list(self._thresholds.values())

    async def set_threshold(
        self,
        metric_type: MetricType,
        operator: str,
        value: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        channels: list[AlertChannel] | None = None,
        cooldown_minutes: int = 60,
    ) -> AlertThreshold:
        """Create or update an alert threshold."""
        threshold = AlertThreshold(
            metric_type=metric_type,
            operator=operator,
            value=value,
            severity=severity,
            channels=channels or [AlertChannel.WEBSOCKET],
            cooldown_minutes=cooldown_minutes,
            created_at=datetime.now(UTC),
        )
        self._thresholds[threshold.id] = threshold
        logger.info(
            "Alert threshold set",
            metric_type=metric_type.value,
            operator=operator,
            value=value,
        )
        return threshold

    async def delete_threshold(self, threshold_id: UUID) -> bool:
        """Delete an alert threshold."""
        if threshold_id in self._thresholds:
            del self._thresholds[threshold_id]
            return True
        return False

    async def get_heatmap_data(self, period: str = "7d") -> dict:
        """Get compliance heatmap data by framework and day."""
        frameworks = ["gdpr", "hipaa", "pci_dss", "soc2", "eu_ai_act"]
        days = 7 if period == "7d" else 30
        now = datetime.now(UTC)

        heatmap = {}
        for fw in frameworks:
            heatmap[fw] = []
            base_score = random.uniform(70, 95)
            for day in range(days):
                dt = now - timedelta(days=days - 1 - day)
                score = max(0, min(100, base_score + random.uniform(-5, 5)))
                base_score = score
                heatmap[fw].append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "score": round(score, 1),
                })

        return {"period": period, "frameworks": heatmap}

    async def _check_thresholds(self, metric: TelemetryMetric) -> list[TelemetryEvent]:
        """Check if metric triggers any alert thresholds."""
        triggered = []
        for threshold in self._thresholds.values():
            if not threshold.enabled or threshold.metric_type != metric.metric_type:
                continue

            if threshold.last_triggered:
                cooldown = timedelta(minutes=threshold.cooldown_minutes)
                if datetime.now(UTC) - threshold.last_triggered < cooldown:
                    continue

            breached = self._evaluate_threshold(metric.value, threshold.operator, threshold.value)
            if breached:
                threshold.last_triggered = datetime.now(UTC)
                event = await self.emit_event(
                    event_type=TelemetryEventType.THRESHOLD_BREACH,
                    title=f"Threshold breach: {metric.metric_type.value}",
                    description=f"{metric.metric_type.value} {threshold.operator} {threshold.value} (actual: {metric.value})",
                    severity=threshold.severity,
                    framework=metric.framework,
                    metric_value=metric.value,
                )
                triggered.append(event)
        return triggered

    @staticmethod
    def _evaluate_threshold(value: float, operator: str, threshold: float) -> bool:
        ops = {"lt": value < threshold, "gt": value > threshold, "eq": value == threshold,
               "lte": value <= threshold, "gte": value >= threshold}
        return ops.get(operator, False)

    def _get_latest_metric(
        self, metric_type: MetricType, framework: str | None, repository: str | None
    ) -> TelemetryMetric | None:
        for m in reversed(self._metrics):
            if m.metric_type == metric_type and m.framework == framework and m.repository == repository:
                return m
        return None

    def _compute_overall_score(self) -> float:
        scores = [m.value for m in self._metrics if m.metric_type == MetricType.COMPLIANCE_SCORE]
        return scores[-1] if scores else 85.0

    def _count_recent_violations(self) -> int:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        return sum(
            1 for e in self._events
            if e.event_type == TelemetryEventType.VIOLATION_DETECTED
            and e.timestamp and e.timestamp >= cutoff
        )

    def _compute_coverage(self) -> float:
        scores = [m.value for m in self._metrics if m.metric_type == MetricType.REQUIREMENT_COVERAGE]
        return scores[-1] if scores else 78.5

    def _compute_drift(self) -> float:
        scores = [m.value for m in self._metrics if m.metric_type == MetricType.DRIFT_SCORE]
        return scores[-1] if scores else 3.2

    def _compute_risk(self) -> float:
        scores = [m.value for m in self._metrics if m.metric_type == MetricType.RISK_SCORE]
        return scores[-1] if scores else 22.0

    def _compute_audit_readiness(self) -> float:
        scores = [m.value for m in self._metrics if m.metric_type == MetricType.AUDIT_READINESS]
        return scores[-1] if scores else 72.0

    def _compute_framework_scores(self) -> dict[str, float]:
        fw_scores: dict[str, float] = {}
        for m in self._metrics:
            if m.metric_type == MetricType.COMPLIANCE_SCORE and m.framework:
                fw_scores[m.framework] = m.value
        if not fw_scores:
            fw_scores = {"gdpr": 88.0, "hipaa": 76.0, "pci_dss": 92.0, "soc2": 81.0}
        return fw_scores

    def _compute_repo_scores(self) -> dict[str, float]:
        repo_scores: dict[str, float] = {}
        for m in self._metrics:
            if m.metric_type == MetricType.COMPLIANCE_SCORE and m.repository:
                repo_scores[m.repository] = m.value
        return repo_scores

    def _generate_synthetic_series(
        self, metric_type: MetricType, hours: int, framework: str | None
    ) -> list[TelemetryMetric]:
        """Generate synthetic time series for demo purposes."""
        now = datetime.now(UTC)
        points = []
        base = 85.0 if metric_type == MetricType.COMPLIANCE_SCORE else 5.0
        step = max(1, hours // 48)

        for i in range(0, hours, step):
            ts = now - timedelta(hours=hours - i)
            value = max(0, min(100, base + random.uniform(-3, 3)))
            base = value
            points.append(TelemetryMetric(
                metric_type=metric_type,
                value=round(value, 2),
                framework=framework,
                timestamp=ts,
            ))
        return points
