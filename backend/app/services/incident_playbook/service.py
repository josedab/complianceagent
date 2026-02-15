"""Incident Response Compliance Playbook Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.incident_playbook.models import (
    Incident,
    IncidentReport,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
    NotificationRequirement,
    Playbook,
    PlaybookStatus,
)


logger = structlog.get_logger()

_DEFAULT_PLAYBOOKS: list[dict] = [
    {
        "name": "Data Breach Response",
        "incident_type": IncidentType.DATA_BREACH,
        "description": "Standard playbook for personal data breaches requiring regulatory notification",
        "steps": [
            {
                "order": 1,
                "action": "Identify scope of breach",
                "role": "Security Lead",
                "sla_hours": 1,
            },
            {"order": 2, "action": "Contain the breach", "role": "Engineering", "sla_hours": 2},
            {"order": 3, "action": "Assess data subjects affected", "role": "DPO", "sla_hours": 4},
            {
                "order": 4,
                "action": "Notify supervisory authority",
                "role": "Legal",
                "sla_hours": 72,
            },
            {
                "order": 5,
                "action": "Notify affected individuals",
                "role": "Communications",
                "sla_hours": 168,
            },
            {"order": 6, "action": "Document root cause", "role": "Engineering", "sla_hours": 336},
        ],
        "notification_requirements": [
            {"jurisdiction": "EU", "authority": "Lead Supervisory Authority", "deadline_hours": 72},
            {"jurisdiction": "US-CA", "authority": "California AG", "deadline_hours": 72},
            {"jurisdiction": "US-NY", "authority": "NY DFS", "deadline_hours": 72},
        ],
        "evidence_checklist": [
            "System logs at time of breach",
            "Access control records",
            "Data flow diagrams for affected systems",
            "List of affected data subjects",
            "Containment action records",
            "Root cause analysis document",
        ],
        "jurisdictions": ["EU", "US-CA", "US-NY", "UK"],
    },
    {
        "name": "Ransomware Response",
        "incident_type": IncidentType.RANSOMWARE,
        "description": "Playbook for ransomware attacks with compliance obligations",
        "steps": [
            {"order": 1, "action": "Isolate affected systems", "role": "IT Ops", "sla_hours": 0.5},
            {
                "order": 2,
                "action": "Activate backup recovery",
                "role": "Engineering",
                "sla_hours": 2,
            },
            {"order": 3, "action": "Engage law enforcement", "role": "Legal", "sla_hours": 24},
            {"order": 4, "action": "Assess data exfiltration", "role": "Security", "sla_hours": 24},
            {
                "order": 5,
                "action": "Restore from clean backups",
                "role": "Engineering",
                "sla_hours": 48,
            },
        ],
        "notification_requirements": [
            {"jurisdiction": "US", "authority": "FBI / CISA", "deadline_hours": 24},
            {"jurisdiction": "EU", "authority": "ENISA", "deadline_hours": 72},
        ],
        "evidence_checklist": [
            "Malware samples",
            "Network traffic logs",
            "Ransom note copy",
            "Affected system inventory",
            "Backup integrity verification",
        ],
        "jurisdictions": ["US", "EU", "UK"],
    },
    {
        "name": "Insider Threat Response",
        "incident_type": IncidentType.INSIDER_THREAT,
        "description": "Playbook for insider threat incidents involving unauthorized data access",
        "steps": [
            {"order": 1, "action": "Revoke user access", "role": "IT Admin", "sla_hours": 0.25},
            {"order": 2, "action": "Preserve digital evidence", "role": "Security", "sla_hours": 1},
            {
                "order": 3,
                "action": "Conduct forensic investigation",
                "role": "Security",
                "sla_hours": 48,
            },
            {"order": 4, "action": "Assess data exposure", "role": "DPO", "sla_hours": 24},
            {"order": 5, "action": "Engage HR and legal", "role": "Legal", "sla_hours": 4},
        ],
        "notification_requirements": [
            {"jurisdiction": "EU", "authority": "DPA", "deadline_hours": 72},
        ],
        "evidence_checklist": [
            "User access logs",
            "File access audit trail",
            "Email/communication records",
            "Device forensic images",
            "HR records",
        ],
        "jurisdictions": ["EU", "US"],
    },
    {
        "name": "Vendor Compromise Response",
        "incident_type": IncidentType.VENDOR_COMPROMISE,
        "description": "Playbook for third-party vendor security incidents",
        "steps": [
            {
                "order": 1,
                "action": "Assess vendor access scope",
                "role": "Vendor Management",
                "sla_hours": 2,
            },
            {"order": 2, "action": "Revoke vendor credentials", "role": "IT Admin", "sla_hours": 1},
            {"order": 3, "action": "Review shared data inventory", "role": "DPO", "sla_hours": 8},
            {
                "order": 4,
                "action": "Request vendor incident report",
                "role": "Legal",
                "sla_hours": 24,
            },
        ],
        "notification_requirements": [
            {"jurisdiction": "EU", "authority": "Lead SA", "deadline_hours": 72},
        ],
        "evidence_checklist": [
            "Vendor access logs",
            "Data sharing agreements",
            "Vendor incident report",
            "Affected data inventory",
        ],
        "jurisdictions": ["EU", "US", "UK"],
    },
    {
        "name": "Unauthorized Access Response",
        "incident_type": IncidentType.UNAUTHORIZED_ACCESS,
        "description": "Playbook for unauthorized system access incidents",
        "steps": [
            {
                "order": 1,
                "action": "Block unauthorized access",
                "role": "Security",
                "sla_hours": 0.5,
            },
            {
                "order": 2,
                "action": "Reset compromised credentials",
                "role": "IT Admin",
                "sla_hours": 1,
            },
            {"order": 3, "action": "Audit access logs", "role": "Security", "sla_hours": 4},
            {"order": 4, "action": "Assess data accessed", "role": "DPO", "sla_hours": 8},
        ],
        "notification_requirements": [],
        "evidence_checklist": [
            "Authentication logs",
            "Session records",
            "IP address traces",
            "Affected system logs",
        ],
        "jurisdictions": ["US", "EU"],
    },
    {
        "name": "API Outage Response",
        "incident_type": IncidentType.API_OUTAGE,
        "description": "Playbook for API outages affecting compliance data flows",
        "steps": [
            {
                "order": 1,
                "action": "Activate status page",
                "role": "Engineering",
                "sla_hours": 0.25,
            },
            {"order": 2, "action": "Identify root cause", "role": "Engineering", "sla_hours": 1},
            {"order": 3, "action": "Assess compliance data impact", "role": "DPO", "sla_hours": 4},
            {"order": 4, "action": "Restore service", "role": "Engineering", "sla_hours": 4},
        ],
        "notification_requirements": [],
        "evidence_checklist": [
            "Service health logs",
            "Error rate metrics",
            "Downtime duration records",
        ],
        "jurisdictions": ["US", "EU"],
    },
]

_NOTIFICATION_DB: dict[str, NotificationRequirement] = {
    "EU": NotificationRequirement(
        jurisdiction="EU",
        authority="Lead Supervisory Authority",
        deadline_hours=72,
        template="GDPR Art. 33 Breach Notification",
        data_required=[
            "nature of breach",
            "categories of data",
            "approximate number of data subjects",
            "DPO contact details",
            "likely consequences",
            "measures taken",
        ],
    ),
    "US-CA": NotificationRequirement(
        jurisdiction="US-CA",
        authority="California Attorney General",
        deadline_hours=72,
        template="CCPA Breach Notice",
        data_required=[
            "description of incident",
            "types of information involved",
            "steps taken",
            "contact information",
        ],
    ),
    "UK": NotificationRequirement(
        jurisdiction="UK",
        authority="ICO",
        deadline_hours=72,
        template="UK GDPR Breach Notification",
        data_required=[
            "nature of breach",
            "categories of data",
            "number of data subjects",
            "DPO contact",
            "likely consequences",
            "measures taken",
        ],
    ),
    "US-NY": NotificationRequirement(
        jurisdiction="US-NY",
        authority="NY Department of Financial Services",
        deadline_hours=72,
        template="23 NYCRR 500 Notification",
        data_required=[
            "date of incident",
            "description",
            "data types affected",
            "remediation steps",
        ],
    ),
    "US": NotificationRequirement(
        jurisdiction="US",
        authority="FBI / CISA",
        deadline_hours=24,
        template="Federal Incident Report",
        data_required=["incident type", "affected systems", "impact assessment", "IOCs"],
    ),
}


class IncidentPlaybookService:
    """Manage incident response playbooks and incidents."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._playbooks: dict[UUID, Playbook] = {}
        self._incidents: dict[UUID, Incident] = {}
        self._init_playbooks()

    def _init_playbooks(self) -> None:
        """Pre-populate with default playbooks."""
        for pb_data in _DEFAULT_PLAYBOOKS:
            playbook = Playbook(
                name=pb_data["name"],
                incident_type=pb_data["incident_type"],
                description=pb_data["description"],
                steps=pb_data["steps"],
                notification_requirements=pb_data["notification_requirements"],
                evidence_checklist=pb_data["evidence_checklist"],
                status=PlaybookStatus.ACTIVE,
                jurisdictions=pb_data["jurisdictions"],
                created_at=datetime.now(UTC),
            )
            self._playbooks[playbook.id] = playbook

    async def list_playbooks(self, incident_type: IncidentType | None = None) -> list[Playbook]:
        """List all playbooks, optionally filtered by incident type."""
        playbooks = list(self._playbooks.values())
        if incident_type:
            playbooks = [p for p in playbooks if p.incident_type == incident_type]
        return playbooks

    async def get_playbook(self, playbook_id: UUID) -> Playbook:
        """Get a specific playbook."""
        playbook = self._playbooks.get(playbook_id)
        if not playbook:
            raise ValueError(f"Playbook not found: {playbook_id}")
        return playbook

    async def create_incident(
        self,
        playbook_id: UUID,
        severity: IncidentSeverity,
        title: str,
        description: str,
        affected_subjects: int,
        jurisdictions: list[str],
    ) -> Incident:
        """Create a new incident from a playbook."""
        playbook = self._playbooks.get(playbook_id)
        if not playbook:
            raise ValueError(f"Playbook not found: {playbook_id}")

        now = datetime.now(UTC)
        incident = Incident(
            playbook_id=playbook_id,
            incident_type=playbook.incident_type,
            severity=severity,
            title=title,
            description=description,
            status=IncidentStatus.DETECTED,
            affected_data_subjects=affected_subjects,
            jurisdictions_affected=jurisdictions,
            timeline=[
                {"event": "Incident detected", "timestamp": now.isoformat(), "actor": "system"}
            ],
            started_at=now,
        )
        self._incidents[incident.id] = incident
        logger.info(
            "Incident created",
            id=str(incident.id),
            type=playbook.incident_type.value,
            severity=severity.value,
        )
        return incident

    async def update_incident_status(self, incident_id: UUID, status: IncidentStatus) -> Incident:
        """Update the status of an incident."""
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        now = datetime.now(UTC)
        incident.status = status
        incident.timeline.append(
            {
                "event": f"Status changed to {status.value}",
                "timestamp": now.isoformat(),
                "actor": "operator",
            }
        )
        if status == IncidentStatus.CLOSED:
            incident.resolved_at = now

        logger.info("Incident status updated", id=str(incident_id), status=status.value)
        return incident

    async def add_evidence(self, incident_id: UUID, evidence_item: str) -> Incident:
        """Add evidence to an incident."""
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        incident.evidence_collected.append(evidence_item)
        incident.timeline.append(
            {
                "event": f"Evidence collected: {evidence_item}",
                "timestamp": datetime.now(UTC).isoformat(),
                "actor": "investigator",
            }
        )
        logger.info("Evidence added", incident_id=str(incident_id), item=evidence_item)
        return incident

    async def get_notification_requirements(
        self, incident_id: UUID
    ) -> list[NotificationRequirement]:
        """Get notification requirements for an incident."""
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        requirements: list[NotificationRequirement] = []
        for jur in incident.jurisdictions_affected:
            if jur in _NOTIFICATION_DB:
                requirements.append(_NOTIFICATION_DB[jur])
        return requirements

    async def generate_incident_report(self, incident_id: UUID) -> IncidentReport:
        """Generate a post-incident compliance report."""
        incident = self._incidents.get(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        playbook = self._playbooks.get(incident.playbook_id)
        now = datetime.now(UTC)

        duration = 0.0
        if incident.started_at:
            end = incident.resolved_at or now
            duration = round((end - incident.started_at).total_seconds() / 3600, 2)

        # Check notification compliance
        notifications_sent_jurs = {n.get("jurisdiction") for n in incident.notifications_sent}
        required_jurs = set(incident.jurisdictions_affected)
        notifications_compliant = required_jurs.issubset(notifications_sent_jurs)

        # Check evidence completeness
        evidence_complete = True
        if playbook:
            for item in playbook.evidence_checklist:
                if item not in incident.evidence_collected:
                    evidence_complete = False
                    break

        report = IncidentReport(
            incident_id=incident_id,
            incident_type=incident.incident_type.value,
            severity=incident.severity.value,
            total_duration_hours=duration,
            notifications_compliant=notifications_compliant,
            evidence_complete=evidence_complete,
            timeline=incident.timeline,
            lessons_learned=[
                "Improve detection time for similar incidents",
                "Update runbooks with lessons from this incident",
                "Review access control policies",
                "Conduct tabletop exercise for team readiness",
            ],
            generated_at=now,
        )
        logger.info("Incident report generated", incident_id=str(incident_id))
        return report

    async def list_incidents(self, status: IncidentStatus | None = None) -> list[Incident]:
        """List all incidents, optionally filtered by status."""
        incidents = list(self._incidents.values())
        if status:
            incidents = [i for i in incidents if i.status == status]
        return incidents
