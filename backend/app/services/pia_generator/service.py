"""Privacy Impact Assessment Generator Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pia_generator.models import (
    DataCategory,
    DataFlow,
    LegalBasis,
    PIADocument,
    PIAStats,
    PIAStatus,
)


logger = structlog.get_logger()

_SEED_DATA_FLOWS: list[DataFlow] = [
    DataFlow(
        id=uuid4(),
        source="User Registration Form",
        destination="PostgreSQL Database",
        data_categories=[DataCategory.PERSONAL],
        purpose="Account creation and identity verification",
        legal_basis=LegalBasis.CONTRACT,
        retention_period="Duration of account + 30 days",
        cross_border=False,
        safeguards=["Encryption at rest", "TLS in transit"],
    ),
    DataFlow(
        id=uuid4(),
        source="Web Application",
        destination="Cloud Analytics Platform",
        data_categories=[DataCategory.PSEUDONYMIZED],
        purpose="Usage analytics and product improvement",
        legal_basis=LegalBasis.LEGITIMATE_INTEREST,
        retention_period="12 months rolling",
        cross_border=True,
        safeguards=["Standard contractual clauses", "Data pseudonymization"],
    ),
    DataFlow(
        id=uuid4(),
        source="Checkout Service",
        destination="Payment Processor",
        data_categories=[DataCategory.SENSITIVE],
        purpose="Payment processing and fraud prevention",
        legal_basis=LegalBasis.CONTRACT,
        retention_period="7 years (regulatory requirement)",
        cross_border=True,
        safeguards=["PCI DSS compliance", "Tokenization", "End-to-end encryption"],
    ),
    DataFlow(
        id=uuid4(),
        source="Patient Portal",
        destination="Electronic Health Records System",
        data_categories=[DataCategory.SPECIAL_CATEGORY],
        purpose="Healthcare service delivery",
        legal_basis=LegalBasis.VITAL_INTEREST,
        retention_period="10 years after last treatment",
        cross_border=False,
        safeguards=["HIPAA compliance", "Role-based access control", "Audit logging"],
    ),
    DataFlow(
        id=uuid4(),
        source="HR Portal",
        destination="HR Management System",
        data_categories=[DataCategory.PERSONAL, DataCategory.SENSITIVE],
        purpose="Employee records management and payroll",
        legal_basis=LegalBasis.LEGAL_OBLIGATION,
        retention_period="Duration of employment + 6 years",
        cross_border=False,
        safeguards=["Access controls", "Encryption", "Regular audits"],
    ),
]


class PIAGeneratorService:
    """Service for generating and managing Privacy Impact Assessments."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._pias: dict[UUID, PIADocument] = {}

    async def generate_pia(self, repo: str, title: str) -> PIADocument:
        """Generate a new Privacy Impact Assessment for a repository."""
        log = logger.bind(repo=repo, title=title)
        log.info("pia.generate.start")

        data_flows = [
            DataFlow(
                id=uuid4(),
                source=f.source,
                destination=f.destination,
                data_categories=list(f.data_categories),
                purpose=f.purpose,
                legal_basis=f.legal_basis,
                retention_period=f.retention_period,
                cross_border=f.cross_border,
                safeguards=list(f.safeguards),
            )
            for f in _SEED_DATA_FLOWS
        ]

        risks = self._assess_risks(data_flows)
        mitigations = self._suggest_mitigations(risks)

        cross_border_count = sum(1 for f in data_flows if f.cross_border)
        has_special = any(
            DataCategory.SPECIAL_CATEGORY in f.data_categories for f in data_flows
        )
        risk_level = (
            "high"
            if has_special or cross_border_count > 2
            else "medium" if cross_border_count > 0 else "low"
        )

        pia = PIADocument(
            id=uuid4(),
            title=title,
            repo=repo,
            status=PIAStatus.DRAFT,
            data_flows=data_flows,
            risks=risks,
            mitigations=mitigations,
            overall_risk_level=risk_level,
            generated_at=datetime.now(UTC),
        )

        self._pias[pia.id] = pia
        log.info("pia.generate.complete", pia_id=str(pia.id), risk_level=risk_level)
        return pia

    def _assess_risks(self, data_flows: list[DataFlow]) -> list[dict]:
        """Auto-generate risks based on detected data flows."""
        risks: list[dict] = []

        cross_border = [f for f in data_flows if f.cross_border]
        if cross_border:
            risks.append({
                "id": str(uuid4()),
                "title": "Cross-border data transfer risk",
                "description": (
                    f"{len(cross_border)} data flow(s) involve cross-border transfers"
                ),
                "severity": "high",
                "likelihood": "medium",
                "affected_flows": [str(f.id) for f in cross_border],
            })

        special = [
            f
            for f in data_flows
            if DataCategory.SPECIAL_CATEGORY in f.data_categories
        ]
        if special:
            risks.append({
                "id": str(uuid4()),
                "title": "Special category data processing",
                "description": (
                    "Processing of special category data requires additional safeguards"
                ),
                "severity": "critical",
                "likelihood": "high",
                "affected_flows": [str(f.id) for f in special],
            })

        sensitive = [
            f
            for f in data_flows
            if DataCategory.SENSITIVE in f.data_categories
        ]
        if sensitive:
            risks.append({
                "id": str(uuid4()),
                "title": "Sensitive data exposure",
                "description": (
                    "Sensitive data flows may be vulnerable to unauthorized access"
                ),
                "severity": "high",
                "likelihood": "medium",
                "affected_flows": [str(f.id) for f in sensitive],
            })

        risks.append({
            "id": str(uuid4()),
            "title": "Data retention compliance",
            "description": (
                "Retention periods must be verified against regulatory requirements"
            ),
            "severity": "medium",
            "likelihood": "low",
            "affected_flows": [str(f.id) for f in data_flows],
        })

        return risks

    def _suggest_mitigations(self, risks: list[dict]) -> list[dict]:
        """Suggest mitigations for identified risks."""
        mitigation_map = {
            "critical": {
                "action": "Implement enhanced safeguards immediately",
                "controls": [
                    "Explicit consent mechanism",
                    "Data Protection Officer review",
                    "Regular impact reassessment",
                ],
            },
            "high": {
                "action": "Implement additional controls before processing",
                "controls": [
                    "Encryption at rest and in transit",
                    "Access control review",
                    "Standard contractual clauses",
                ],
            },
            "medium": {
                "action": "Monitor and review controls periodically",
                "controls": [
                    "Automated retention enforcement",
                    "Periodic compliance audit",
                ],
            },
        }

        mitigations: list[dict] = []
        for risk in risks:
            severity = risk.get("severity", "medium")
            template = mitigation_map.get(severity, mitigation_map["medium"])
            mitigations.append({
                "risk_id": risk["id"],
                "action": template["action"],
                "controls": template["controls"],
                "status": "proposed",
            })

        return mitigations

    async def approve_pia(self, pia_id: UUID, approver: str) -> PIADocument:
        """Approve a PIA document."""
        log = logger.bind(pia_id=str(pia_id), approver=approver)

        pia = self._pias.get(pia_id)
        if not pia:
            log.warning("pia.approve.not_found")
            raise ValueError(f"PIA {pia_id} not found")

        pia.status = PIAStatus.APPROVED
        pia.dpo_approved = True
        pia.approved_by = approver
        pia.approved_at = datetime.now(UTC)

        log.info("pia.approved")
        return pia

    async def export_pia(
        self, pia_id: UUID, format: str = "pdf"
    ) -> dict:
        """Export a PIA document in the specified format."""
        log = logger.bind(pia_id=str(pia_id), format=format)

        pia = self._pias.get(pia_id)
        if not pia:
            log.warning("pia.export.not_found")
            raise ValueError(f"PIA {pia_id} not found")

        content = {
            "format": format,
            "title": pia.title,
            "repo": pia.repo,
            "status": pia.status.value,
            "overall_risk_level": pia.overall_risk_level,
            "data_flows_count": len(pia.data_flows),
            "risks_count": len(pia.risks),
            "mitigations_count": len(pia.mitigations),
            "generated_at": (
                pia.generated_at.isoformat() if pia.generated_at else None
            ),
            "exported_at": datetime.now(UTC).isoformat(),
        }

        log.info("pia.exported", format=format)
        return content

    async def list_pias(
        self, status: PIAStatus | None = None
    ) -> list[PIADocument]:
        """List all PIAs, optionally filtered by status."""
        pias = list(self._pias.values())
        if status:
            pias = [p for p in pias if p.status == status]
        return pias

    async def get_stats(self) -> PIAStats:
        """Get aggregate PIA statistics."""
        pias = list(self._pias.values())
        total = len(pias)

        by_status: dict[str, int] = {}
        by_risk_level: dict[str, int] = {}
        total_flows = 0
        cross_border = 0

        for pia in pias:
            by_status[pia.status.value] = by_status.get(pia.status.value, 0) + 1
            by_risk_level[pia.overall_risk_level] = (
                by_risk_level.get(pia.overall_risk_level, 0) + 1
            )
            total_flows += len(pia.data_flows)
            cross_border += sum(1 for f in pia.data_flows if f.cross_border)

        return PIAStats(
            total_assessments=total,
            by_status=by_status,
            by_risk_level=by_risk_level,
            avg_data_flows_per_pia=total_flows / total if total else 0.0,
            cross_border_flows=cross_border,
        )
