"""Telemetry mesh models for service monitoring and SLO compliance."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class SLOType(str, Enum):
    """Types of Service Level Objectives."""

    availability = "availability"
    latency = "latency"
    error_rate = "error_rate"
    throughput = "throughput"


class AnomalyType(str, Enum):
    """Types of detected anomalies."""

    spike = "spike"
    drop = "drop"
    trend_change = "trend_change"
    outlier = "outlier"


class ServiceTier(str, Enum):
    """Service criticality tiers."""

    critical = "critical"
    standard = "standard"
    background = "background"


@dataclass
class ServiceTelemetry:
    """Telemetry data for a monitored service."""

    service_name: str
    tier: ServiceTier
    metrics: dict[str, float] = field(default_factory=dict)
    health_score: float = 1.0
    last_heartbeat: datetime | None = None


@dataclass
class ComplianceSLO:
    """A Service Level Objective for compliance monitoring."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slo_type: SLOType = SLOType.availability
    target: float = 0.0
    current: float = 0.0
    window_hours: int = 24
    in_compliance: bool = True
    last_evaluated: datetime | None = None


@dataclass
class DetectedAnomaly:
    """An anomaly detected in service telemetry."""

    id: UUID = field(default_factory=uuid4)
    service_name: str = ""
    anomaly_type: AnomalyType = AnomalyType.spike
    metric_name: str = ""
    expected_value: float = 0.0
    actual_value: float = 0.0
    deviation_pct: float = 0.0
    severity: str = "medium"
    detected_at: datetime | None = None
    resolved: bool = False


@dataclass
class TelemetryStats:
    """Aggregate telemetry statistics."""

    services_monitored: int = 0
    slos_defined: int = 0
    slos_in_compliance: int = 0
    anomalies_detected: int = 0
    anomalies_active: int = 0
    avg_health_score: float = 0.0
