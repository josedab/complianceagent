"""Incident-to-Compliance Auto-Remediation service."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import structlog

from app.services.incident_remediation.models import (
    BreachNotification,
    ComplianceIncident,
    IncidentSeverity,
    IncidentSource,
    RemediationAction,
    RemediationStatus,
)

logger = structlog.get_logger()

_incidents: list[ComplianceIncident] = []


def _seed_data() -> None:
    if _incidents:
        return
    _incidents.extend([
        ComplianceIncident(
            id=uuid4(), title="Unencrypted PII in API Response",
            description="Datadog alert: /api/users endpoint returning SSN in plaintext response body.",
            source=IncidentSource.DATADOG, severity=IncidentSeverity.CRITICAL,
            status=RemediationStatus.PR_CREATED,
            affected_frameworks=["GDPR", "HIPAA", "PCI-DSS"],
            affected_controls=["GDPR-Art32", "HIPAA-164.312(a)"],
            affected_files=["src/api/users.py", "src/models/user.py"],
            cvss_score=8.5, compliance_impact_score=9.2,
            remediation_pr_url="https://github.com/example/pr/142",
            breach_notification_required=True,
            detected_at=datetime.utcnow() - timedelta(hours=4),
        ),
        ComplianceIncident(
            id=uuid4(), title="Disabled Audit Logging on Payment Service",
            description="Splunk detected gap in audit logs for payment processing service lasting 45 minutes.",
            source=IncidentSource.SPLUNK, severity=IncidentSeverity.HIGH,
            status=RemediationStatus.REMEDIATING,
            affected_frameworks=["PCI-DSS", "SOC 2"],
            affected_controls=["PCI-10.2", "SOC2-CC7.2"],
            affected_files=["src/services/payment.py", "config/logging.yaml"],
            cvss_score=6.8, compliance_impact_score=7.5,
            detected_at=datetime.utcnow() - timedelta(hours=2),
        ),
        ComplianceIncident(
            id=uuid4(), title="Excessive Data Retention in Analytics DB",
            description="Elastic Security found user behavior data older than 90-day retention policy.",
            source=IncidentSource.ELASTIC, severity=IncidentSeverity.MEDIUM,
            status=RemediationStatus.DETECTED,
            affected_frameworks=["GDPR"],
            affected_controls=["GDPR-Art5(1)(e)"],
            affected_files=["src/jobs/analytics_cleanup.py"],
            cvss_score=4.2, compliance_impact_score=5.8,
            detected_at=datetime.utcnow() - timedelta(minutes=30),
        ),
    ])


class IncidentRemediationService:
    """Service for incident-to-compliance auto-remediation."""

    def __init__(self) -> None:
        _seed_data()

    async def list_incidents(
        self, severity: IncidentSeverity | None = None,
        status: RemediationStatus | None = None,
    ) -> list[ComplianceIncident]:
        result = list(_incidents)
        if severity:
            result = [i for i in result if i.severity == severity]
        if status:
            result = [i for i in result if i.status == status]
        return result

    async def get_incident(self, incident_id: UUID) -> ComplianceIncident | None:
        return next((i for i in _incidents if i.id == incident_id), None)

    async def ingest_incident(
        self, title: str, description: str,
        source: IncidentSource, severity: IncidentSeverity,
    ) -> ComplianceIncident:
        if not title or not title.strip():
            raise ValueError("Incident title must not be empty")
        if not description or not description.strip():
            raise ValueError("Incident description must not be empty")
        frameworks = self._classify_frameworks(title, description)
        incident = ComplianceIncident(
            id=uuid4(), title=title, description=description,
            source=source, severity=severity,
            status=RemediationStatus.ANALYZING,
            affected_frameworks=frameworks,
            breach_notification_required=severity == IncidentSeverity.CRITICAL,
        )
        _incidents.append(incident)
        logger.info("incident.ingested", incident_id=str(incident.id), severity=severity.value)
        return incident

    async def get_remediation_actions(self, incident_id: UUID) -> list[RemediationAction]:
        incident = await self.get_incident(incident_id)
        if not incident:
            return []
        actions = [
            RemediationAction(
                id=uuid4(), incident_id=incident_id,
                action_type="code_fix", description="Add data masking to API response",
                file_path=incident.affected_files[0] if incident.affected_files else "",
                code_patch="# Apply PII masking filter\nresponse = mask_pii(response)",
                priority=1, estimated_effort_minutes=15, automated=True,
            ),
            RemediationAction(
                id=uuid4(), incident_id=incident_id,
                action_type="config_update", description="Enable encryption at rest",
                file_path="config/security.yaml",
                code_patch="encryption:\n  at_rest: true\n  algorithm: AES-256-GCM",
                priority=2, estimated_effort_minutes=10, automated=True,
            ),
        ]
        return actions

    async def generate_breach_notification(self, incident_id: UUID) -> BreachNotification | None:
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        if not incident.breach_notification_required:
            return None
        return BreachNotification(
            id=uuid4(), incident_id=incident_id,
            regulation="GDPR", authority="Data Protection Authority",
            deadline=incident.detected_at + timedelta(hours=72),
            draft_text=f"Pursuant to GDPR Article 33, we are notifying your authority of a personal data breach: {incident.title}. "
                       f"The breach was detected on {incident.detected_at.isoformat()} and affects the following data categories.",
            affected_individuals_count=12000,
            data_categories=["name", "email", "IP address"],
        )

    def _classify_frameworks(self, title: str, description: str) -> list[str]:
        text = f"{title} {description}".lower()
        frameworks = []
        if any(kw in text for kw in ["pii", "personal", "gdpr", "consent", "data subject"]):
            frameworks.append("GDPR")
        if any(kw in text for kw in ["phi", "hipaa", "health", "patient", "medical"]):
            frameworks.append("HIPAA")
        if any(kw in text for kw in ["payment", "cardholder", "pci", "card"]):
            frameworks.append("PCI-DSS")
        if any(kw in text for kw in ["audit", "soc", "control"]):
            frameworks.append("SOC 2")
        return frameworks or ["General"]
