"""Legal Copilot Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.legal_copilot.models import (
    ContractClause,
    DocumentType,
    LegalCopilotStats,
    LegalDocument,
    ReviewStatus,
)


logger = structlog.get_logger()


class LegalCopilotService:
    """AI-assisted legal document generation and review."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._documents: dict[UUID, LegalDocument] = {}
        self._clauses: dict[UUID, ContractClause] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed sample legal documents."""
        docs = [
            LegalDocument(
                doc_type=DocumentType.DPA_DRAFT,
                title="Data Processing Agreement — Acme Corp & CloudSync Ltd",
                content=(
                    "1. DEFINITIONS AND INTERPRETATION\n"
                    "1.1 'Personal Data' means any information relating to an identified "
                    "or identifiable natural person as defined under GDPR Article 4(1).\n"
                    "1.2 'Processing' shall have the meaning given in GDPR Article 4(2).\n\n"
                    "2. SCOPE AND PURPOSE\n"
                    "2.1 The Processor shall process Personal Data solely for the purpose "
                    "of providing cloud infrastructure services.\n\n"
                    "3. OBLIGATIONS OF THE PROCESSOR\n"
                    "3.1 The Processor shall implement appropriate technical and "
                    "organisational measures pursuant to Article 32 GDPR.\n"
                    "3.2 The Processor shall notify the Controller without undue delay "
                    "upon becoming aware of a personal data breach (Article 33).\n\n"
                    "4. SUB-PROCESSING\n"
                    "4.1 The Processor shall not engage another processor without prior "
                    "written authorisation of the Controller (Article 28(2)).\n\n"
                    "5. DATA TRANSFERS\n"
                    "5.1 Any transfer of Personal Data to a third country shall be subject "
                    "to appropriate safeguards under Chapter V GDPR."
                ),
                citations=[
                    {"regulation": "GDPR", "article": "Article 28", "text": "Processor obligations"},
                    {"regulation": "GDPR", "article": "Article 32", "text": "Security of processing"},
                    {"regulation": "GDPR", "article": "Article 33", "text": "Breach notification"},
                ],
                framework="GDPR",
                jurisdiction="EU",
                status=ReviewStatus.APPROVED,
                author="legal-copilot",
                reviewer="j.martinez@legal.com",
                created_at=datetime(2025, 1, 10, 9, 0, tzinfo=UTC),
                approved_at=datetime(2025, 1, 12, 14, 30, tzinfo=UTC),
            ),
            LegalDocument(
                doc_type=DocumentType.LEGAL_MEMO,
                title="Regulatory Impact Analysis — California CCPA Amendments",
                content=(
                    "MEMORANDUM\n\n"
                    "TO: Chief Privacy Officer\n"
                    "FROM: Legal Compliance Team\n"
                    "RE: CCPA/CPRA Amendments — Impact on Data Broker Operations\n\n"
                    "I. EXECUTIVE SUMMARY\n"
                    "The California Privacy Rights Act (CPRA) amendments effective "
                    "January 2025 impose additional obligations on data brokers.\n\n"
                    "II. KEY CHANGES\n"
                    "A. Expanded definition of 'sensitive personal information' under "
                    "Cal. Civ. Code § 1798.140(ae).\n"
                    "B. New opt-out mechanisms required under § 1798.120.\n"
                    "C. Enhanced enforcement powers granted to the CPPA.\n\n"
                    "III. RECOMMENDED ACTIONS\n"
                    "1. Update privacy notices within 30 days.\n"
                    "2. Implement universal opt-out signal recognition.\n"
                    "3. Conduct data mapping for sensitive PI categories."
                ),
                citations=[
                    {"regulation": "CCPA", "article": "§ 1798.140", "text": "Definitions"},
                    {"regulation": "CPRA", "article": "§ 1798.120", "text": "Opt-out rights"},
                ],
                framework="CCPA",
                jurisdiction="US-CA",
                status=ReviewStatus.IN_REVIEW,
                author="legal-copilot",
                reviewer="s.chen@legal.com",
                created_at=datetime(2025, 2, 5, 11, 0, tzinfo=UTC),
            ),
            LegalDocument(
                doc_type=DocumentType.COMPLIANCE_OPINION,
                title="Opinion on Cross-Border Data Transfer Mechanisms Post-Schrems II",
                content=(
                    "LEGAL OPINION\n\n"
                    "RE: Adequacy of Standard Contractual Clauses for EU-US Transfers\n\n"
                    "1. BACKGROUND\n"
                    "Following the CJEU ruling in Case C-311/18 (Schrems II), "
                    "organisations must conduct Transfer Impact Assessments.\n\n"
                    "2. ANALYSIS\n"
                    "The EU-US Data Privacy Framework adopted July 2023 provides "
                    "a new adequacy basis. However, supplementary measures remain "
                    "advisable for sensitive data categories.\n\n"
                    "3. CONCLUSION\n"
                    "SCCs combined with encryption-in-transit and pseudonymisation "
                    "provide adequate safeguards for the proposed transfers."
                ),
                citations=[
                    {"regulation": "GDPR", "article": "Article 46", "text": "Appropriate safeguards"},
                    {"regulation": "GDPR", "article": "Article 49", "text": "Derogations for transfers"},
                    {"regulation": "CJEU", "article": "Case C-311/18", "text": "Schrems II ruling"},
                ],
                framework="GDPR",
                jurisdiction="EU",
                status=ReviewStatus.APPROVED,
                author="legal-copilot",
                reviewer="a.schmidt@legal.com",
                created_at=datetime(2025, 3, 1, 10, 0, tzinfo=UTC),
                approved_at=datetime(2025, 3, 3, 16, 0, tzinfo=UTC),
            ),
        ]
        for doc in docs:
            self._documents[doc.id] = doc

        logger.info("Legal copilot seeded", document_count=len(self._documents))

    async def generate_dpa(
        self,
        parties: list[str],
        frameworks: list[str],
        jurisdiction: str,
    ) -> LegalDocument:
        """Generate a Data Processing Agreement."""
        party_text = " and ".join(parties) if parties else "Party A and Party B"
        framework_text = ", ".join(frameworks) if frameworks else "GDPR"

        citations = [
            {"regulation": fw, "article": "Article 28", "text": "Processor obligations"}
            for fw in frameworks
        ]
        citations.append(
            {"regulation": framework_text, "article": "Article 32", "text": "Security of processing"}
        )

        content = (
            f"DATA PROCESSING AGREEMENT\n\n"
            f"Between: {party_text}\n"
            f"Jurisdiction: {jurisdiction}\n"
            f"Governing Frameworks: {framework_text}\n\n"
            f"1. DEFINITIONS AND INTERPRETATION\n"
            f"1.1 'Controller' means the party determining the purposes and means "
            f"of processing of Personal Data.\n"
            f"1.2 'Processor' means the party processing Personal Data on behalf "
            f"of the Controller.\n\n"
            f"2. SCOPE OF PROCESSING\n"
            f"2.1 The Processor shall process Personal Data only on documented "
            f"instructions from the Controller.\n"
            f"2.2 Processing activities are limited to those described in Annex I.\n\n"
            f"3. SECURITY MEASURES\n"
            f"3.1 The Processor shall implement technical and organisational measures "
            f"including encryption, access controls, and regular security testing.\n\n"
            f"4. DATA BREACH NOTIFICATION\n"
            f"4.1 The Processor shall notify the Controller within 72 hours of "
            f"becoming aware of a personal data breach.\n\n"
            f"5. DATA SUBJECT RIGHTS\n"
            f"5.1 The Processor shall assist the Controller in responding to data "
            f"subject requests.\n\n"
            f"6. TERM AND TERMINATION\n"
            f"6.1 This Agreement shall remain in effect for the duration of the "
            f"processing activities."
        )

        doc = LegalDocument(
            doc_type=DocumentType.DPA_DRAFT,
            title=f"Data Processing Agreement — {party_text}",
            content=content,
            citations=citations,
            framework=framework_text,
            jurisdiction=jurisdiction,
            status=ReviewStatus.DRAFT,
            author="legal-copilot",
            created_at=datetime.now(UTC),
        )
        self._documents[doc.id] = doc

        logger.info("DPA generated", doc_id=str(doc.id), parties=parties)
        return doc

    async def generate_legal_memo(
        self,
        topic: str,
        framework: str,
        jurisdiction: str,
    ) -> LegalDocument:
        """Generate a legal memorandum."""
        content = (
            f"MEMORANDUM\n\n"
            f"TO: Compliance Team\n"
            f"FROM: Legal Copilot\n"
            f"RE: {topic}\n"
            f"FRAMEWORK: {framework}\n"
            f"JURISDICTION: {jurisdiction}\n\n"
            f"I. EXECUTIVE SUMMARY\n"
            f"This memorandum addresses the regulatory implications of {topic} "
            f"under the {framework} framework within {jurisdiction}.\n\n"
            f"II. REGULATORY BACKGROUND\n"
            f"The {framework} establishes requirements that directly impact "
            f"the subject matter. Key provisions include data protection obligations, "
            f"breach notification requirements, and cross-border transfer restrictions.\n\n"
            f"III. ANALYSIS\n"
            f"Based on current regulatory guidance and enforcement actions, "
            f"the organisation should adopt a risk-based approach to compliance.\n\n"
            f"IV. RECOMMENDATIONS\n"
            f"1. Conduct a gap analysis against {framework} requirements.\n"
            f"2. Update internal policies and procedures.\n"
            f"3. Implement technical controls where applicable.\n"
            f"4. Schedule periodic compliance reviews."
        )

        citations = [
            {"regulation": framework, "article": "General Provisions", "text": f"Applicability to {topic}"},
        ]

        doc = LegalDocument(
            doc_type=DocumentType.LEGAL_MEMO,
            title=f"Legal Memorandum — {topic}",
            content=content,
            citations=citations,
            framework=framework,
            jurisdiction=jurisdiction,
            status=ReviewStatus.DRAFT,
            author="legal-copilot",
            created_at=datetime.now(UTC),
        )
        self._documents[doc.id] = doc

        logger.info("Legal memo generated", doc_id=str(doc.id), topic=topic)
        return doc

    async def review_contract_clause(self, clause_text: str) -> ContractClause:
        """Review a contract clause and provide risk assessment."""
        risk_keywords_high = ["unlimited liability", "indemnify", "sole discretion", "waive"]
        risk_keywords_medium = ["reasonable efforts", "material breach", "termination", "limitation"]

        risk_level = "low"
        recommendation = "Clause appears standard and acceptable."

        lower_text = clause_text.lower()
        for keyword in risk_keywords_high:
            if keyword in lower_text:
                risk_level = "high"
                recommendation = (
                    f"High-risk clause detected containing '{keyword}'. "
                    "Recommend negotiation to limit exposure and add mutual obligations."
                )
                break

        if risk_level == "low":
            for keyword in risk_keywords_medium:
                if keyword in lower_text:
                    risk_level = "medium"
                    recommendation = (
                        f"Clause contains '{keyword}' which requires careful review. "
                        "Consider adding specific thresholds or time limits."
                    )
                    break

        clause = ContractClause(
            clause_type="general",
            text=clause_text,
            risk_level=risk_level,
            recommendation=recommendation,
            framework="contract_law",
        )
        self._clauses[clause.id] = clause

        logger.info("Clause reviewed", clause_id=str(clause.id), risk_level=risk_level)
        return clause

    async def approve_document(self, doc_id: UUID, reviewer: str) -> LegalDocument:
        """Approve a legal document."""
        doc = self._documents.get(doc_id)
        if not doc:
            msg = f"Document {doc_id} not found"
            raise ValueError(msg)

        doc.status = ReviewStatus.APPROVED
        doc.reviewer = reviewer
        doc.approved_at = datetime.now(UTC)

        logger.info("Document approved", doc_id=str(doc_id), reviewer=reviewer)
        return doc

    async def list_documents(
        self,
        doc_type: DocumentType | None = None,
        status: ReviewStatus | None = None,
    ) -> list[LegalDocument]:
        """List legal documents with optional filters."""
        docs = list(self._documents.values())

        if doc_type is not None:
            docs = [d for d in docs if d.doc_type == doc_type]
        if status is not None:
            docs = [d for d in docs if d.status == status]

        return docs

    async def get_stats(self) -> LegalCopilotStats:
        """Get legal copilot statistics."""
        docs = list(self._documents.values())
        total = len(docs)

        by_type: dict[str, int] = {}
        for doc in docs:
            by_type[doc.doc_type.value] = by_type.get(doc.doc_type.value, 0) + 1

        approved = sum(1 for d in docs if d.status == ReviewStatus.APPROVED)

        total_citations = sum(len(d.citations) for d in docs)
        avg_citations = total_citations / total if total > 0 else 0.0

        frameworks = list({d.framework for d in docs if d.framework})

        return LegalCopilotStats(
            total_documents=total,
            by_type=by_type,
            approved=approved,
            avg_citations_per_doc=round(avg_citations, 2),
            frameworks_covered=sorted(frameworks),
        )
