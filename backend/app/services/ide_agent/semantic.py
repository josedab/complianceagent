"""Semantic compliance analysis for IDE integration.

Provides regulation-context hover tooltips, file-level posture scoring,
and compliance panel data for real-time IDE feedback.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class TooltipSeverity(str, Enum):
    """Severity for hover tooltip display."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class RegulationTooltip:
    """Hover tooltip with regulation context for a code location."""

    line: int
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    regulation: str = ""
    article: str = ""
    title: str = ""
    description: str = ""
    severity: TooltipSeverity = TooltipSeverity.INFO
    fix_available: bool = False
    citation_url: str | None = None


@dataclass
class FilePostureScore:
    """Compliance posture score for a single file."""

    file_path: str = ""
    score: float = 100.0
    grade: str = "A+"
    violations_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    frameworks_affected: list[str] = field(default_factory=list)
    last_analyzed: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompliancePanelData:
    """Data for the IDE compliance side panel."""

    repository: str = ""
    overall_score: float = 100.0
    overall_grade: str = "A+"
    files_analyzed: int = 0
    total_violations: int = 0
    critical_violations: int = 0
    frameworks: list[dict[str, Any]] = field(default_factory=list)
    recent_changes: list[dict[str, Any]] = field(default_factory=list)
    top_issues: list[dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


# Regulation citation database for tooltips
REGULATION_CITATIONS: dict[str, dict[str, dict[str, str]]] = {
    "gdpr": {
        "consent": {
            "article": "Article 6-7",
            "title": "Lawfulness of processing & Conditions for consent",
            "description": "Personal data processing requires a lawful basis. Consent must be freely given, specific, informed, and unambiguous.",
            "url": "https://gdpr-info.eu/art-6-gdpr/",
        },
        "data_minimization": {
            "article": "Article 5(1)(c)",
            "title": "Data minimization principle",
            "description": "Personal data shall be adequate, relevant, and limited to what is necessary.",
            "url": "https://gdpr-info.eu/art-5-gdpr/",
        },
        "right_to_erasure": {
            "article": "Article 17",
            "title": "Right to erasure ('right to be forgotten')",
            "description": "Data subjects have the right to obtain erasure of personal data without undue delay.",
            "url": "https://gdpr-info.eu/art-17-gdpr/",
        },
        "data_breach": {
            "article": "Article 33",
            "title": "Notification of a personal data breach",
            "description": "Controller shall notify supervisory authority within 72 hours of becoming aware of a breach.",
            "url": "https://gdpr-info.eu/art-33-gdpr/",
        },
    },
    "hipaa": {
        "phi_encryption": {
            "article": "§164.312(a)(2)(iv)",
            "title": "Encryption and decryption",
            "description": "Implement a mechanism to encrypt and decrypt electronic protected health information.",
            "url": "https://www.law.cornell.edu/cfr/text/45/164.312",
        },
        "audit_controls": {
            "article": "§164.312(b)",
            "title": "Audit controls",
            "description": "Implement hardware, software, and/or procedural mechanisms that record and examine activity.",
            "url": "https://www.law.cornell.edu/cfr/text/45/164.312",
        },
        "access_control": {
            "article": "§164.312(a)(1)",
            "title": "Access control",
            "description": "Implement technical policies and procedures for electronic information systems that maintain ePHI.",
            "url": "https://www.law.cornell.edu/cfr/text/45/164.312",
        },
    },
    "pci_dss": {
        "card_data": {
            "article": "Requirement 3.4",
            "title": "Render PAN unreadable anywhere it is stored",
            "description": "Render PAN unreadable anywhere it is stored using cryptography, truncation, masking, or hashing.",
            "url": "https://www.pcisecuritystandards.org/",
        },
        "encryption": {
            "article": "Requirement 4.1",
            "title": "Protect cardholder data with strong cryptography during transmission",
            "description": "Use strong cryptography and security protocols to safeguard sensitive cardholder data during transmission.",
            "url": "https://www.pcisecuritystandards.org/",
        },
    },
    "eu_ai_act": {
        "transparency": {
            "article": "Article 52",
            "title": "Transparency obligations",
            "description": "Providers shall ensure AI systems intended to interact with natural persons are designed so users are aware they are interacting with an AI.",
            "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
        },
        "risk_classification": {
            "article": "Article 6",
            "title": "Classification of AI systems as high-risk",
            "description": "AI systems shall be classified as high-risk when used in biometric identification, critical infrastructure, education, employment, or law enforcement.",
            "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
        },
    },
}

# Code patterns that map to regulation citations
PATTERN_TO_REGULATION: list[dict[str, Any]] = [
    {
        "pattern": "personal_data|user_data|pii",
        "regulation": "gdpr",
        "topic": "consent",
        "severity": "warning",
    },
    {
        "pattern": "email.*collect|collect.*email",
        "regulation": "gdpr",
        "topic": "data_minimization",
        "severity": "info",
    },
    {
        "pattern": "delete.*user|purge.*data|erasure",
        "regulation": "gdpr",
        "topic": "right_to_erasure",
        "severity": "info",
    },
    {
        "pattern": "breach|incident.*report",
        "regulation": "gdpr",
        "topic": "data_breach",
        "severity": "critical",
    },
    {
        "pattern": "phi|health.*record|patient.*data|medical",
        "regulation": "hipaa",
        "topic": "phi_encryption",
        "severity": "critical",
    },
    {
        "pattern": "audit.*log|access.*log",
        "regulation": "hipaa",
        "topic": "audit_controls",
        "severity": "warning",
    },
    {
        "pattern": "card.*number|pan|credit.*card|cvv",
        "regulation": "pci_dss",
        "topic": "card_data",
        "severity": "critical",
    },
    {
        "pattern": "ai.*model|machine.*learn|neural|prediction",
        "regulation": "eu_ai_act",
        "topic": "transparency",
        "severity": "warning",
    },
    {
        "pattern": "biometric|facial.*recog|fingerprint",
        "regulation": "eu_ai_act",
        "topic": "risk_classification",
        "severity": "critical",
    },
]


class SemanticAnalyzer:
    """Provides semantic compliance analysis for IDE integration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_file_for_tooltips(
        self,
        file_content: str,
        file_path: str,
        language: str = "python",
    ) -> list[RegulationTooltip]:
        """Analyze a file and generate regulation-context hover tooltips."""
        import re

        tooltips: list[RegulationTooltip] = []
        lines = file_content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            line_lower = line.lower()
            for pattern_info in PATTERN_TO_REGULATION:
                if re.search(pattern_info["pattern"], line_lower):
                    reg = pattern_info["regulation"]
                    topic = pattern_info["topic"]
                    citation = REGULATION_CITATIONS.get(reg, {}).get(topic, {})
                    if citation:
                        tooltips.append(
                            RegulationTooltip(
                                line=line_num,
                                column=0,
                                end_line=line_num,
                                end_column=len(line),
                                regulation=reg.upper().replace("_", " "),
                                article=citation.get("article", ""),
                                title=citation.get("title", ""),
                                description=citation.get("description", ""),
                                severity=TooltipSeverity(pattern_info["severity"]),
                                fix_available=pattern_info["severity"] in ("critical", "warning"),
                                citation_url=citation.get("url"),
                            )
                        )

        logger.info(
            "File analyzed for tooltips",
            file=file_path,
            tooltips=len(tooltips),
        )
        return tooltips

    async def get_file_posture(
        self,
        file_content: str,
        file_path: str,
    ) -> FilePostureScore:
        """Calculate compliance posture score for a single file."""
        tooltips = await self.analyze_file_for_tooltips(file_content, file_path)

        critical = sum(1 for t in tooltips if t.severity == TooltipSeverity.CRITICAL)
        warning = sum(1 for t in tooltips if t.severity == TooltipSeverity.WARNING)
        info = sum(1 for t in tooltips if t.severity == TooltipSeverity.INFO)

        # Score: start at 100, deduct per issue
        score = max(0.0, 100.0 - (critical * 15) - (warning * 5) - (info * 1))
        frameworks = list({t.regulation for t in tooltips})

        return FilePostureScore(
            file_path=file_path,
            score=round(score, 1),
            grade=_score_to_grade(score),
            violations_count=len(tooltips),
            critical_count=critical,
            warning_count=warning,
            info_count=info,
            frameworks_affected=frameworks,
        )

    async def get_compliance_panel(
        self,
        repository: str,
        files: dict[str, str] | None = None,
    ) -> CompliancePanelData:
        """Generate compliance panel data for the IDE sidebar."""
        file_scores: list[FilePostureScore] = []
        if files:
            for path, content in files.items():
                score = await self.get_file_posture(content, path)
                file_scores.append(score)

        total_violations = sum(f.violations_count for f in file_scores)
        critical_violations = sum(f.critical_count for f in file_scores)
        avg_score = sum(f.score for f in file_scores) / len(file_scores) if file_scores else 100.0

        # Aggregate frameworks
        all_frameworks: dict[str, int] = {}
        for f in file_scores:
            for fw in f.frameworks_affected:
                all_frameworks[fw] = all_frameworks.get(fw, 0) + 1

        top_issues = sorted(file_scores, key=lambda f: f.score)[:5]

        return CompliancePanelData(
            repository=repository,
            overall_score=round(avg_score, 1),
            overall_grade=_score_to_grade(avg_score),
            files_analyzed=len(file_scores),
            total_violations=total_violations,
            critical_violations=critical_violations,
            frameworks=[
                {"name": fw, "files_affected": count}
                for fw, count in sorted(all_frameworks.items(), key=lambda x: -x[1])
            ],
            top_issues=[
                {
                    "file": f.file_path,
                    "score": f.score,
                    "grade": f.grade,
                    "violations": f.violations_count,
                }
                for f in top_issues
            ],
        )


def _score_to_grade(score: float) -> str:
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 85:
        return "B+"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"
