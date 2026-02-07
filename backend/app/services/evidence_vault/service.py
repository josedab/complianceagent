"""Compliance Evidence Vault Service."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evidence_vault.models import (
    AuditReport,
    AuditorRole,
    AuditorSession,
    ControlFramework,
    ControlMapping,
    EvidenceChain,
    EvidenceItem,
    EvidenceType,
)

logger = structlog.get_logger()

# SOC 2 Type II control mappings
_SOC2_CONTROLS = [
    ("CC1.1", "Control Environment"),
    ("CC1.2", "Board Oversight"),
    ("CC2.1", "Information and Communication"),
    ("CC3.1", "Risk Assessment"),
    ("CC4.1", "Monitoring Activities"),
    ("CC5.1", "Control Activities"),
    ("CC6.1", "Logical Access Security"),
    ("CC6.2", "Access Authentication"),
    ("CC6.3", "Access Authorization"),
    ("CC7.1", "System Operations Monitoring"),
    ("CC7.2", "Incident Management"),
    ("CC8.1", "Change Management"),
    ("CC9.1", "Risk Mitigation"),
]


class EvidenceVaultService:
    """Immutable evidence repository with auditor portal."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._chains: dict[ControlFramework, EvidenceChain] = {}
        self._auditor_sessions: dict[UUID, AuditorSession] = {}
        self._reports: dict[UUID, AuditReport] = {}

    async def store_evidence(
        self,
        evidence_type: EvidenceType,
        title: str,
        description: str,
        content: str,
        framework: ControlFramework,
        control_id: str,
        control_name: str = "",
        source: str = "",
        metadata: dict | None = None,
    ) -> EvidenceItem:
        """Store a new evidence item in the immutable vault."""
        chain = self._chains.get(framework)
        if not chain:
            chain = EvidenceChain(framework=framework)
            self._chains[framework] = chain

        previous_hash = chain.items[-1].content_hash if chain.items else ""

        content_hash = hashlib.sha256(
            (content + previous_hash).encode()
        ).hexdigest()

        item = EvidenceItem(
            evidence_type=evidence_type,
            title=title,
            description=description,
            content_hash=content_hash,
            framework=framework,
            control_id=control_id,
            control_name=control_name,
            collected_at=datetime.now(UTC),
            source=source,
            metadata=metadata or {},
            previous_hash=previous_hash,
        )

        chain.items.append(item)
        chain.chain_hash = content_hash

        logger.info(
            "Evidence stored",
            framework=framework.value,
            control=control_id,
            hash=content_hash[:12],
        )
        return item

    async def verify_chain(self, framework: ControlFramework) -> bool:
        """Verify the integrity of an evidence chain."""
        chain = self._chains.get(framework)
        if not chain or not chain.items:
            return True

        for i, item in enumerate(chain.items):
            if i == 0:
                continue
            if item.previous_hash != chain.items[i - 1].content_hash:
                logger.error(
                    "Chain integrity violation",
                    framework=framework.value,
                    item=str(item.id),
                    index=i,
                )
                chain.verified = False
                return False

        chain.verified = True
        chain.last_verified_at = datetime.now(UTC)
        logger.info("Chain verified", framework=framework.value, items=len(chain.items))
        return True

    async def get_evidence(
        self,
        framework: ControlFramework | None = None,
        control_id: str | None = None,
        evidence_type: EvidenceType | None = None,
        limit: int = 50,
    ) -> list[EvidenceItem]:
        """Query evidence items with filters."""
        items: list[EvidenceItem] = []
        chains = [self._chains[framework]] if framework and framework in self._chains else list(self._chains.values())

        for chain in chains:
            for item in chain.items:
                if control_id and item.control_id != control_id:
                    continue
                if evidence_type and item.evidence_type != evidence_type:
                    continue
                items.append(item)

        return sorted(items, key=lambda i: i.collected_at or datetime.min, reverse=True)[:limit]

    async def get_control_mappings(self, framework: ControlFramework) -> list[ControlMapping]:
        """Get control-to-evidence mappings for a framework."""
        chain = self._chains.get(framework, EvidenceChain())

        controls = _SOC2_CONTROLS if framework == ControlFramework.SOC2 else []
        mappings = []

        for control_id, control_name in controls:
            evidence_ids = [
                item.id for item in chain.items if item.control_id == control_id
            ]
            coverage = min(100.0, len(evidence_ids) * 25.0)
            mappings.append(ControlMapping(
                control_id=control_id,
                control_name=control_name,
                framework=framework,
                evidence_ids=evidence_ids,
                coverage_pct=coverage,
                status="complete" if coverage >= 75 else ("partial" if coverage > 0 else "incomplete"),
            ))

        return mappings

    async def create_auditor_session(
        self,
        auditor_email: str,
        auditor_name: str,
        firm: str = "",
        role: AuditorRole = AuditorRole.VIEWER,
        frameworks: list[ControlFramework] | None = None,
        expires_hours: int = 72,
    ) -> AuditorSession:
        """Create a read-only auditor portal session."""
        from datetime import timedelta

        session = AuditorSession(
            auditor_email=auditor_email,
            auditor_name=auditor_name,
            firm=firm,
            role=role,
            frameworks=frameworks or [ControlFramework.SOC2],
            expires_at=datetime.now(UTC) + timedelta(hours=expires_hours),
            created_at=datetime.now(UTC),
        )

        self._auditor_sessions[session.id] = session
        logger.info("Auditor session created", email=auditor_email, firm=firm)
        return session

    async def get_auditor_session(self, session_id: UUID) -> AuditorSession | None:
        """Get an auditor session."""
        session = self._auditor_sessions.get(session_id)
        if session and session.expires_at and session.expires_at < datetime.now(UTC):
            session.is_active = False
        return session

    async def list_auditor_sessions(self) -> list[AuditorSession]:
        """List all auditor sessions."""
        return list(self._auditor_sessions.values())

    async def generate_report(
        self,
        framework: ControlFramework,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        report_format: str = "pdf",
    ) -> AuditReport:
        """Generate an audit report for a framework."""
        mappings = await self.get_control_mappings(framework)

        total = len(mappings)
        with_evidence = sum(1 for m in mappings if m.evidence_ids)
        coverage = (with_evidence / total * 100) if total else 0

        report = AuditReport(
            framework=framework,
            title=f"{framework.value.upper()} Compliance Report",
            period_start=period_start or datetime.now(UTC),
            period_end=period_end or datetime.now(UTC),
            total_controls=total,
            controls_with_evidence=with_evidence,
            coverage_pct=round(coverage, 1),
            control_mappings=mappings,
            generated_at=datetime.now(UTC),
            report_format=report_format,
        )

        self._reports[report.id] = report
        logger.info(
            "Audit report generated",
            framework=framework.value,
            coverage=f"{coverage:.1f}%",
        )
        return report

    async def get_report(self, report_id: UUID) -> AuditReport | None:
        """Get a generated report."""
        return self._reports.get(report_id)
