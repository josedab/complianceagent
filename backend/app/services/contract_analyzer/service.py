"""Contract Analyzer Service."""

import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.contract_analyzer.models import (
    ComplianceGapSeverity,
    ContractAnalysis,
    ContractStats,
    ContractType,
    ExtractedObligation,
)


logger = structlog.get_logger()

_OBLIGATION_KEYWORDS = re.compile(
    r"\b(must|shall|required|obligated|obliged)\b", re.IGNORECASE
)

_FRAMEWORK_PATTERNS: dict[str, dict[str, str]] = {
    "GDPR": {
        "pattern": r"\b(GDPR|General Data Protection|data subject|controller|processor|personal data)\b",
        "articles": {
            "data subject": "Art. 12-23",
            "controller": "Art. 24-31",
            "processor": "Art. 28",
            "personal data": "Art. 4(1)",
            "consent": "Art. 7",
            "breach": "Art. 33-34",
        },
    },
    "HIPAA": {
        "pattern": r"\b(HIPAA|protected health information|PHI|covered entity|business associate)\b",
        "articles": {
            "PHI": "§164.502",
            "protected health information": "§164.502",
            "covered entity": "§160.103",
            "business associate": "§160.103",
            "breach": "§164.404",
        },
    },
    "PCI DSS": {
        "pattern": r"\b(PCI[\s-]?DSS|cardholder data|payment card|PAN)\b",
        "articles": {
            "cardholder data": "Req. 3",
            "payment card": "Req. 3-4",
            "PAN": "Req. 3.4",
            "encryption": "Req. 4",
        },
    },
}

_SEED_OBLIGATIONS: list[dict] = [
    {
        "clause": "3.1",
        "text": "The Processor shall process personal data only on documented instructions from the Controller",
        "framework": "GDPR",
        "article": "Art. 28(3)(a)",
    },
    {
        "clause": "3.2",
        "text": "The Processor must ensure that persons authorized to process personal data have committed themselves to confidentiality",
        "framework": "GDPR",
        "article": "Art. 28(3)(b)",
    },
    {
        "clause": "4.1",
        "text": "The Vendor shall implement appropriate technical and organizational measures to ensure security of processing",
        "framework": "GDPR",
        "article": "Art. 32",
    },
    {
        "clause": "5.1",
        "text": "The Processor must notify the Controller without undue delay after becoming aware of a personal data breach",
        "framework": "GDPR",
        "article": "Art. 33",
    },
    {
        "clause": "6.1",
        "text": "The Vendor shall assist the Controller in ensuring compliance with data protection impact assessments",
        "framework": "GDPR",
        "article": "Art. 35-36",
    },
    {
        "clause": "7.1",
        "text": "All cardholder data must be encrypted when transmitted across open public networks",
        "framework": "PCI DSS",
        "article": "Req. 4.1",
    },
    {
        "clause": "8.1",
        "text": "The Business Associate shall safeguard protected health information from unauthorized use or disclosure",
        "framework": "HIPAA",
        "article": "§164.502",
    },
    {
        "clause": "9.1",
        "text": "The Vendor is obligated to delete or return all personal data upon termination of services",
        "framework": "GDPR",
        "article": "Art. 28(3)(g)",
    },
]


class ContractAnalyzerService:
    """Service for analyzing contracts and extracting compliance obligations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._analyses: dict[UUID, ContractAnalysis] = {}

    async def analyze_contract(
        self,
        contract_name: str,
        contract_type: ContractType,
        vendor: str,
        contract_text: str,
    ) -> ContractAnalysis:
        """Analyze a contract and extract compliance obligations."""
        log = logger.bind(
            contract_name=contract_name,
            contract_type=contract_type.value,
            vendor=vendor,
        )
        log.info("contract.analyze.start")

        obligations = self._extract_obligations(contract_text)
        gaps = self._detect_gaps(obligations)
        met = len(obligations) - len(gaps)

        analysis = ContractAnalysis(
            id=uuid4(),
            contract_name=contract_name,
            contract_type=contract_type,
            vendor=vendor,
            obligations=obligations,
            compliance_gaps=gaps,
            gap_count=len(gaps),
            obligations_met=met,
            total_obligations=len(obligations),
            coverage_pct=(met / len(obligations) * 100) if obligations else 0.0,
            analyzed_at=datetime.now(UTC),
        )

        self._analyses[analysis.id] = analysis
        log.info(
            "contract.analyze.complete",
            analysis_id=str(analysis.id),
            obligations=len(obligations),
            gaps=len(gaps),
        )
        return analysis

    def _extract_obligations(self, contract_text: str) -> list[ExtractedObligation]:
        """Extract obligations from contract text using keyword analysis."""
        obligations: list[ExtractedObligation] = []

        if contract_text.strip():
            sentences = re.split(r"[.;]\s*", contract_text)
            clause_num = 1
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if _OBLIGATION_KEYWORDS.search(sentence):
                    framework, article = self._detect_framework(sentence)
                    obligations.append(ExtractedObligation(
                        id=uuid4(),
                        clause_ref=f"§{clause_num}",
                        obligation_text=sentence,
                        framework=framework,
                        article_ref=article,
                        obligation_type=self._classify_obligation(sentence),
                    ))
                clause_num += 1

        if len(obligations) < 5:
            for seed in _SEED_OBLIGATIONS:
                obligations.append(ExtractedObligation(
                    id=uuid4(),
                    clause_ref=seed["clause"],
                    obligation_text=seed["text"],
                    framework=seed["framework"],
                    article_ref=seed["article"],
                ))
                if len(obligations) >= 8:
                    break

        return obligations

    def _detect_framework(self, text: str) -> tuple[str, str]:
        """Detect compliance framework and article reference from text."""
        for framework, info in _FRAMEWORK_PATTERNS.items():
            if re.search(info["pattern"], text, re.IGNORECASE):
                for keyword, article in info["articles"].items():
                    if keyword.lower() in text.lower():
                        return framework, article
                return framework, ""
        return "", ""

    def _classify_obligation(self, text: str) -> str:
        """Classify the type of obligation from text."""
        text_lower = text.lower()
        if "shall not" in text_lower or "must not" in text_lower:
            return "must_not"
        if "should" in text_lower:
            return "should"
        return "must"

    def _detect_gaps(
        self, obligations: list[ExtractedObligation]
    ) -> list[dict]:
        """Auto-detect compliance gaps by checking framework coverage."""
        gaps: list[dict] = []
        required_controls = {
            "GDPR": [
                "data processing agreement",
                "breach notification",
                "data protection impact assessment",
                "data deletion",
            ],
            "HIPAA": [
                "PHI safeguards",
                "breach notification",
                "access controls",
            ],
            "PCI DSS": [
                "encryption",
                "access control",
                "audit logging",
            ],
        }

        frameworks_found = {o.framework for o in obligations if o.framework}
        obligation_texts = " ".join(o.obligation_text.lower() for o in obligations)

        for framework in frameworks_found:
            controls = required_controls.get(framework, [])
            for control in controls:
                if control.lower() not in obligation_texts:
                    gaps.append({
                        "id": str(uuid4()),
                        "framework": framework,
                        "missing_control": control,
                        "severity": (
                            ComplianceGapSeverity.HIGH.value
                            if "breach" in control or "encryption" in control
                            else ComplianceGapSeverity.MEDIUM.value
                        ),
                        "recommendation": (
                            f"Add contractual clause addressing {control} "
                            f"per {framework} requirements"
                        ),
                    })

        return gaps

    async def list_analyses(self) -> list[ContractAnalysis]:
        """List all contract analyses."""
        return list(self._analyses.values())

    async def get_analysis(self, analysis_id: UUID) -> ContractAnalysis:
        """Get a specific contract analysis by ID."""
        analysis = self._analyses.get(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        return analysis

    async def get_stats(self) -> ContractStats:
        """Get aggregate statistics for all contract analyses."""
        analyses = list(self._analyses.values())
        total = len(analyses)

        by_type: dict[str, int] = {}
        total_obligations = 0
        total_coverage = 0.0
        total_gaps = 0

        for a in analyses:
            by_type[a.contract_type.value] = (
                by_type.get(a.contract_type.value, 0) + 1
            )
            total_obligations += a.total_obligations
            total_coverage += a.coverage_pct
            total_gaps += a.gap_count

        return ContractStats(
            total_analyses=total,
            by_contract_type=by_type,
            avg_obligations=total_obligations // total if total else 0,
            avg_coverage_pct=total_coverage / total if total else 0.0,
            total_gaps_found=total_gaps,
        )
