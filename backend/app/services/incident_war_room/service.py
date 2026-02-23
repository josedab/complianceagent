"""Compliance Incident War Room Service."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.incident_war_room.models import (
    IncidentPhase,
    IncidentSeverity,
    PostMortem,
    TimelineEntry,
    WarRoomIncident,
    WarRoomStats,
)


logger = structlog.get_logger()

# GDPR Art. 33 requires notification within 72 hours
_NOTIFICATION_WINDOW_HOURS = 72

_PHASE_ORDER = [
    IncidentPhase.DETECTED,
    IncidentPhase.TRIAGING,
    IncidentPhase.RESPONDING,
    IncidentPhase.NOTIFYING,
    IncidentPhase.POST_MORTEM,
    IncidentPhase.CLOSED,
]


class IncidentWarRoomService:
    """Manage compliance incidents through their full lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._incidents: dict[str, WarRoomIncident] = {}
        self._post_mortems: list[PostMortem] = []

    async def create_incident(
        self,
        title: str,
        severity: str,
        description: str,
        regulation: str = "",
        stakeholders: list[str] | None = None,
    ) -> WarRoomIncident:
        now = datetime.now(UTC)
        incident = WarRoomIncident(
            title=title,
            severity=IncidentSeverity(severity),
            phase=IncidentPhase.DETECTED,
            description=description,
            regulation=regulation,
            breach_detected_at=now,
            notification_deadline=now + timedelta(hours=_NOTIFICATION_WINDOW_HOURS),
            stakeholders=stakeholders or [],
            created_at=now,
        )
        incident.timeline_events.append(
            TimelineEntry(
                timestamp=now,
                actor="system",
                action="incident_created",
                details=f"Incident created: {title} (severity={severity})",
            )
        )
        self._incidents[str(incident.id)] = incident
        logger.info(
            "Incident created",
            incident_id=str(incident.id),
            severity=severity,
            notification_deadline=str(incident.notification_deadline),
        )
        return incident

    async def advance_phase(self, incident_id: str, actor: str = "system") -> WarRoomIncident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        current_idx = _PHASE_ORDER.index(incident.phase)
        if current_idx >= len(_PHASE_ORDER) - 1:
            raise ValueError(f"Incident already in final phase: {incident.phase.value}")

        old_phase = incident.phase
        incident.phase = _PHASE_ORDER[current_idx + 1]
        now = datetime.now(UTC)

        incident.timeline_events.append(
            TimelineEntry(
                timestamp=now,
                actor=actor,
                action="phase_transition",
                details=f"Phase changed: {old_phase.value} → {incident.phase.value}",
            )
        )

        if incident.phase == IncidentPhase.CLOSED:
            incident.closed_at = now

        logger.info(
            "Incident phase advanced",
            incident_id=incident_id,
            old_phase=old_phase.value,
            new_phase=incident.phase.value,
        )
        return incident

    async def add_timeline_entry(
        self,
        incident_id: str,
        actor: str,
        action: str,
        details: str,
    ) -> WarRoomIncident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        incident.timeline_events.append(
            TimelineEntry(
                timestamp=datetime.now(UTC),
                actor=actor,
                action=action,
                details=details,
            )
        )
        logger.info("Timeline entry added", incident_id=incident_id, action=action)
        return incident

    async def add_evidence(self, incident_id: str, evidence: str) -> WarRoomIncident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        incident.evidence.append(evidence)
        incident.timeline_events.append(
            TimelineEntry(
                timestamp=datetime.now(UTC),
                actor="system",
                action="evidence_added",
                details=f"Evidence collected: {evidence[:80]}",
            )
        )
        logger.info("Evidence added", incident_id=incident_id)
        return incident

    async def generate_post_mortem(self, incident_id: str) -> PostMortem:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")


        post_mortem = PostMortem(
            incident_id=incident.id,
            root_cause=f"Compliance incident involving {incident.regulation or 'unknown regulation'}: {incident.description[:200]}",
            impact_summary=f"Severity {incident.severity.value} incident with {len(incident.timeline_events)} timeline events and {len(incident.evidence)} evidence items",
            lessons_learned=[
                f"Detection to triage should be faster for {incident.severity.value} severity incidents",
                f"Notification deadline was {'met' if incident.notification_deadline and (incident.closed_at or datetime.now(UTC)) <= incident.notification_deadline else 'at risk'}",
                f"Evidence collection captured {len(incident.evidence)} items during response",
            ],
            action_items=[
                f"Review {incident.regulation} compliance controls",
                "Update incident response playbook with findings",
                "Schedule follow-up audit within 30 days",
                "Validate notification procedures meet regulatory deadlines",
            ],
            generated_at=datetime.now(UTC),
        )
        self._post_mortems.append(post_mortem)
        logger.info("Post-mortem generated", incident_id=incident_id, post_mortem_id=str(post_mortem.id))
        return post_mortem

    async def list_incidents(self, phase: str | None = None) -> list[WarRoomIncident]:
        incidents = list(self._incidents.values())
        if phase:
            target_phase = IncidentPhase(phase)
            incidents = [i for i in incidents if i.phase == target_phase]
        return incidents

    async def get_incident(self, incident_id: str) -> WarRoomIncident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        return incident

    def get_stats(self) -> WarRoomStats:
        incidents = list(self._incidents.values())
        by_severity: dict[str, int] = {}
        by_phase: dict[str, int] = {}
        resolution_hours: list[float] = []

        for inc in incidents:
            by_severity[inc.severity.value] = by_severity.get(inc.severity.value, 0) + 1
            by_phase[inc.phase.value] = by_phase.get(inc.phase.value, 0) + 1
            if inc.closed_at and inc.created_at:
                delta = (inc.closed_at - inc.created_at).total_seconds() / 3600
                resolution_hours.append(delta)

        return WarRoomStats(
            total_incidents=len(incidents),
            by_severity=by_severity,
            by_phase=by_phase,
            avg_resolution_hours=round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else 0.0,
            post_mortems_generated=len(self._post_mortems),
        )
