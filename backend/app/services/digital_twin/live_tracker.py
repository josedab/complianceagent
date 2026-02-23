"""Live compliance posture tracking with time-travel and blast radius analysis.

Provides event-driven snapshot capture, point-in-time posture queries,
and blast radius calculation for regulatory changes.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.digital_twin.models import (
    ComplianceSnapshot,
    ComplianceStatus,
)
from app.services.digital_twin.snapshot import SnapshotManager


logger = structlog.get_logger()


class TwinEventType(str, Enum):
    """Events that trigger automatic snapshot capture."""

    REGULATION_CHANGE = "regulation_change"
    CODE_DEPLOY = "code_deploy"
    SCAN_COMPLETE = "scan_complete"
    DRIFT_DETECTED = "drift_detected"
    VENDOR_CHANGE = "vendor_change"
    MANUAL = "manual"


class BlastRadiusSeverity(str, Enum):
    """Severity of a blast radius impact."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class TwinEvent:
    """An event that affects compliance posture."""

    id: UUID = field(default_factory=uuid4)
    event_type: TwinEventType = TwinEventType.MANUAL
    source: str = ""
    description: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    snapshot_id: UUID | None = None


@dataclass
class BlastRadiusItem:
    """A single item affected by a regulatory change."""

    component: str = ""
    file_path: str | None = None
    regulation: str = ""
    current_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    projected_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    impact_severity: BlastRadiusSeverity = BlastRadiusSeverity.MEDIUM
    remediation_effort_hours: float = 0.0
    description: str = ""


@dataclass
class BlastRadiusReport:
    """Blast radius analysis for a regulatory change."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    scenario_description: str = ""
    total_affected_components: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_remediation_hours: float = 0.0
    affected_items: list[BlastRadiusItem] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TimeTravelQuery:
    """Query to view posture at a specific point in time."""

    target_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    organization_id: UUID | None = None
    regulation_filter: str | None = None


@dataclass
class PostureTimeline:
    """Compliance posture over a time period."""

    organization_id: str = ""
    start_time: str = ""
    end_time: str = ""
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    score_trend: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)


class LivePostureTracker:
    """Tracks compliance posture in real-time with event-driven snapshots."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._snapshot_manager = SnapshotManager(db=db)
        self._events: list[TwinEvent] = []
        self._auto_snapshot_enabled = True

    async def record_event(
        self,
        event_type: TwinEventType,
        source: str,
        description: str,
        organization_id: UUID,
        payload: dict[str, Any] | None = None,
        auto_snapshot: bool = True,
    ) -> TwinEvent:
        """Record a compliance-relevant event and optionally capture a snapshot."""
        event = TwinEvent(
            event_type=event_type,
            source=source,
            description=description,
            payload=payload or {},
        )
        self._events.append(event)

        if auto_snapshot and self._auto_snapshot_enabled:
            snapshot = await self._snapshot_manager.create_snapshot(
                organization_id=organization_id,
                repository="*",
                metadata={
                    "trigger": event_type.value,
                    "event_id": str(event.id),
                    "source": source,
                },
            )
            event.snapshot_id = snapshot.id
            logger.info(
                "Auto-snapshot captured",
                event_type=event_type.value,
                snapshot_id=str(snapshot.id),
            )

        return event

    async def time_travel(
        self,
        organization_id: UUID,
        target_time: datetime,
    ) -> ComplianceSnapshot | None:
        """Get the compliance posture at a specific point in time.

        Returns the most recent snapshot taken before ``target_time``.
        """
        snapshots = await self._snapshot_manager.list_snapshots(
            organization_id=organization_id,
        )

        # Find closest snapshot at or before target time
        candidates = [s for s in snapshots if s.captured_at and s.captured_at <= target_time]
        if not candidates:
            return None

        candidates.sort(
            key=lambda s: s.captured_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )
        snapshot = candidates[0]

        logger.info(
            "Time-travel query",
            target=target_time.isoformat(),
            found=snapshot.captured_at.isoformat() if snapshot.captured_at else "none",
        )
        return snapshot

    async def get_posture_timeline(
        self,
        organization_id: UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        max_points: int = 50,
    ) -> PostureTimeline:
        """Get compliance posture trend over a time period."""
        if not end_time:
            end_time = datetime.now(UTC)
        if not start_time:
            start_time = end_time - timedelta(days=30)

        snapshots = await self._snapshot_manager.list_snapshots(
            organization_id=organization_id,
        )

        filtered = [
            s for s in snapshots if s.captured_at and start_time <= s.captured_at <= end_time
        ]
        filtered.sort(key=lambda s: s.captured_at or datetime.min.replace(tzinfo=UTC))

        # Downsample if too many points
        if len(filtered) > max_points:
            step = len(filtered) // max_points
            filtered = filtered[::step]

        score_trend = [
            {
                "timestamp": s.captured_at.isoformat() if s.captured_at else "",
                "score": s.overall_score,
                "status": s.status.value if s.status else "unknown",
            }
            for s in filtered
        ]

        events_in_range = [
            {
                "id": str(e.id),
                "type": e.event_type.value,
                "source": e.source,
                "description": e.description,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self._events
            if start_time <= e.timestamp <= end_time
        ]

        return PostureTimeline(
            organization_id=str(organization_id),
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            snapshots=[
                {
                    "id": str(s.id),
                    "captured_at": s.captured_at.isoformat() if s.captured_at else "",
                    "score": s.overall_score,
                    "issues_count": len(s.issues),
                }
                for s in filtered
            ],
            score_trend=score_trend,
            events=events_in_range,
        )

    async def calculate_blast_radius(
        self,
        organization_id: UUID,
        regulation: str,
        scenario_description: str = "",
        affected_areas: list[str] | None = None,
    ) -> BlastRadiusReport:
        """Calculate the blast radius of a new or changed regulation.

        Analyzes which components, files, and services would be impacted,
        and estimates remediation effort.
        """
        latest = await self._snapshot_manager.get_latest_snapshot(
            organization_id=organization_id,
        )

        report = BlastRadiusReport(
            regulation=regulation,
            scenario_description=scenario_description or f"Impact analysis for {regulation}",
        )

        if not latest:
            report.recommendations.append(
                "No baseline snapshot available. Run a compliance scan first."
            )
            return report

        # Analyze current regulations for overlap
        regulation_lower = regulation.lower()
        affected_items: list[BlastRadiusItem] = []

        # Map regulation to commonly affected component types
        regulation_impact_map: dict[str, list[dict[str, Any]]] = {
            "gdpr": [
                {"component": "User Data Processing", "severity": "critical", "hours": 40},
                {"component": "Consent Management", "severity": "high", "hours": 24},
                {"component": "Data Retention Policies", "severity": "high", "hours": 16},
                {"component": "Right to Erasure Handlers", "severity": "critical", "hours": 32},
                {"component": "Data Export/Portability", "severity": "medium", "hours": 16},
                {"component": "Privacy Policy", "severity": "medium", "hours": 8},
            ],
            "hipaa": [
                {"component": "PHI Data Handlers", "severity": "critical", "hours": 48},
                {"component": "Encryption Layer", "severity": "critical", "hours": 32},
                {"component": "Access Control", "severity": "high", "hours": 24},
                {"component": "Audit Logging", "severity": "high", "hours": 16},
                {"component": "Business Associate Agreements", "severity": "medium", "hours": 8},
            ],
            "pci-dss": [
                {"component": "Payment Processing", "severity": "critical", "hours": 40},
                {"component": "Card Data Storage", "severity": "critical", "hours": 32},
                {"component": "Network Segmentation", "severity": "high", "hours": 24},
                {"component": "Encryption at Rest/Transit", "severity": "high", "hours": 20},
                {"component": "Vulnerability Management", "severity": "medium", "hours": 16},
            ],
            "eu ai act": [
                {"component": "AI Model Registry", "severity": "critical", "hours": 40},
                {"component": "Risk Assessment Pipeline", "severity": "critical", "hours": 48},
                {"component": "Transparency Documentation", "severity": "high", "hours": 24},
                {"component": "Human Oversight Mechanisms", "severity": "high", "hours": 32},
                {"component": "Data Governance", "severity": "medium", "hours": 16},
            ],
        }

        matched_impacts = regulation_impact_map.get(regulation_lower, [])
        if not matched_impacts and affected_areas:
            matched_impacts = [
                {"component": area, "severity": "medium", "hours": 16} for area in affected_areas
            ]
        elif not matched_impacts:
            matched_impacts = [
                {"component": "General Compliance Controls", "severity": "medium", "hours": 24},
                {"component": "Documentation", "severity": "low", "hours": 8},
                {"component": "Monitoring & Alerting", "severity": "low", "hours": 8},
            ]

        severity_map = {
            "critical": BlastRadiusSeverity.CRITICAL,
            "high": BlastRadiusSeverity.HIGH,
            "medium": BlastRadiusSeverity.MEDIUM,
            "low": BlastRadiusSeverity.LOW,
        }

        for impact in matched_impacts:
            item = BlastRadiusItem(
                component=impact["component"],
                regulation=regulation,
                current_status=ComplianceStatus.UNKNOWN,
                projected_status=ComplianceStatus.NON_COMPLIANT,
                impact_severity=severity_map.get(impact["severity"], BlastRadiusSeverity.MEDIUM),
                remediation_effort_hours=impact["hours"],
                description=f"{impact['component']} requires updates for {regulation} compliance",
            )
            affected_items.append(item)

        report.affected_items = affected_items
        report.total_affected_components = len(affected_items)
        report.critical_count = sum(
            1 for i in affected_items if i.impact_severity == BlastRadiusSeverity.CRITICAL
        )
        report.high_count = sum(
            1 for i in affected_items if i.impact_severity == BlastRadiusSeverity.HIGH
        )
        report.medium_count = sum(
            1 for i in affected_items if i.impact_severity == BlastRadiusSeverity.MEDIUM
        )
        report.low_count = sum(
            1 for i in affected_items if i.impact_severity == BlastRadiusSeverity.LOW
        )
        report.total_remediation_hours = sum(i.remediation_effort_hours for i in affected_items)

        report.recommendations = [
            f"Prioritize {report.critical_count} critical-severity components first",
            f"Estimated total effort: {report.total_remediation_hours:.0f} person-hours",
            f"Start with a gap analysis against {regulation} requirements",
            "Create a remediation plan with milestone deadlines",
        ]

        logger.info(
            "Blast radius calculated",
            regulation=regulation,
            affected=report.total_affected_components,
            critical=report.critical_count,
            hours=report.total_remediation_hours,
        )

        return report

    async def list_events(
        self,
        organization_id: UUID | None = None,
        event_type: TwinEventType | None = None,
        limit: int = 50,
    ) -> list[TwinEvent]:
        """List tracked events with optional filters."""
        results = list(self._events)
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]
