"""Telemetry mesh service for monitoring, SLO compliance, and anomaly detection."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.telemetry_mesh.models import (
    AnomalyType,
    ComplianceSLO,
    DetectedAnomaly,
    ServiceTelemetry,
    ServiceTier,
    SLOType,
    TelemetryStats,
)


logger = structlog.get_logger()


class TelemetryMeshService:
    """Service for monitoring service telemetry, SLOs, and anomaly detection."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._services: dict[str, ServiceTelemetry] = {}
        self._slos: dict[UUID, ComplianceSLO] = {}
        self._anomalies: dict[UUID, DetectedAnomaly] = {}
        self._seed_services()

    def _seed_services(self) -> None:
        """Seed initial services with metrics."""
        seed_data = [
            ("auth-service", ServiceTier.critical, {"availability": 99.95, "latency_ms": 45.0, "error_rate": 0.02, "rps": 1200.0}),
            ("policy-engine", ServiceTier.critical, {"availability": 99.99, "latency_ms": 120.0, "error_rate": 0.01, "rps": 800.0}),
            ("evidence-collector", ServiceTier.standard, {"availability": 99.8, "latency_ms": 250.0, "error_rate": 0.05, "rps": 300.0}),
            ("audit-logger", ServiceTier.critical, {"availability": 99.97, "latency_ms": 30.0, "error_rate": 0.005, "rps": 2000.0}),
            ("report-generator", ServiceTier.standard, {"availability": 99.5, "latency_ms": 1500.0, "error_rate": 0.08, "rps": 50.0}),
            ("notification-service", ServiceTier.standard, {"availability": 99.7, "latency_ms": 200.0, "error_rate": 0.03, "rps": 150.0}),
            ("data-pipeline", ServiceTier.background, {"availability": 98.5, "latency_ms": 5000.0, "error_rate": 0.1, "rps": 20.0}),
            ("backup-service", ServiceTier.background, {"availability": 99.0, "latency_ms": 3000.0, "error_rate": 0.02, "rps": 5.0}),
        ]
        for name, tier, metrics in seed_data:
            health = self._compute_health(metrics)
            self._services[name] = ServiceTelemetry(
                service_name=name,
                tier=tier,
                metrics=metrics,
                health_score=health,
                last_heartbeat=datetime.now(UTC),
            )

    def _compute_health(self, metrics: dict[str, float]) -> float:
        """Compute health score from metrics."""
        score = 1.0
        availability = metrics.get("availability", 100.0)
        score -= max(0, (100.0 - availability) * 0.1)
        error_rate = metrics.get("error_rate", 0.0)
        score -= min(error_rate * 5, 0.5)
        latency = metrics.get("latency_ms", 0.0)
        if latency > 1000:
            score -= 0.2
        elif latency > 500:
            score -= 0.1
        return round(max(0.0, min(1.0, score)), 3)

    async def register_service(self, name: str, tier: ServiceTier) -> ServiceTelemetry:
        """Register a new service for monitoring."""
        service = ServiceTelemetry(
            service_name=name,
            tier=tier,
            last_heartbeat=datetime.now(UTC),
        )
        self._services[name] = service
        logger.info("Service registered", service=name, tier=tier.value)
        return service

    async def report_metrics(self, service_name: str, metrics: dict[str, float]) -> ServiceTelemetry:
        """Report metrics for a service and update health score."""
        if service_name not in self._services:
            raise ValueError(f"Service not found: {service_name}")
        service = self._services[service_name]
        service.metrics.update(metrics)
        service.health_score = self._compute_health(service.metrics)
        service.last_heartbeat = datetime.now(UTC)
        logger.info("Metrics reported", service=service_name, health=service.health_score)
        return service

    async def define_slo(
        self,
        name: str,
        slo_type: SLOType,
        target: float,
        window_hours: int = 24,
    ) -> ComplianceSLO:
        """Define a new SLO."""
        slo = ComplianceSLO(
            id=uuid4(),
            name=name,
            slo_type=slo_type,
            target=target,
            window_hours=window_hours,
            last_evaluated=datetime.now(UTC),
        )
        self._slos[slo.id] = slo
        logger.info("SLO defined", name=name, type=slo_type.value, target=target)
        return slo

    async def evaluate_slos(self) -> list[ComplianceSLO]:
        """Evaluate all SLOs against current metrics."""
        evaluated = []
        for slo in self._slos.values():
            current_values = []
            for service in self._services.values():
                metric_key = slo.slo_type.value
                if metric_key in service.metrics:
                    current_values.append(service.metrics[metric_key])
            if current_values:
                slo.current = sum(current_values) / len(current_values)
            if slo.slo_type in (SLOType.error_rate, SLOType.latency):
                slo.in_compliance = slo.current <= slo.target
            else:
                slo.in_compliance = slo.current >= slo.target
            slo.last_evaluated = datetime.now(UTC)
            evaluated.append(slo)
        logger.info("SLOs evaluated", total=len(evaluated))
        return evaluated

    async def detect_anomalies(self, service_name: str) -> list[DetectedAnomaly]:
        """Detect anomalies for a service using deviation thresholds."""
        if service_name not in self._services:
            raise ValueError(f"Service not found: {service_name}")
        service = self._services[service_name]
        detected = []
        thresholds = {
            "availability": (99.0, AnomalyType.drop),
            "error_rate": (0.05, AnomalyType.spike),
            "latency_ms": (1000.0, AnomalyType.spike),
            "rps": (10.0, AnomalyType.drop),
        }
        for metric_name, value in service.metrics.items():
            if metric_name not in thresholds:
                continue
            threshold, anomaly_type = thresholds[metric_name]
            is_anomaly = False
            if (anomaly_type == AnomalyType.spike and value > threshold) or (anomaly_type == AnomalyType.drop and value < threshold):
                is_anomaly = True
            if is_anomaly:
                deviation = abs(value - threshold) / max(threshold, 0.001) * 100
                severity = "critical" if deviation > 50 else "high" if deviation > 20 else "medium"
                anomaly = DetectedAnomaly(
                    id=uuid4(),
                    service_name=service_name,
                    anomaly_type=anomaly_type,
                    metric_name=metric_name,
                    expected_value=threshold,
                    actual_value=value,
                    deviation_pct=round(deviation, 2),
                    severity=severity,
                    detected_at=datetime.now(UTC),
                )
                self._anomalies[anomaly.id] = anomaly
                detected.append(anomaly)
        logger.info("Anomaly detection", service=service_name, found=len(detected))
        return detected

    async def resolve_anomaly(self, anomaly_id: UUID) -> DetectedAnomaly:
        """Resolve a detected anomaly."""
        if anomaly_id not in self._anomalies:
            raise ValueError(f"Anomaly not found: {anomaly_id}")
        anomaly = self._anomalies[anomaly_id]
        anomaly.resolved = True
        logger.info("Anomaly resolved", anomaly_id=str(anomaly_id))
        return anomaly

    async def list_services(self) -> list[ServiceTelemetry]:
        """List all monitored services."""
        return list(self._services.values())

    async def list_slos(self) -> list[ComplianceSLO]:
        """List all defined SLOs."""
        return list(self._slos.values())

    async def list_anomalies(self, active_only: bool = False) -> list[DetectedAnomaly]:
        """List detected anomalies."""
        anomalies = list(self._anomalies.values())
        if active_only:
            anomalies = [a for a in anomalies if not a.resolved]
        return anomalies

    async def get_stats(self) -> TelemetryStats:
        """Get aggregate telemetry statistics."""
        services = list(self._services.values())
        slos = list(self._slos.values())
        anomalies = list(self._anomalies.values())
        avg_health = (
            sum(s.health_score for s in services) / len(services) if services else 0.0
        )
        return TelemetryStats(
            services_monitored=len(services),
            slos_defined=len(slos),
            slos_in_compliance=sum(1 for s in slos if s.in_compliance),
            anomalies_detected=len(anomalies),
            anomalies_active=sum(1 for a in anomalies if not a.resolved),
            avg_health_score=round(avg_health, 3),
        )
