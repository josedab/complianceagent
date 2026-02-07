"""Compliance Drift Detection Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.drift_detection.models import (
    AlertChannel,
    AlertConfig,
    AlertStatus,
    ComplianceBaseline,
    DriftAlert,
    DriftEvent,
    DriftReport,
    DriftSeverity,
    DriftType,
)

logger = structlog.get_logger()


class DriftDetectionService:
    """Service for detecting compliance drift and sending alerts."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._baselines: dict[str, ComplianceBaseline] = {}
        self._events: list[DriftEvent] = []
        self._alerts: list[DriftAlert] = []
        self._config: AlertConfig = AlertConfig()

    async def capture_baseline(
        self, repo: str, branch: str = "main", commit_sha: str = ""
    ) -> ComplianceBaseline:
        """Capture current compliance state as a baseline."""
        baseline = ComplianceBaseline(
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            score=100.0,
            findings_count=0,
            captured_at=datetime.now(UTC),
        )

        key = f"{repo}:{branch}"
        self._baselines[key] = baseline
        logger.info("Baseline captured", repo=repo, branch=branch, score=baseline.score)
        return baseline

    async def get_baseline(self, repo: str, branch: str = "main") -> ComplianceBaseline | None:
        """Get the current baseline for a repo/branch."""
        return self._baselines.get(f"{repo}:{branch}")

    async def detect_drift(
        self,
        repo: str,
        branch: str = "main",
        commit_sha: str = "",
        current_findings: list[dict] | None = None,
        current_score: float = 100.0,
    ) -> list[DriftEvent]:
        """Compare current state against baseline to detect drift."""
        key = f"{repo}:{branch}"
        baseline = self._baselines.get(key)

        events: list[DriftEvent] = []

        if not baseline:
            logger.info("No baseline found, creating initial", repo=repo)
            await self.capture_baseline(repo, branch, commit_sha)
            return events

        # Score regression detection
        score_delta = current_score - baseline.score
        if score_delta < -5:  # 5+ point regression
            severity = DriftSeverity.CRITICAL if score_delta < -20 else (
                DriftSeverity.HIGH if score_delta < -10 else DriftSeverity.MEDIUM
            )
            events.append(DriftEvent(
                repo=repo,
                branch=branch,
                drift_type=DriftType.REGRESSION,
                severity=severity,
                description=f"Compliance score dropped by {abs(score_delta):.1f} points",
                commit_sha=commit_sha,
                previous_score=baseline.score,
                current_score=current_score,
                detected_at=datetime.now(UTC),
            ))

        # New findings detection
        if current_findings:
            for finding in current_findings:
                events.append(DriftEvent(
                    repo=repo,
                    branch=branch,
                    drift_type=DriftType.NEW_VIOLATION,
                    severity=DriftSeverity(finding.get("severity", "medium")),
                    regulation=finding.get("regulation", ""),
                    article_ref=finding.get("article_ref", ""),
                    description=finding.get("description", "New compliance violation detected"),
                    file_path=finding.get("file_path", ""),
                    commit_sha=commit_sha,
                    detected_at=datetime.now(UTC),
                ))

        self._events.extend(events)

        if events:
            logger.warning("Drift detected", repo=repo, events=len(events))
            await self._trigger_alerts(events)

        return events

    async def list_events(
        self,
        repo: str | None = None,
        severity: DriftSeverity | None = None,
        drift_type: DriftType | None = None,
        limit: int = 50,
    ) -> list[DriftEvent]:
        """List drift events with optional filters."""
        results = list(self._events)
        if repo:
            results = [e for e in results if e.repo == repo]
        if severity:
            results = [e for e in results if e.severity == severity]
        if drift_type:
            results = [e for e in results if e.drift_type == drift_type]
        return sorted(results, key=lambda e: e.detected_at or datetime.min, reverse=True)[:limit]

    async def resolve_event(self, event_id: UUID) -> DriftEvent | None:
        """Mark a drift event as resolved."""
        for event in self._events:
            if event.id == event_id:
                event.resolved_at = datetime.now(UTC)
                logger.info("Drift event resolved", event_id=str(event_id))
                return event
        return None

    async def configure_alerts(self, config: AlertConfig) -> AlertConfig:
        """Update alert configuration."""
        self._config = config
        logger.info("Alert config updated", channels=[c.value for c in config.channels])
        return config

    async def get_alert_config(self) -> AlertConfig:
        """Get current alert configuration."""
        return self._config

    async def get_report(
        self,
        repo: str,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> DriftReport:
        """Generate a drift report for a repository."""
        events = [e for e in self._events if e.repo == repo]
        if period_start:
            events = [e for e in events if e.detected_at and e.detected_at >= period_start]
        if period_end:
            events = [e for e in events if e.detected_at and e.detected_at <= period_end]

        by_severity: dict[str, int] = {}
        by_type: dict[str, int] = {}
        file_counts: dict[str, int] = {}

        for event in events:
            by_severity[event.severity.value] = by_severity.get(event.severity.value, 0) + 1
            by_type[event.drift_type.value] = by_type.get(event.drift_type.value, 0) + 1
            if event.file_path:
                file_counts[event.file_path] = file_counts.get(event.file_path, 0) + 1

        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return DriftReport(
            repo=repo,
            period_start=period_start,
            period_end=period_end,
            total_events=len(events),
            events_by_severity=by_severity,
            events_by_type=by_type,
            top_drifting_files=[{"file": f, "count": c} for f, c in top_files],
        )

    async def _trigger_alerts(self, events: list[DriftEvent]) -> None:
        """Send alerts for drift events based on configuration."""
        for event in events:
            if self._severity_meets_threshold(event.severity):
                for channel in self._config.channels:
                    alert = DriftAlert(
                        drift_event_id=event.id,
                        channel=channel,
                        status=AlertStatus.PENDING,
                        recipients=self._config.recipients.get(channel.value, []),
                        message=self._format_alert(event),
                    )
                    self._alerts.append(alert)

                    # In production: dispatch via Celery task
                    alert.status = AlertStatus.SENT
                    alert.sent_at = datetime.now(UTC)

        logger.info("Alerts dispatched", count=len(self._alerts))

    def _severity_meets_threshold(self, severity: DriftSeverity) -> bool:
        """Check if severity meets the configured threshold."""
        severity_order = {
            DriftSeverity.LOW: 0,
            DriftSeverity.MEDIUM: 1,
            DriftSeverity.HIGH: 2,
            DriftSeverity.CRITICAL: 3,
        }
        return severity_order.get(severity, 0) >= severity_order.get(self._config.severity_threshold, 1)

    def _format_alert(self, event: DriftEvent) -> str:
        """Format a drift event as an alert message."""
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
        icon = emoji.get(event.severity.value, "⚪")
        return (
            f"{icon} Compliance drift detected in {event.repo}\n"
            f"Type: {event.drift_type.value} | Severity: {event.severity.value}\n"
            f"{event.description}"
        )
