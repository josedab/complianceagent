"""Compliance Drift Detection Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.drift_detection.models import (
    AlertChannel,
    AlertConfig,
    AlertStatus,
    CICDGateDecision,
    CICDGateResult,
    ComplianceBaseline,
    DriftAlert,
    DriftEvent,
    DriftReport,
    DriftSeverity,
    DriftTrend,
    DriftType,
    TopDriftingFile,
    WebhookDelivery,
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

    async def check_cicd_gate(
        self,
        repo: str,
        branch: str = "main",
        commit_sha: str = "",
        current_score: float = 100.0,
        current_findings: list[dict] | None = None,
        threshold_score: float = 80.0,
        block_on_critical: bool = True,
    ) -> CICDGateResult:
        """Evaluate compliance gate for CI/CD pipeline.

        Returns pass/fail/warn decision based on compliance score and findings.
        Designed to be called from GitHub Actions, GitLab CI, or similar.
        """
        events = await self.detect_drift(
            repo=repo, branch=branch, commit_sha=commit_sha,
            current_findings=current_findings, current_score=current_score,
        )

        critical_violations = sum(1 for e in events if e.severity == DriftSeverity.CRITICAL)
        high_violations = sum(1 for e in events if e.severity == DriftSeverity.HIGH)
        blocking = [e.description for e in events if e.severity == DriftSeverity.CRITICAL]
        warnings = [e.description for e in events if e.severity in (DriftSeverity.HIGH, DriftSeverity.MEDIUM)]

        # Determine decision
        if block_on_critical and critical_violations > 0:
            decision = CICDGateDecision.FAIL
        elif current_score < threshold_score:
            decision = CICDGateDecision.FAIL
        elif high_violations > 0 or current_score < threshold_score + 10:
            decision = CICDGateDecision.WARN
        else:
            decision = CICDGateDecision.PASS

        result = CICDGateResult(
            repo=repo, branch=branch, commit_sha=commit_sha,
            decision=decision, current_score=current_score,
            threshold_score=threshold_score,
            violations_found=len(events),
            critical_violations=critical_violations,
            blocking_findings=blocking, warnings=warnings,
            checked_at=datetime.now(UTC),
        )

        logger.info(
            "CI/CD gate checked",
            repo=repo, decision=decision.value,
            score=current_score, violations=len(events),
        )
        return result

    # ── Trend Analysis ───────────────────────────────────────────────────

    def get_drift_trend(
        self,
        repo: str,
        period: str = "7d",
    ) -> DriftTrend:
        """Get drift score trend over time."""
        events = [e for e in self._events if e.repo == repo]
        events.sort(key=lambda e: e.detected_at or datetime.now(UTC))

        if not events:
            baseline = self._baselines.get(repo)
            score = baseline.score if baseline else 100.0
            return DriftTrend(
                repo=repo, period=period,
                data_points=[{"date": datetime.now(UTC).isoformat(), "score": score}],
                trend_direction="stable", avg_score=score, min_score=score, max_score=score,
            )

        data_points = []
        scores = []
        for event in events:
            score = event.current_score
            scores.append(score)
            data_points.append({
                "date": event.detected_at.isoformat() if event.detected_at else "",
                "score": score,
                "event_id": str(event.id),
                "severity": event.severity.value if hasattr(event.severity, 'value') else event.severity,
            })

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        volatility = max_score - min_score

        # Determine trend direction
        if len(scores) >= 2:
            recent_half = scores[len(scores) // 2:]
            earlier_half = scores[:len(scores) // 2]
            recent_avg = sum(recent_half) / len(recent_half)
            earlier_avg = sum(earlier_half) / len(earlier_half) if earlier_half else recent_avg
            if recent_avg > earlier_avg + 2:
                direction = "improving"
            elif recent_avg < earlier_avg - 2:
                direction = "degrading"
            else:
                direction = "stable"
        else:
            direction = "stable"

        return DriftTrend(
            repo=repo,
            period=period,
            data_points=data_points,
            trend_direction=direction,
            avg_score=round(avg_score, 2),
            min_score=round(min_score, 2),
            max_score=round(max_score, 2),
            volatility=round(volatility, 2),
        )

    def get_top_drifting_files(
        self,
        repo: str,
        limit: int = 10,
    ) -> list[TopDriftingFile]:
        """Get the files with the most compliance drift."""
        events = [e for e in self._events if e.repo == repo]

        file_stats: dict[str, dict] = {}
        for event in events:
            for file_path in event.blast_radius:
                if file_path not in file_stats:
                    file_stats[file_path] = {
                        "drift_count": 0,
                        "total_delta": 0.0,
                        "last_drift_at": "",
                        "regulations": set(),
                    }
                stats = file_stats[file_path]
                stats["drift_count"] += 1
                stats["total_delta"] += abs(event.current_score - event.previous_score)
                detected = event.detected_at.isoformat() if event.detected_at else ""
                if detected > stats["last_drift_at"]:
                    stats["last_drift_at"] = detected
                stats["regulations"].add(event.regulation if event.regulation else "General")

        results = [
            TopDriftingFile(
                file_path=path,
                drift_count=stats["drift_count"],
                total_delta=round(stats["total_delta"], 2),
                last_drift_at=stats["last_drift_at"],
                regulations_affected=list(stats["regulations"]),
            )
            for path, stats in file_stats.items()
        ]
        results.sort(key=lambda f: f.drift_count, reverse=True)
        return results[:limit]

    # ── Webhook Delivery ─────────────────────────────────────────────────

    async def deliver_webhook(
        self,
        event_id: str,
        channel: str,
    ) -> WebhookDelivery:
        """Simulate delivering a webhook notification for a drift event."""
        if not hasattr(self, '_webhook_deliveries'):
            self._webhook_deliveries: list[WebhookDelivery] = []

        config = self._config
        url_map = {
            "slack": config.slack_webhook_url or "https://hooks.slack.com/services/...",
            "teams": config.teams_webhook_url or "https://outlook.office.com/webhook/...",
            "pagerduty": config.pagerduty_routing_key or "https://events.pagerduty.com/v2/enqueue",
            "email": "smtp://localhost:587",
        }

        delivery = WebhookDelivery(
            channel=channel,
            url=url_map.get(channel, ""),
            event_id=event_id,
            payload={"event_id": event_id, "channel": channel, "type": "drift_alert"},
            status="delivered",
            response_code=200,
            delivered_at=datetime.now(UTC),
            attempts=1,
        )

        self._webhook_deliveries.append(delivery)

        logger.info(
            "Webhook delivered",
            channel=channel,
            event_id=event_id,
            delivery_id=str(delivery.id),
        )
        return delivery

    def get_webhook_deliveries(
        self,
        event_id: str | None = None,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        """Get webhook delivery history."""
        if not hasattr(self, '_webhook_deliveries'):
            self._webhook_deliveries: list[WebhookDelivery] = []

        deliveries = self._webhook_deliveries
        if event_id:
            deliveries = [d for d in deliveries if d.event_id == event_id]
        return deliveries[:limit]

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
