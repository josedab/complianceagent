"""Regulation Changelog Diff Viewer service."""

from __future__ import annotations

from datetime import datetime, timedelta

import structlog

from app.services.regulation_diff.models import (
    ArticleChange,
    ChangeSeverity,
    ChangeType,
    RegulationDiff,
    RegulationVersion,
)

logger = structlog.get_logger()

_VERSIONS: list[RegulationVersion] = [
    RegulationVersion(id="gdpr-v1", regulation="GDPR", version="2016/679", title="General Data Protection Regulation (Original)",
        effective_date=datetime(2018, 5, 25), total_articles=99, total_words=88000,
        source_url="https://eur-lex.europa.eu/eli/reg/2016/679/oj"),
    RegulationVersion(id="gdpr-v2", regulation="GDPR", version="2024/1689-amend", title="GDPR as amended by AI Act cross-references",
        effective_date=datetime(2024, 8, 1), total_articles=99, total_words=89200,
        source_url="https://eur-lex.europa.eu/eli/reg/2024/1689"),
    RegulationVersion(id="hipaa-v1", regulation="HIPAA", version="2013-final", title="HIPAA Omnibus Rule (Final)",
        effective_date=datetime(2013, 9, 23), total_articles=45, total_words=62000,
        source_url="https://www.federalregister.gov/documents/2013/01/25"),
    RegulationVersion(id="hipaa-v2", regulation="HIPAA", version="2024-nprm", title="HIPAA Security Rule Update (NPRM)",
        effective_date=datetime(2025, 3, 1), total_articles=48, total_words=67500,
        source_url="https://www.federalregister.gov/documents/2024"),
    RegulationVersion(id="pci-v1", regulation="PCI-DSS", version="3.2.1", title="PCI-DSS v3.2.1",
        effective_date=datetime(2018, 5, 1), total_articles=12, total_words=35000),
    RegulationVersion(id="pci-v2", regulation="PCI-DSS", version="4.0.1", title="PCI-DSS v4.0.1",
        effective_date=datetime(2024, 6, 1), total_articles=12, total_words=42000),
]

_DIFFS: list[RegulationDiff] = [
    RegulationDiff(
        id="gdpr-diff-1", regulation="GDPR", from_version="2016/679", to_version="2024/1689-amend",
        total_changes=8, critical_changes=2, articles_modified=5, articles_added=3,
        ai_summary="The AI Act (Regulation 2024/1689) introduces cross-references to GDPR for AI systems processing personal data. Key changes: (1) New recital clarifying GDPR applies to all AI training data, (2) Added Art. 10a on data governance for AI, (3) Modified Art. 22 automated decision-making to reference AI Act risk categories.",
        impact_assessment="HIGH: Organizations using AI systems must now cross-reference both GDPR and AI Act. Automated decision-making under Art. 22 now triggers AI Act obligations for high-risk systems.",
        changes=[
            ArticleChange(article="Art. 22", section="Automated Decision-Making", change_type=ChangeType.MODIFICATION, severity=ChangeSeverity.CRITICAL,
                old_text="The data subject shall have the right not to be subject to a decision based solely on automated processing.",
                new_text="The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling by AI systems as defined in Regulation (EU) 2024/1689.",
                summary="Expanded scope to explicitly include AI systems per EU AI Act.", impact_on_code="Update automated decision-making checks to include AI system classification.",
                affected_controls=["GDPR-Art22", "AIACT-Art6"]),
            ArticleChange(article="Art. 10a", section="Data Governance for AI", change_type=ChangeType.ADDITION, severity=ChangeSeverity.CRITICAL,
                new_text="Personal data used for training AI systems shall be subject to data governance measures ensuring data quality, relevance, and representativeness.",
                summary="New article requiring data governance for AI training data.", impact_on_code="Add data quality validation for ML training pipelines.",
                affected_controls=["GDPR-Art10a", "AIACT-Art10"]),
            ArticleChange(article="Recital 71", section="Profiling", change_type=ChangeType.MODIFICATION, severity=ChangeSeverity.MAJOR,
                old_text="The data subject should have the right not to be subject to profiling.",
                new_text="The data subject should have the right not to be subject to profiling, which includes inference by AI systems.",
                summary="Clarified that AI inference constitutes profiling.", impact_on_code="Flag AI inference endpoints as profiling under GDPR."),
        ],
    ),
    RegulationDiff(
        id="pci-diff-1", regulation="PCI-DSS", from_version="3.2.1", to_version="4.0.1",
        total_changes=64, critical_changes=12, articles_modified=12, articles_added=0,
        ai_summary="PCI-DSS v4.0.1 introduces significant changes: (1) Customized approach for meeting requirements, (2) Enhanced authentication (MFA everywhere), (3) Targeted risk analysis replaces blanket requirements, (4) New e-commerce/anti-phishing requirements.",
        impact_assessment="CRITICAL: All PCI-DSS compliant organizations must migrate to v4.0.1 by March 31, 2025. Major code changes required for authentication, logging, and encryption.",
        changes=[
            ArticleChange(article="Req. 8.3.6", section="Multi-Factor Authentication", change_type=ChangeType.MODIFICATION, severity=ChangeSeverity.CRITICAL,
                old_text="MFA for remote access to CDE.",
                new_text="MFA for ALL access to the CDE, not just remote access.",
                summary="MFA now required for all CDE access, not just remote.", impact_on_code="Implement MFA on all CDE-accessing endpoints including internal.",
                affected_controls=["PCI-8.3.6"]),
            ArticleChange(article="Req. 6.4.3", section="Payment Page Scripts", change_type=ChangeType.ADDITION, severity=ChangeSeverity.CRITICAL,
                new_text="All payment page scripts that are loaded and executed in the consumer's browser are managed with a method to confirm script integrity.",
                summary="New requirement for payment page script integrity verification.", impact_on_code="Add Subresource Integrity (SRI) to all payment page scripts.",
                affected_controls=["PCI-6.4.3"]),
        ],
    ),
]


class RegulationDiffService:
    """Service for regulation changelog diff viewing."""

    async def list_versions(self, regulation: str | None = None) -> list[RegulationVersion]:
        if regulation:
            return [v for v in _VERSIONS if v.regulation.lower() == regulation.lower()]
        return list(_VERSIONS)

    async def get_version(self, version_id: str) -> RegulationVersion | None:
        return next((v for v in _VERSIONS if v.id == version_id), None)

    async def list_diffs(self, regulation: str | None = None) -> list[RegulationDiff]:
        if regulation:
            return [d for d in _DIFFS if d.regulation.lower() == regulation.lower()]
        return list(_DIFFS)

    async def get_diff(self, diff_id: str) -> RegulationDiff | None:
        return next((d for d in _DIFFS if d.id == diff_id), None)

    async def compare_versions(self, from_version_id: str, to_version_id: str) -> RegulationDiff | None:
        v_from = await self.get_version(from_version_id)
        v_to = await self.get_version(to_version_id)
        if not v_from or not v_to:
            return None
        return next(
            (d for d in _DIFFS if d.from_version == v_from.version and d.to_version == v_to.version),
            None,
        )
