"""Regulatory filing service for compliance submissions and authority management."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.regulatory_filing.models import (
    AuthorityType,
    FilingStats,
    FilingStatus,
    FilingTemplate,
    FilingType,
    RegulatoryAuthority,
    RegulatoryFiling,
)


logger = structlog.get_logger()


class RegulatoryFilingService:
    """Service for managing regulatory filings and authority submissions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._filings: dict[UUID, RegulatoryFiling] = {}
        self._authorities = self._seed_authorities()
        self._templates = self._seed_templates()

    def _seed_authorities(self) -> list[RegulatoryAuthority]:
        """Seed regulatory authorities."""
        return [
            RegulatoryAuthority(
                id="ico-uk",
                name="Information Commissioner's Office",
                authority_type=AuthorityType.dpa,
                jurisdiction="United Kingdom",
                api_endpoint="https://api.ico.org.uk/filings",
                accepts_electronic=True,
            ),
            RegulatoryAuthority(
                id="cnil-fr",
                name="Commission Nationale de l'Informatique et des Libertés",
                authority_type=AuthorityType.dpa,
                jurisdiction="France",
                api_endpoint="https://api.cnil.fr/filings",
                accepts_electronic=True,
            ),
            RegulatoryAuthority(
                id="bfdi-de",
                name="Bundesbeauftragte für den Datenschutz",
                authority_type=AuthorityType.dpa,
                jurisdiction="Germany",
                api_endpoint="https://api.bfdi.bund.de/filings",
                accepts_electronic=True,
            ),
            RegulatoryAuthority(
                id="hhs-us",
                name="U.S. Department of Health and Human Services",
                authority_type=AuthorityType.hhs,
                jurisdiction="United States",
                api_endpoint="https://api.hhs.gov/hipaa/filings",
                accepts_electronic=True,
            ),
            RegulatoryAuthority(
                id="sec-us",
                name="U.S. Securities and Exchange Commission",
                authority_type=AuthorityType.sec,
                jurisdiction="United States",
                api_endpoint="https://api.sec.gov/filings",
                accepts_electronic=True,
            ),
            RegulatoryAuthority(
                id="pci-global",
                name="PCI Security Standards Council",
                authority_type=AuthorityType.pci_council,
                jurisdiction="Global",
                api_endpoint="https://api.pcissc.org/filings",
                accepts_electronic=True,
            ),
        ]

    def _seed_templates(self) -> list[FilingTemplate]:
        """Seed filing templates."""
        return [
            FilingTemplate(
                id="tpl-gdpr-art30",
                filing_type=FilingType.gdpr_art30,
                authority_id="ico-uk",
                template_fields=[
                    "controller_name",
                    "processing_purposes",
                    "data_categories",
                    "recipients",
                    "retention_periods",
                    "technical_measures",
                ],
                required_attachments=["processing_register"],
                description="GDPR Article 30 Records of Processing Activities",
            ),
            FilingTemplate(
                id="tpl-dpia",
                filing_type=FilingType.dpia_submission,
                authority_id="cnil-fr",
                template_fields=[
                    "processing_description",
                    "necessity_assessment",
                    "risk_assessment",
                    "mitigation_measures",
                    "dpo_opinion",
                ],
                required_attachments=["risk_matrix", "dpo_sign_off"],
                description="Data Protection Impact Assessment submission",
            ),
            FilingTemplate(
                id="tpl-breach-notify",
                filing_type=FilingType.breach_notification,
                authority_id="bfdi-de",
                template_fields=[
                    "breach_description",
                    "data_affected",
                    "individuals_affected",
                    "consequences",
                    "measures_taken",
                    "contact_details",
                ],
                required_attachments=["incident_report"],
                description="Data breach notification to supervisory authority",
            ),
            FilingTemplate(
                id="tpl-annual-report",
                filing_type=FilingType.annual_report,
                authority_id="hhs-us",
                template_fields=[
                    "reporting_period",
                    "compliance_summary",
                    "incidents",
                    "training_records",
                    "audit_results",
                ],
                required_attachments=["compliance_report", "audit_certificate"],
                description="Annual compliance report submission",
            ),
            FilingTemplate(
                id="tpl-registration",
                filing_type=FilingType.registration,
                authority_id="ico-uk",
                template_fields=[
                    "organization_name",
                    "dpo_contact",
                    "processing_activities",
                    "legal_basis",
                ],
                required_attachments=[],
                description="Data controller registration with supervisory authority",
            ),
        ]

    def _find_template(self, filing_type: FilingType, authority_id: str) -> FilingTemplate | None:
        """Find a matching template for a filing type and authority."""
        for template in self._templates:
            if template.filing_type == filing_type and template.authority_id == authority_id:
                return template
        for template in self._templates:
            if template.filing_type == filing_type:
                return template
        return None

    async def generate_filing(
        self,
        filing_type: FilingType,
        authority_id: str,
        data: dict,
    ) -> RegulatoryFiling:
        """Generate a filing auto-populated from template."""
        template = self._find_template(filing_type, authority_id)
        content: dict = {}
        if template:
            for field_name in template.template_fields:
                content[field_name] = data.get(field_name, "")
            content["_template_id"] = template.id
            content["_required_attachments"] = template.required_attachments
        else:
            content = dict(data)

        now = datetime.now(UTC)
        filing = RegulatoryFiling(
            id=uuid4(),
            filing_type=filing_type,
            authority_id=authority_id,
            title=data.get("title", f"{filing_type.value} filing"),
            content=content,
            status=FilingStatus.draft,
            deadline=now + timedelta(days=30),
        )
        self._filings[filing.id] = filing
        logger.info(
            "Filing generated",
            filing_id=str(filing.id),
            type=filing_type.value,
            authority=authority_id,
        )
        return filing

    async def submit_filing(self, filing_id: UUID) -> RegulatoryFiling:
        """Submit a filing, changing status to submitted."""
        if filing_id not in self._filings:
            raise ValueError(f"Filing not found: {filing_id}")
        filing = self._filings[filing_id]
        if filing.status not in (FilingStatus.draft, FilingStatus.ready):
            raise ValueError(f"Filing cannot be submitted in status: {filing.status.value}")
        filing.status = FilingStatus.submitted
        filing.submitted_at = datetime.now(UTC)
        filing.reference_number = f"REF-{filing.filing_type.value.upper()}-{str(filing.id)[:8].upper()}"
        logger.info(
            "Filing submitted",
            filing_id=str(filing_id),
            reference=filing.reference_number,
        )
        return filing

    async def list_authorities(self) -> list[RegulatoryAuthority]:
        """List all regulatory authorities."""
        return self._authorities

    async def list_templates(self) -> list[FilingTemplate]:
        """List all filing templates."""
        return self._templates

    async def list_filings(self) -> list[RegulatoryFiling]:
        """List all filings."""
        return list(self._filings.values())

    async def get_stats(self) -> FilingStats:
        """Get aggregate filing statistics."""
        filings = list(self._filings.values())
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        on_time = 0
        total_with_deadline = 0

        for filing in filings:
            type_key = filing.filing_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            status_key = filing.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
            if filing.deadline:
                total_with_deadline += 1
                if (filing.submitted_at and filing.submitted_at <= filing.deadline) or (filing.status == FilingStatus.draft and datetime.now(UTC) <= filing.deadline):
                    on_time += 1

        on_time_pct = (on_time / total_with_deadline * 100) if total_with_deadline else 100.0
        return FilingStats(
            total_filings=len(filings),
            by_type=by_type,
            by_status=by_status,
            on_time_pct=round(on_time_pct, 1),
            authorities_connected=len(self._authorities),
        )
