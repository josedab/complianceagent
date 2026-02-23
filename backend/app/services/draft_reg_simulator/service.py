"""Draft Regulation Impact Simulator Service."""


import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.draft_reg_simulator.models import (
    DraftRegulation,
    DraftStatus,
    ImpactAnalysis,
    ImpactScope,
    SimulationStats,
)


logger = structlog.get_logger()

_FRAMEWORK_KEYWORDS: dict[str, list[str]] = {
    "GDPR": ["personal data", "data subject", "consent", "erasure", "portability", "processing", "controller", "processor", "dpo", "privacy"],
    "HIPAA": ["health", "phi", "protected health", "medical", "patient", "healthcare", "covered entity", "hipaa"],
    "PCI-DSS": ["payment", "card", "cardholder", "pan", "tokenization", "merchant", "acquirer", "pci"],
    "SOC2": ["availability", "confidentiality", "processing integrity", "trust service", "service organization"],
}

_SEED_DRAFTS: list[dict] = [
    {
        "title": "EU AI Act — High-Risk AI Systems Amendment",
        "jurisdiction": "EU",
        "source_url": "https://eur-lex.europa.eu/draft/ai-act-amendment-2025",
        "draft_text": "This regulation establishes requirements for high-risk AI systems processing personal data. Controllers must ensure AI-driven decisions respect data subject rights including consent withdrawal and erasure requests. Automated processing must include human oversight and transparency obligations.",
        "status": "committee",
        "sponsoring_body": "European Parliament",
    },
    {
        "title": "US Federal Privacy Rights Act",
        "jurisdiction": "US",
        "source_url": "https://congress.gov/bill/119th/s-privacy-2025",
        "draft_text": "Establishes federal baseline for consumer privacy protection. Requires covered entities to obtain consent before processing personal data for targeted advertising. Creates a private right of action for data breaches affecting health information and payment card data.",
        "status": "proposed",
        "sponsoring_body": "US Senate Commerce Committee",
    },
    {
        "title": "Digital Markets Compliance Directive",
        "jurisdiction": "EU",
        "source_url": "https://eur-lex.europa.eu/draft/dma-compliance-2025",
        "draft_text": "Gatekeepers must provide interoperability for core platform services. Requires transparent processing of merchant payment data with cardholder tokenization. Service organizations must demonstrate availability and processing integrity through annual audits.",
        "status": "floor_vote",
        "sponsoring_body": "European Commission",
    },
    {
        "title": "Healthcare Data Modernization Act",
        "jurisdiction": "US",
        "source_url": "https://congress.gov/bill/119th/hr-health-data-2025",
        "draft_text": "Modernizes HIPAA requirements for cloud-based health systems. Covered entities must implement zero-trust architecture for protected health information. Patient data portability must support FHIR standards. Medical device manufacturers must ensure PHI encryption at rest and in transit.",
        "status": "committee",
        "sponsoring_body": "US House Energy and Commerce Committee",
    },
]


class DraftRegSimulatorService:
    """Simulate the impact of draft regulations on codebase compliance."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._drafts: dict[str, DraftRegulation] = {}
        self._analyses: dict[str, ImpactAnalysis] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        for draft_def in _SEED_DRAFTS:
            draft = DraftRegulation(
                title=draft_def["title"],
                jurisdiction=draft_def["jurisdiction"],
                source_url=draft_def["source_url"],
                draft_text=draft_def["draft_text"],
                status=DraftStatus(draft_def["status"]),
                sponsoring_body=draft_def["sponsoring_body"],
            )
            self._drafts[str(draft.id)] = draft

    async def simulate_draft(self, draft_id: str, repos: list[str] | None = None) -> ImpactAnalysis:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise ValueError(f"Draft regulation not found: {draft_id}")

        text_lower = draft.draft_text.lower()
        affected_frameworks: list[str] = []
        total_keyword_hits = 0

        for framework, keywords in _FRAMEWORK_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in text_lower)
            if hits > 0:
                affected_frameworks.append(framework)
                total_keyword_hits += hits

        # Determine impact scope based on keyword coverage
        if total_keyword_hits >= 10:
            scope = ImpactScope.TRANSFORMATIVE
        elif total_keyword_hits >= 6:
            scope = ImpactScope.BROAD
        elif total_keyword_hits >= 3:
            scope = ImpactScope.MODERATE
        else:
            scope = ImpactScope.NARROW

        code_changes = total_keyword_hits * 5
        effort_hours = total_keyword_hits * 8.0
        risk_score = min(round(total_keyword_hits / 15.0, 2), 1.0)

        preparation_tasks: list[str] = []
        for fw in affected_frameworks:
            preparation_tasks.append(f"Audit current {fw} compliance controls")
            preparation_tasks.append(f"Gap analysis for {fw} requirements in draft text")
        preparation_tasks.append("Engage legal counsel for regulatory interpretation")
        preparation_tasks.append("Estimate engineering resources for compliance updates")

        analysis = ImpactAnalysis(
            draft_id=draft.id,
            affected_repos=repos or ["backend-api", "frontend-app"],
            affected_frameworks=affected_frameworks,
            code_changes_needed=code_changes,
            estimated_effort_hours=effort_hours,
            impact_scope=scope,
            preparation_tasks=preparation_tasks,
            risk_score=risk_score,
        )
        self._analyses[str(analysis.id)] = analysis
        logger.info(
            "Draft regulation simulated",
            draft_id=draft_id,
            affected_frameworks=affected_frameworks,
            impact_scope=scope.value,
        )
        return analysis

    async def list_drafts(self, status: str | None = None) -> list[DraftRegulation]:
        drafts = list(self._drafts.values())
        if status:
            target_status = DraftStatus(status)
            drafts = [d for d in drafts if d.status == target_status]
        return drafts

    async def get_analysis(self, analysis_id: str) -> ImpactAnalysis:
        analysis = self._analyses.get(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        return analysis

    def get_stats(self) -> SimulationStats:
        drafts = list(self._drafts.values())
        analyses = list(self._analyses.values())
        by_status: dict[str, int] = {}
        by_jurisdiction: dict[str, int] = {}
        effort_hours: list[float] = []

        for d in drafts:
            by_status[d.status.value] = by_status.get(d.status.value, 0) + 1
            by_jurisdiction[d.jurisdiction] = by_jurisdiction.get(d.jurisdiction, 0) + 1

        for a in analyses:
            effort_hours.append(a.estimated_effort_hours)

        return SimulationStats(
            total_drafts=len(drafts),
            by_status=by_status,
            by_jurisdiction=by_jurisdiction,
            total_analyses=len(analyses),
            avg_effort_hours=round(sum(effort_hours) / len(effort_hours), 1) if effort_hours else 0.0,
        )
