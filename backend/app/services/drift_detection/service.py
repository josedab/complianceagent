"""Compliance Drift Detection Service."""

from datetime import UTC, datetime
from uuid import UUID

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.secondary_persistence import DriftAlertRecord, DriftBaselineRecord, DriftEventRecord
from app.services.drift_detection.models import (
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
_WEBHOOK_DELIVERIES: list[WebhookDelivery] = []


def _baseline_record_to_domain(record: DriftBaselineRecord) -> ComplianceBaseline:
    snapshot = record.snapshot or {}
    return ComplianceBaseline(
        id=record.id,
        repo=snapshot.get("repo", ""),
        branch=snapshot.get("branch", "main"),
        commit_sha=snapshot.get("commit_sha", ""),
        score=snapshot.get("score", 100.0),
        findings_count=snapshot.get("findings_count", 0),
        findings_by_severity=snapshot.get("findings_by_severity", {}),
        findings_by_regulation=snapshot.get("findings_by_regulation", {}),
        captured_at=record.created_at,
    )


def _event_record_to_domain(
    record: DriftEventRecord, baseline_lookup: dict[UUID, ComplianceBaseline]
) -> DriftEvent:
    meta = record.drift_metadata or {}
    baseline = baseline_lookup.get(record.baseline_id)
    return DriftEvent(
        id=record.id,
        repo=meta.get("repo", baseline.repo if baseline else ""),
        branch=meta.get("branch", baseline.branch if baseline else "main"),
        drift_type=DriftType(record.drift_type),
        severity=DriftSeverity(record.severity),
        regulation=meta.get("regulation", ""),
        article_ref=meta.get("article_ref", ""),
        description=record.description,
        file_path=meta.get("file_path", ""),
        commit_sha=meta.get("commit_sha", baseline.commit_sha if baseline else ""),
        previous_score=meta.get("previous_score", baseline.score if baseline else 100.0),
        current_score=meta.get("current_score", meta.get("score", 100.0)),
        blast_radius=meta.get("blast_radius", []),
        detected_at=record.created_at,
        resolved_at=record.resolved_at,
    )


class DriftDetectionService:
    """Service for detecting compliance drift and sending alerts."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id
        self._config: AlertConfig = AlertConfig()

    async def capture_baseline(
        self, repo: str, branch: str = "main", commit_sha: str = ""
    ) -> ComplianceBaseline:
        baseline = ComplianceBaseline(
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            score=100.0,
            findings_count=0,
            captured_at=datetime.now(UTC),
        )
        existing = await self._load_baseline_records()
        for record in existing:
            snapshot = record.snapshot or {}
            if (
                snapshot.get("repo") == repo
                and snapshot.get("branch") == branch
                and record.is_active
            ):
                record.is_active = False
        snapshot = {
            "repo": repo,
            "branch": branch,
            "commit_sha": commit_sha,
            "score": baseline.score,
            "findings_count": baseline.findings_count,
            "findings_by_severity": baseline.findings_by_severity,
            "findings_by_regulation": baseline.findings_by_regulation,
        }
        hash_value = self._hash_snapshot(snapshot)
        record = DriftBaselineRecord(
            id=baseline.id,
            organization_id=self.organization_id,
            regulation="repository",
            snapshot=snapshot,
            hash_value=hash_value,
            is_active=True,
        )
        self.db.add(record)
        await self.db.flush()
        logger.info("Baseline captured", repo=repo, branch=branch, score=baseline.score)
        return _baseline_record_to_domain(record)

    async def get_baseline(self, repo: str, branch: str = "main") -> ComplianceBaseline | None:
        record = await self._get_active_baseline_record(repo, branch)
        return _baseline_record_to_domain(record) if record else None

    async def detect_drift(
        self,
        repo: str,
        branch: str = "main",
        commit_sha: str = "",
        current_findings: list[dict] | None = None,
        current_score: float = 100.0,
    ) -> list[DriftEvent]:
        baseline_record = await self._get_active_baseline_record(repo, branch)
        events: list[DriftEvent] = []
        if not baseline_record:
            logger.info("No baseline found, creating initial", repo=repo)
            await self.capture_baseline(repo, branch, commit_sha)
            return events

        baseline = _baseline_record_to_domain(baseline_record)
        score_delta = current_score - baseline.score
        if score_delta < -5:
            severity = (
                DriftSeverity.CRITICAL
                if score_delta < -20
                else DriftSeverity.HIGH
                if score_delta < -10
                else DriftSeverity.MEDIUM
            )
            events.append(
                DriftEvent(
                    repo=repo,
                    branch=branch,
                    drift_type=DriftType.REGRESSION,
                    severity=severity,
                    description=f"Compliance score dropped by {abs(score_delta):.1f} points",
                    commit_sha=commit_sha,
                    previous_score=baseline.score,
                    current_score=current_score,
                    detected_at=datetime.now(UTC),
                )
            )
        if current_findings:
            for finding in current_findings:
                events.append(
                    DriftEvent(
                        repo=repo,
                        branch=branch,
                        drift_type=DriftType.NEW_VIOLATION,
                        severity=DriftSeverity(finding.get("severity", "medium")),
                        regulation=finding.get("regulation", ""),
                        article_ref=finding.get("article_ref", ""),
                        description=finding.get("description", "New compliance violation detected"),
                        file_path=finding.get("file_path", ""),
                        commit_sha=commit_sha,
                        previous_score=baseline.score,
                        current_score=current_score,
                        blast_radius=[finding.get("file_path", "")]
                        if finding.get("file_path")
                        else [],
                        detected_at=datetime.now(UTC),
                    )
                )
        persisted: list[DriftEvent] = []
        for event in events:
            record = DriftEventRecord(
                id=event.id,
                organization_id=self.organization_id,
                baseline_id=baseline_record.id,
                drift_type=event.drift_type.value,
                severity=event.severity.value,
                description=event.description,
                affected_controls=event.blast_radius,
                drift_metadata={
                    "repo": event.repo,
                    "branch": event.branch,
                    "regulation": event.regulation,
                    "article_ref": event.article_ref,
                    "file_path": event.file_path,
                    "commit_sha": event.commit_sha,
                    "previous_score": event.previous_score,
                    "current_score": event.current_score,
                    "blast_radius": event.blast_radius,
                },
            )
            self.db.add(record)
            persisted.append(event)
        await self.db.flush()
        if persisted:
            logger.warning("Drift detected", repo=repo, events=len(persisted))
            await self._trigger_alerts(persisted)
        return persisted

    async def list_events(
        self,
        repo: str | None = None,
        severity: DriftSeverity | None = None,
        drift_type: DriftType | None = None,
        limit: int = 50,
    ) -> list[DriftEvent]:
        baseline_lookup = await self._baseline_lookup()
        stmt = (
            select(DriftEventRecord)
            .where(DriftEventRecord.organization_id == self.organization_id)
            .order_by(DriftEventRecord.created_at.desc())
            .limit(limit)
        )
        if severity:
            stmt = stmt.where(DriftEventRecord.severity == severity.value)
        if drift_type:
            stmt = stmt.where(DriftEventRecord.drift_type == drift_type.value)
        result = await self.db.execute(stmt)
        events = [
            _event_record_to_domain(record, baseline_lookup) for record in result.scalars().all()
        ]
        if repo:
            events = [event for event in events if event.repo == repo]
        return events

    async def resolve_event(self, event_id: UUID) -> DriftEvent | None:
        stmt = select(DriftEventRecord).where(
            DriftEventRecord.id == event_id,
            DriftEventRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        record.resolved_at = datetime.now(UTC)
        await self.db.flush()
        logger.info("Drift event resolved", event_id=str(event_id))
        return _event_record_to_domain(record, await self._baseline_lookup())

    async def configure_alerts(self, config: AlertConfig) -> AlertConfig:
        self._config = config
        logger.info("Alert config updated", channels=[channel.value for channel in config.channels])
        return config

    async def get_alert_config(self) -> AlertConfig:
        return self._config

    async def get_report(
        self, repo: str, period_start: datetime | None = None, period_end: datetime | None = None
    ) -> DriftReport:
        events = [
            event
            for event in await self.list_events(repo=repo, limit=500)
            if (not period_start or (event.detected_at and event.detected_at >= period_start))
            and (not period_end or (event.detected_at and event.detected_at <= period_end))
        ]
        by_severity: dict[str, int] = {}
        by_type: dict[str, int] = {}
        file_counts: dict[str, int] = {}
        for event in events:
            by_severity[event.severity.value] = by_severity.get(event.severity.value, 0) + 1
            by_type[event.drift_type.value] = by_type.get(event.drift_type.value, 0) + 1
            if event.file_path:
                file_counts[event.file_path] = file_counts.get(event.file_path, 0) + 1
        top_files = sorted(file_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        return DriftReport(
            repo=repo,
            period_start=period_start,
            period_end=period_end,
            total_events=len(events),
            events_by_severity=by_severity,
            events_by_type=by_type,
            top_drifting_files=[{"file": path, "count": count} for path, count in top_files],
        )

    async def _trigger_alerts(self, events: list[DriftEvent]) -> None:
        baseline_record_lookup = await self._baseline_record_lookup_by_repo_branch()
        for event in events:
            if self._severity_meets_threshold(event.severity):
                baseline_id = baseline_record_lookup.get((event.repo, event.branch))
                if baseline_id is None:
                    continue
                for channel in self._config.channels:
                    alert = DriftAlert(
                        drift_event_id=event.id,
                        channel=channel,
                        status=AlertStatus.SENT,
                        recipients=self._config.recipients.get(channel.value, []),
                        message=self._format_alert(event),
                        sent_at=datetime.now(UTC),
                    )
                    self.db.add(
                        DriftAlertRecord(
                            organization_id=self.organization_id,
                            drift_event_id=event.id,
                            status=alert.status.value,
                            notified_at=alert.sent_at,
                            alert_metadata={
                                "channel": channel.value,
                                "recipients": alert.recipients,
                                "message": alert.message,
                            },
                        )
                    )
        await self.db.flush()
        logger.info("Alerts dispatched", count=len(events))

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
        events = await self.detect_drift(
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            current_findings=current_findings,
            current_score=current_score,
        )
        critical_violations = sum(1 for event in events if event.severity == DriftSeverity.CRITICAL)
        high_violations = sum(1 for event in events if event.severity == DriftSeverity.HIGH)
        blocking = [
            event.description for event in events if event.severity == DriftSeverity.CRITICAL
        ]
        warnings = [
            event.description
            for event in events
            if event.severity in (DriftSeverity.HIGH, DriftSeverity.MEDIUM)
        ]
        if (block_on_critical and critical_violations > 0) or current_score < threshold_score:
            decision = CICDGateDecision.FAIL
        elif high_violations > 0 or current_score < threshold_score + 10:
            decision = CICDGateDecision.WARN
        else:
            decision = CICDGateDecision.PASS
        result = CICDGateResult(
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            decision=decision,
            current_score=current_score,
            threshold_score=threshold_score,
            violations_found=len(events),
            critical_violations=critical_violations,
            blocking_findings=blocking,
            warnings=warnings,
            checked_at=datetime.now(UTC),
        )
        logger.info(
            "CI/CD gate checked",
            repo=repo,
            decision=decision.value,
            score=current_score,
            violations=len(events),
        )
        return result

    async def get_drift_trend(self, repo: str, period: str = "7d") -> DriftTrend:
        events = await self.list_events(repo=repo, limit=500)
        events.sort(key=lambda event: event.detected_at or datetime.now(UTC))
        if not events:
            baseline = await self.get_baseline(repo)
            score = baseline.score if baseline else 100.0
            return DriftTrend(
                repo=repo,
                period=period,
                data_points=[{"date": datetime.now(UTC).isoformat(), "score": score}],
                trend_direction="stable",
                avg_score=score,
                min_score=score,
                max_score=score,
            )
        data_points = []
        scores = []
        for event in events:
            scores.append(event.current_score)
            data_points.append(
                {
                    "date": event.detected_at.isoformat() if event.detected_at else "",
                    "score": event.current_score,
                    "event_id": str(event.id),
                    "severity": event.severity.value,
                }
            )
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        if len(scores) >= 2:
            recent_half = scores[len(scores) // 2 :]
            earlier_half = scores[: len(scores) // 2]
            recent_avg = sum(recent_half) / len(recent_half)
            earlier_avg = sum(earlier_half) / len(earlier_half) if earlier_half else recent_avg
            direction = (
                "improving"
                if recent_avg > earlier_avg + 2
                else "degrading"
                if recent_avg < earlier_avg - 2
                else "stable"
            )
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
            volatility=round(max_score - min_score, 2),
        )

    async def get_top_drifting_files(self, repo: str, limit: int = 10) -> list[TopDriftingFile]:
        events = await self.list_events(repo=repo, limit=500)
        file_stats: dict[str, dict] = {}
        for event in events:
            for file_path in event.blast_radius or ([event.file_path] if event.file_path else []):
                stats = file_stats.setdefault(
                    file_path,
                    {
                        "drift_count": 0,
                        "total_delta": 0.0,
                        "last_drift_at": "",
                        "regulations": set(),
                    },
                )
                stats["drift_count"] += 1
                stats["total_delta"] += abs(event.current_score - event.previous_score)
                detected = event.detected_at.isoformat() if event.detected_at else ""
                stats["last_drift_at"] = max(stats["last_drift_at"], detected)
                stats["regulations"].add(event.regulation or "General")
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
        results.sort(key=lambda item: item.drift_count, reverse=True)
        return results[:limit]

    async def deliver_webhook(self, event_id: str, channel: str) -> WebhookDelivery:
        event = next(
            (item for item in await self.list_events(limit=500) if str(item.id) == event_id), None
        )
        alert_message = self._format_alert(event) if event else f"Drift event {event_id}"
        url = ""
        payload: dict = {}
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if channel == "slack" and self._config.slack_webhook_url:
            url = self._config.slack_webhook_url
            payload = {
                "text": alert_message,
                "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": alert_message}}],
            }
        elif channel == "teams" and self._config.teams_webhook_url:
            url = self._config.teams_webhook_url
            payload = {
                "@type": "MessageCard",
                "summary": "Compliance Drift Alert",
                "themeColor": "FF0000",
                "text": alert_message,
            }
        status = "skipped"
        response_code = 0
        attempts = 0
        if url:
            attempts = 1
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response_code = response.status_code
                    status = "delivered" if response.is_success else "failed"
            except (httpx.HTTPError, OSError, ValueError) as exc:
                status = "failed"
                logger.warning("Webhook delivery failed", channel=channel, error=str(exc))
        delivery = WebhookDelivery(
            channel=channel,
            url=url,
            event_id=event_id,
            payload=payload,
            status=status,
            response_code=response_code,
            delivered_at=datetime.now(UTC),
            attempts=attempts,
        )
        _WEBHOOK_DELIVERIES.append(delivery)
        logger.info(
            "Webhook delivery attempted",
            channel=channel,
            event_id=event_id,
            status=status,
            response_code=response_code,
        )
        return delivery

    def get_webhook_deliveries(
        self, event_id: str | None = None, limit: int = 50
    ) -> list[WebhookDelivery]:
        deliveries = _WEBHOOK_DELIVERIES
        if event_id:
            deliveries = [delivery for delivery in deliveries if delivery.event_id == event_id]
        return deliveries[:limit]

    def _severity_meets_threshold(self, severity: DriftSeverity) -> bool:
        severity_order = {
            DriftSeverity.LOW: 0,
            DriftSeverity.MEDIUM: 1,
            DriftSeverity.HIGH: 2,
            DriftSeverity.CRITICAL: 3,
        }
        return severity_order.get(severity, 0) >= severity_order.get(
            self._config.severity_threshold, 1
        )

    def _format_alert(self, event: DriftEvent) -> str:
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
        icon = emoji.get(event.severity.value, "⚪")
        return f"{icon} Compliance drift detected in {event.repo}\nType: {event.drift_type.value} | Severity: {event.severity.value}\n{event.description}"

    async def _load_baseline_records(self) -> list[DriftBaselineRecord]:
        stmt = select(DriftBaselineRecord).where(
            DriftBaselineRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_active_baseline_record(
        self, repo: str, branch: str
    ) -> DriftBaselineRecord | None:
        records = await self._load_baseline_records()
        for record in records:
            snapshot = record.snapshot or {}
            if (
                record.is_active
                and snapshot.get("repo") == repo
                and snapshot.get("branch") == branch
            ):
                return record
        return None

    async def _baseline_lookup(self) -> dict[UUID, ComplianceBaseline]:
        return {
            record.id: _baseline_record_to_domain(record)
            for record in await self._load_baseline_records()
        }

    async def _baseline_record_lookup_by_repo_branch(self) -> dict[tuple[str, str], UUID]:
        lookup: dict[tuple[str, str], UUID] = {}
        for record in await self._load_baseline_records():
            snapshot = record.snapshot or {}
            lookup[(snapshot.get("repo", ""), snapshot.get("branch", "main"))] = record.id
        return lookup

    def _hash_snapshot(self, snapshot: dict) -> str:
        import hashlib
        import json

        return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
