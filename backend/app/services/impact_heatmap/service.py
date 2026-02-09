"""Regulatory Change Impact Heat Map service."""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from uuid import uuid4

import structlog

from app.services.impact_heatmap.models import (
    ExportFormat,
    HeatmapCell,
    HeatmapChange,
    HeatmapExport,
    HeatmapFilter,
    HeatmapSnapshot,
    HeatmapTimeSeries,
    ModuleRiskTrend,
    RiskForecast,
    RiskLevel,
    TimeTravel,
    TrendDirection,
)


logger = structlog.get_logger()

# Realistic sample modules with baseline risk profiles
_SAMPLE_MODULES: list[dict] = [
    {"path": "src/auth", "module": "Authentication", "base_score": 92.0, "regs": ["SOC2", "ISO27001"]},
    {"path": "src/payments", "module": "Payment Processing", "base_score": 65.0, "regs": ["PCI-DSS", "SOX"]},
    {"path": "src/data/storage", "module": "Data Storage", "base_score": 78.0, "regs": ["GDPR", "CCPA"]},
    {"path": "src/api/gateway", "module": "API Gateway", "base_score": 85.0, "regs": ["SOC2", "NIST"]},
    {"path": "src/ml/models", "module": "ML Models", "base_score": 55.0, "regs": ["EU-AI-Act", "NIST-AI"]},
    {"path": "src/ml/training", "module": "ML Training Pipeline", "base_score": 60.0, "regs": ["EU-AI-Act"]},
    {"path": "src/data/pipelines", "module": "Data Pipelines", "base_score": 72.0, "regs": ["GDPR", "HIPAA"]},
    {"path": "src/infrastructure/k8s", "module": "Kubernetes Infra", "base_score": 88.0, "regs": ["SOC2", "FedRAMP"]},
    {"path": "src/logging", "module": "Audit Logging", "base_score": 95.0, "regs": ["SOC2", "HIPAA", "SOX"]},
    {"path": "src/encryption", "module": "Encryption Services", "base_score": 90.0, "regs": ["PCI-DSS", "HIPAA"]},
    {"path": "src/user/consent", "module": "User Consent Manager", "base_score": 70.0, "regs": ["GDPR", "CCPA", "LGPD"]},
    {"path": "src/data/export", "module": "Data Export/Portability", "base_score": 68.0, "regs": ["GDPR", "CCPA"]},
    {"path": "src/notifications", "module": "Notification Service", "base_score": 82.0, "regs": ["CAN-SPAM", "GDPR"]},
    {"path": "src/vendor/integrations", "module": "Third-Party Integrations", "base_score": 58.0, "regs": ["SOC2", "GDPR"]},
    {"path": "src/reporting", "module": "Compliance Reporting", "base_score": 87.0, "regs": ["SOX", "SOC2"]},
    {"path": "src/access/rbac", "module": "Role-Based Access Control", "base_score": 91.0, "regs": ["SOC2", "HIPAA"]},
    {"path": "src/data/anonymization", "module": "Data Anonymization", "base_score": 63.0, "regs": ["GDPR", "HIPAA"]},
    {"path": "src/backup", "module": "Backup & Recovery", "base_score": 80.0, "regs": ["SOC2", "ISO27001"]},
    {"path": "src/ci/scanning", "module": "CI Security Scanning", "base_score": 76.0, "regs": ["NIST", "SOC2"]},
    {"path": "src/mobile/sdk", "module": "Mobile SDK", "base_score": 50.0, "regs": ["GDPR", "CCPA", "EU-AI-Act"]},
]

_RISK_COLORS: dict[RiskLevel, str] = {
    RiskLevel.CRITICAL: "#DC2626",
    RiskLevel.HIGH: "#F97316",
    RiskLevel.MEDIUM: "#EAB308",
    RiskLevel.LOW: "#22C55E",
    RiskLevel.COMPLIANT: "#16A34A",
}


class ImpactHeatmapService:
    """Generates compliance risk heatmaps with time-travel and forecasting."""

    def __init__(self, db, copilot_client=None):
        self.db = db
        self.copilot_client = copilot_client
        self._rng = random.Random(42)

    async def get_current_heatmap(
        self,
        org_id: str,
        filters: HeatmapFilter | None = None,
    ) -> HeatmapSnapshot:
        """Get the current compliance heatmap for an organization."""
        snapshot = self._generate_snapshot(org_id)

        if filters:
            snapshot = self._apply_filters(snapshot, filters)

        logger.info(
            "current_heatmap_generated",
            org_id=org_id,
            cells=len(snapshot.cells),
            overall_score=snapshot.overall_score,
        )
        return snapshot

    async def get_heatmap_at(
        self,
        org_id: str,
        timestamp: datetime,
    ) -> HeatmapSnapshot:
        """Get the compliance heatmap at a specific historical point in time."""
        days_ago = (datetime.utcnow() - timestamp).days
        snapshot = self._generate_snapshot(org_id, days_offset=-days_ago)
        snapshot.timestamp = timestamp

        logger.info(
            "historical_heatmap_generated",
            org_id=org_id,
            timestamp=timestamp.isoformat(),
            days_ago=days_ago,
        )
        return snapshot

    async def get_time_series(
        self,
        org_id: str,
        period_days: int = 90,
        granularity: str = "daily",
    ) -> HeatmapTimeSeries:
        """Get time-series heatmap data for the slider visualization."""
        now = datetime.utcnow()
        step_days = {"daily": 1, "weekly": 7, "monthly": 30}.get(granularity, 1)
        num_snapshots = max(1, period_days // step_days)

        snapshots: list[HeatmapSnapshot] = []
        for i in range(num_snapshots):
            offset = -(period_days - i * step_days)
            snap = self._generate_snapshot(org_id, days_offset=offset)
            snap.timestamp = now + timedelta(days=offset)
            snapshots.append(snap)

        scores = [s.overall_score for s in snapshots]
        score_change = scores[-1] - scores[0] if len(scores) >= 2 else 0.0
        trend = self._compute_trend(scores)

        time_series = HeatmapTimeSeries(
            snapshots=snapshots,
            period_start=now - timedelta(days=period_days),
            period_end=now,
            granularity=granularity,
            trend=trend,
            score_change=round(score_change, 2),
        )

        logger.info(
            "time_series_generated",
            org_id=org_id,
            period_days=period_days,
            granularity=granularity,
            num_snapshots=len(snapshots),
            trend=trend.value,
        )
        return time_series

    async def compare_timepoints(
        self,
        org_id: str,
        from_date: datetime,
        to_date: datetime,
    ) -> TimeTravel:
        """Compare heatmaps at two points in time (time-travel)."""
        historical = await self.get_heatmap_at(org_id, from_date)
        current = await self.get_heatmap_at(org_id, to_date)

        changes: list[HeatmapChange] = []
        improvements = 0
        regressions = 0

        hist_map = {c.path: c for c in historical.cells}
        for cell in current.cells:
            hist_cell = hist_map.get(cell.path)
            if not hist_cell:
                continue

            if cell.compliance_score != hist_cell.compliance_score:
                score_delta = cell.compliance_score - hist_cell.compliance_score
                if score_delta > 0:
                    improvements += 1
                    reason = "Compliance improvements applied"
                else:
                    regressions += 1
                    reason = "New violations or regulatory changes detected"

                changes.append(
                    HeatmapChange(
                        path=cell.path,
                        old_risk=hist_cell.risk_level,
                        new_risk=cell.risk_level,
                        old_score=hist_cell.compliance_score,
                        new_score=cell.compliance_score,
                        change_reason=reason,
                    )
                )

        result = TimeTravel(
            current=current,
            historical=historical,
            changes=changes,
            improvements=improvements,
            regressions=regressions,
        )

        logger.info(
            "timepoints_compared",
            org_id=org_id,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            improvements=improvements,
            regressions=regressions,
        )
        return result

    async def forecast_risk(
        self,
        org_id: str,
        forecast_days: int = 90,
    ) -> RiskForecast:
        """Forecast future compliance risk using trend analysis."""
        # Build historical score series for forecasting
        scores = self._build_historical_scores(org_id, lookback_days=180)
        predicted_score = self._linear_forecast(scores, forecast_days)
        predicted_score = max(0.0, min(100.0, predicted_score))

        # Estimate future violations from predicted score
        predicted_violations = max(0, int((100.0 - predicted_score) * 0.8))
        confidence = max(30.0, 85.0 - forecast_days * 0.15)

        risk_factors = []
        if predicted_score < 70.0:
            risk_factors.append("Multiple modules trending below compliance threshold")
        if predicted_score < scores[-1]:
            risk_factors.append("Declining compliance trajectory detected")
        risk_factors.append("Upcoming EU AI Act enforcement deadlines")
        risk_factors.append("Third-party dependency risk accumulation")

        recommended_actions = []
        if predicted_score < 60.0:
            recommended_actions.append("Immediately prioritize critical module remediation")
        if predicted_score < 80.0:
            recommended_actions.append("Schedule compliance review for high-risk modules")
        recommended_actions.append("Update data anonymization module to meet GDPR requirements")
        recommended_actions.append("Conduct vendor integration compliance audit")

        forecast = RiskForecast(
            id=uuid4(),
            org_id=org_id,
            forecast_date=datetime.utcnow() + timedelta(days=forecast_days),
            predicted_violations=predicted_violations,
            predicted_score=round(predicted_score, 1),
            confidence_pct=round(confidence, 1),
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
        )

        logger.info(
            "risk_forecast_generated",
            org_id=org_id,
            forecast_days=forecast_days,
            predicted_score=forecast.predicted_score,
            predicted_violations=forecast.predicted_violations,
            confidence=forecast.confidence_pct,
        )
        return forecast

    async def get_module_trends(
        self,
        org_id: str,
        limit: int = 20,
    ) -> list[ModuleRiskTrend]:
        """Get risk trends per module over time."""
        now = datetime.utcnow()
        trends: list[ModuleRiskTrend] = []

        for mod_info in _SAMPLE_MODULES[:limit]:
            timestamps = [now - timedelta(days=90 - i * 10) for i in range(10)]
            scores = self._build_module_scores(mod_info["base_score"], count=10)
            trend = self._compute_trend(scores)
            prediction_30d = self._linear_forecast(scores, 30)

            trends.append(
                ModuleRiskTrend(
                    module=mod_info["module"],
                    scores=[round(s, 1) for s in scores],
                    timestamps=timestamps,
                    trend=trend,
                    prediction_30d=round(max(0.0, min(100.0, prediction_30d)), 1),
                )
            )

        logger.info("module_trends_generated", org_id=org_id, count=len(trends))
        return trends

    async def export_heatmap(
        self,
        org_id: str,
        format: str = "pdf",
        title: str | None = None,
    ) -> HeatmapExport:
        """Export the current heatmap as a downloadable artifact."""
        export_format = ExportFormat(format.lower())
        export_id = uuid4()
        export_title = title or f"Compliance Heatmap — {datetime.utcnow():%Y-%m-%d}"

        export = HeatmapExport(
            id=export_id,
            format=export_format,
            content_url=f"/api/v1/impact-heatmap/exports/{export_id}.{export_format.value}",
            generated_at=datetime.utcnow(),
            title=export_title,
            description=f"Compliance risk heatmap for organization {org_id}",
        )

        logger.info(
            "heatmap_exported",
            org_id=org_id,
            format=export_format.value,
            export_id=str(export_id),
        )
        return export

    async def get_framework_overlay(
        self,
        org_id: str,
        framework: str,
    ) -> HeatmapSnapshot:
        """Get a heatmap filtered to a specific compliance framework."""
        snapshot = self._generate_snapshot(org_id)
        snapshot.framework_overlay = framework

        framework_upper = framework.upper().replace("_", "-")
        snapshot.cells = [
            c for c in snapshot.cells if framework_upper in c.regulations_affected
        ]

        if snapshot.cells:
            snapshot.overall_score = round(
                sum(c.compliance_score for c in snapshot.cells) / len(snapshot.cells), 1
            )
            snapshot.total_violations = sum(c.violation_count for c in snapshot.cells)
        else:
            snapshot.overall_score = 100.0
            snapshot.total_violations = 0

        logger.info(
            "framework_overlay_generated",
            org_id=org_id,
            framework=framework,
            matching_cells=len(snapshot.cells),
        )
        return snapshot

    async def get_hotspots(
        self,
        org_id: str,
        limit: int = 10,
    ) -> list[HeatmapCell]:
        """Get the top risk hotspots across the codebase."""
        snapshot = self._generate_snapshot(org_id)
        sorted_cells = sorted(snapshot.cells, key=lambda c: c.compliance_score)

        hotspots = sorted_cells[:limit]

        logger.info(
            "hotspots_generated",
            org_id=org_id,
            count=len(hotspots),
            worst_score=hotspots[0].compliance_score if hotspots else None,
        )
        return hotspots

    # --- Private helpers ---

    def _risk_to_color(self, risk_level: RiskLevel) -> str:
        """Map a risk level to its hex color for visualization."""
        return _RISK_COLORS.get(risk_level, "#9CA3AF")

    def _compute_trend(self, scores: list[float]) -> TrendDirection:
        """Compute the trend direction from a series of compliance scores."""
        if len(scores) < 2:
            return TrendDirection.STABLE

        recent = scores[-3:] if len(scores) >= 3 else scores[-2:]
        older = scores[:3] if len(scores) >= 3 else scores[:2]

        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)
        delta = avg_recent - avg_older

        if delta > 5.0:
            return TrendDirection.IMPROVING
        if delta > -2.0:
            return TrendDirection.STABLE
        if delta > -10.0:
            return TrendDirection.DEGRADING
        return TrendDirection.RAPIDLY_DEGRADING

    def _linear_forecast(self, scores: list[float], days: int) -> float:
        """Forecast a future score using simple linear regression."""
        n = len(scores)
        if n < 2:
            return scores[0] if scores else 75.0

        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(scores) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        if denominator == 0:
            return y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Project forward by the requested number of steps
        steps_per_day = n / 90.0 if n > 1 else 1.0
        future_x = n + days * steps_per_day
        return slope * future_x + intercept

    def _generate_snapshot(
        self,
        org_id: str,
        days_offset: int = 0,
    ) -> HeatmapSnapshot:
        """Generate a realistic heatmap snapshot with sample data."""
        cells: list[HeatmapCell] = []
        now = datetime.utcnow() + timedelta(days=days_offset)

        for mod_info in _SAMPLE_MODULES:
            # Introduce time-based variation for realistic historical data
            variation = math.sin(days_offset * 0.05 + hash(mod_info["path"]) % 100) * 8.0
            score = max(0.0, min(100.0, mod_info["base_score"] + variation))
            risk_level = self._score_to_risk(score)
            violation_count = max(0, int((100.0 - score) * 0.3))

            cells.append(
                HeatmapCell(
                    path=mod_info["path"],
                    module=mod_info["module"],
                    risk_level=risk_level,
                    compliance_score=round(score, 1),
                    violation_count=violation_count,
                    regulations_affected=mod_info["regs"],
                    last_changed=now - timedelta(days=abs(hash(mod_info["path"])) % 30),
                    color_hex=self._risk_to_color(risk_level),
                )
            )

        overall_score = round(sum(c.compliance_score for c in cells) / len(cells), 1)
        total_violations = sum(c.violation_count for c in cells)

        return HeatmapSnapshot(
            id=uuid4(),
            org_id=org_id,
            timestamp=now,
            cells=cells,
            overall_score=overall_score,
            total_violations=total_violations,
        )

    def _score_to_risk(self, score: float) -> RiskLevel:
        """Convert a numeric compliance score to a risk level."""
        if score >= 90.0:
            return RiskLevel.COMPLIANT
        if score >= 75.0:
            return RiskLevel.LOW
        if score >= 60.0:
            return RiskLevel.MEDIUM
        if score >= 40.0:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _apply_filters(
        self,
        snapshot: HeatmapSnapshot,
        filters: HeatmapFilter,
    ) -> HeatmapSnapshot:
        """Apply filters to a heatmap snapshot."""
        cells = snapshot.cells

        if filters.regulations:
            regs_upper = {r.upper() for r in filters.regulations}
            cells = [c for c in cells if set(c.regulations_affected) & regs_upper]

        if filters.modules:
            modules_lower = {m.lower() for m in filters.modules}
            cells = [c for c in cells if c.module.lower() in modules_lower]

        if filters.min_risk:
            risk_order = [
                RiskLevel.COMPLIANT,
                RiskLevel.LOW,
                RiskLevel.MEDIUM,
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            ]
            min_idx = risk_order.index(filters.min_risk)
            cells = [c for c in cells if risk_order.index(c.risk_level) >= min_idx]

        snapshot.cells = cells
        if cells:
            snapshot.overall_score = round(
                sum(c.compliance_score for c in cells) / len(cells), 1
            )
            snapshot.total_violations = sum(c.violation_count for c in cells)
        else:
            snapshot.overall_score = 100.0
            snapshot.total_violations = 0

        return snapshot

    def _build_historical_scores(
        self,
        org_id: str,
        lookback_days: int = 180,
    ) -> list[float]:
        """Build a series of historical overall scores for forecasting."""
        scores: list[float] = []
        for offset in range(-lookback_days, 0, 10):
            snap = self._generate_snapshot(org_id, days_offset=offset)
            scores.append(snap.overall_score)
        return scores

    def _build_module_scores(
        self,
        base_score: float,
        count: int = 10,
    ) -> list[float]:
        """Build a series of scores for a single module over time."""
        scores: list[float] = []
        for i in range(count):
            variation = math.sin(i * 0.6) * 5.0 + self._rng.uniform(-2.0, 2.0)
            scores.append(max(0.0, min(100.0, base_score + variation)))
        return scores
