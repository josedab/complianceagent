"""Regulatory Change Impact Heat Map models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class RiskLevel(str, Enum):
    """Risk level classification for heatmap cells."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    COMPLIANT = "compliant"


class TrendDirection(str, Enum):
    """Trend direction for compliance scores over time."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    RAPIDLY_DEGRADING = "rapidly_degrading"


class ExportFormat(str, Enum):
    """Supported export formats for heatmap visualizations."""

    PNG = "png"
    PDF = "pdf"
    SVG = "svg"
    JSON = "json"


@dataclass
class HeatmapCell:
    """A single cell in the compliance heatmap representing a codebase module."""

    path: str
    module: str
    risk_level: RiskLevel
    compliance_score: float
    violation_count: int
    regulations_affected: list[str]
    last_changed: datetime
    color_hex: str


@dataclass
class HeatmapSnapshot:
    """Point-in-time snapshot of the full compliance heatmap."""

    id: UUID
    org_id: str
    timestamp: datetime
    cells: list[HeatmapCell]
    overall_score: float
    total_violations: int
    framework_overlay: str | None = None


@dataclass
class HeatmapChange:
    """A change detected between two heatmap snapshots."""

    path: str
    old_risk: RiskLevel
    new_risk: RiskLevel
    old_score: float
    new_score: float
    change_reason: str


@dataclass
class TimeTravel:
    """Comparison between two heatmap snapshots (time-travel view)."""

    current: HeatmapSnapshot
    historical: HeatmapSnapshot
    changes: list[HeatmapChange]
    improvements: int
    regressions: int


@dataclass
class HeatmapTimeSeries:
    """Time-series collection of heatmap snapshots."""

    snapshots: list[HeatmapSnapshot]
    period_start: datetime
    period_end: datetime
    granularity: str
    trend: TrendDirection
    score_change: float


@dataclass
class RiskForecast:
    """Predictive risk forecast for an organization."""

    id: UUID
    org_id: str
    forecast_date: datetime
    predicted_violations: int
    predicted_score: float
    confidence_pct: float
    risk_factors: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class HeatmapExport:
    """Exported heatmap artifact."""

    id: UUID
    format: ExportFormat
    content_url: str
    generated_at: datetime
    title: str
    description: str


@dataclass
class HeatmapFilter:
    """Filter criteria for heatmap queries."""

    regulations: list[str] | None = None
    modules: list[str] | None = None
    min_risk: RiskLevel | None = None
    framework: str | None = None


@dataclass
class ModuleRiskTrend:
    """Risk trend data for a single module over time."""

    module: str
    scores: list[float]
    timestamps: list[datetime]
    trend: TrendDirection
    prediction_30d: float
