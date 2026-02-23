"""Regulatory Intelligence Feed Service."""

from datetime import UTC, datetime
from uuid import UUID  # noqa: TC003

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.regulatory_intel_feed.models import (
    ContentFormat,
    DigestReport,
    FeedCategory,
    FeedPreferences,
    IntelArticle,
    IntelFeedStats,
)


logger = structlog.get_logger()


class RegulatoryIntelFeedService:
    """Curated regulatory intelligence feed with AI analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._articles: dict[UUID, IntelArticle] = {}
        self._subscriptions: dict[str, FeedPreferences] = {}
        self._digests: dict[UUID, DigestReport] = {}
        self._digests_sent: int = 0
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed realistic regulatory news articles."""
        articles = [
            IntelArticle(
                title="EU AI Act Enters Into Force — Compliance Timeline Published",
                summary=(
                    "The European AI Act officially entered into force on 1 August 2024. "
                    "Prohibited AI practices must be phased out within 6 months, while "
                    "high-risk AI system requirements take effect after 36 months."
                ),
                category=FeedCategory.BREAKING,
                regulation="EU AI Act",
                jurisdiction="EU",
                impact_score=9.5,
                source="European Commission",
                source_url="https://ec.europa.eu/ai-act",
                ai_analysis=(
                    "This represents the most significant AI regulation globally. "
                    "Organisations deploying AI in the EU must immediately classify their "
                    "systems by risk tier. High-risk AI used in employment, credit scoring, "
                    "and law enforcement faces the strictest requirements including mandatory "
                    "conformity assessments and human oversight provisions."
                ),
                action_items=[
                    "Inventory all AI systems and classify by risk tier",
                    "Identify prohibited AI practices for immediate phase-out",
                    "Establish AI governance committee",
                    "Begin conformity assessment planning for high-risk systems",
                ],
                published_at=datetime(2025, 1, 15, 8, 0, tzinfo=UTC),
            ),
            IntelArticle(
                title="SEC Finalises Climate Disclosure Rules for Public Companies",
                summary=(
                    "The SEC adopted final rules requiring public companies to disclose "
                    "climate-related risks, greenhouse gas emissions, and transition plans "
                    "in annual reports beginning fiscal year 2025."
                ),
                category=FeedCategory.GUIDANCE,
                regulation="SEC Climate Disclosure",
                jurisdiction="US",
                impact_score=8.7,
                source="Securities and Exchange Commission",
                source_url="https://www.sec.gov/climate-disclosure",
                ai_analysis=(
                    "Public companies must prepare for Scope 1 and Scope 2 emissions "
                    "reporting with phased Scope 3 requirements. Large accelerated filers "
                    "face the earliest deadlines. Companies should begin establishing "
                    "measurement infrastructure and internal controls over climate data."
                ),
                action_items=[
                    "Assess filer category and applicable deadlines",
                    "Implement GHG emissions measurement systems",
                    "Develop climate risk assessment methodology",
                    "Engage auditors for climate data assurance",
                ],
                published_at=datetime(2025, 1, 20, 14, 30, tzinfo=UTC),
            ),
            IntelArticle(
                title="CNIL Issues €32M Fine for GDPR Cookie Consent Violations",
                summary=(
                    "France's data protection authority fined a major ad-tech company "
                    "€32 million for deploying cookies without valid user consent and "
                    "using dark patterns in consent interfaces."
                ),
                category=FeedCategory.ENFORCEMENT,
                regulation="GDPR",
                jurisdiction="EU-FR",
                impact_score=7.8,
                source="CNIL",
                source_url="https://www.cnil.fr/enforcement",
                ai_analysis=(
                    "This enforcement action signals intensifying scrutiny of cookie "
                    "consent mechanisms. The CNIL specifically cited pre-ticked checkboxes "
                    "and asymmetric button design as violations. Organisations should audit "
                    "their consent management platforms for compliance with the latest "
                    "EDPB guidelines on consent."
                ),
                action_items=[
                    "Audit cookie consent mechanisms for dark patterns",
                    "Review CMP configuration against EDPB guidelines",
                    "Ensure reject-all option is equally prominent as accept-all",
                ],
                published_at=datetime(2025, 2, 3, 10, 0, tzinfo=UTC),
            ),
            IntelArticle(
                title="NIST Releases Updated Cybersecurity Framework 2.0",
                summary=(
                    "NIST published CSF 2.0 with expanded governance function, improved "
                    "supply chain risk management guidance, and enhanced alignment with "
                    "international standards including ISO 27001:2022."
                ),
                category=FeedCategory.GUIDANCE,
                regulation="NIST CSF",
                jurisdiction="US",
                impact_score=8.2,
                source="NIST",
                source_url="https://www.nist.gov/cyberframework",
                ai_analysis=(
                    "CSF 2.0 introduces a sixth function (Govern) emphasising "
                    "cybersecurity governance at the organisational level. The update "
                    "provides better mapping to other frameworks and includes new "
                    "implementation examples for small and medium enterprises."
                ),
                action_items=[
                    "Map current controls to CSF 2.0 categories",
                    "Assess gaps in the new Govern function",
                    "Update risk assessment methodology",
                ],
                published_at=datetime(2025, 2, 10, 9, 0, tzinfo=UTC),
            ),
            IntelArticle(
                title="Brazil LGPD Authority Issues Guidance on International Data Transfers",
                summary=(
                    "The ANPD published detailed guidance on mechanisms for international "
                    "transfers of personal data, including standard contractual clauses "
                    "and binding corporate rules under the LGPD."
                ),
                category=FeedCategory.ANALYSIS,
                regulation="LGPD",
                jurisdiction="BR",
                impact_score=7.0,
                source="ANPD Brazil",
                source_url="https://www.gov.br/anpd/transfer-guidance",
                ai_analysis=(
                    "The ANPD's approach closely mirrors GDPR Chapter V provisions. "
                    "Multinational companies already using GDPR SCCs may adapt these "
                    "for LGPD compliance. However, adequacy decisions differ from EU "
                    "equivalents and must be assessed independently."
                ),
                action_items=[
                    "Review existing data transfer mechanisms for Brazil applicability",
                    "Prepare LGPD-specific transfer impact assessments",
                    "Update records of processing activities for Brazilian data",
                ],
                published_at=datetime(2025, 2, 18, 12, 0, tzinfo=UTC),
            ),
            IntelArticle(
                title="PCI DSS 4.0 Transition Deadline — 31 March 2025",
                summary=(
                    "All organisations processing payment card data must fully comply "
                    "with PCI DSS v4.0 by 31 March 2025. The previous version 3.2.1 "
                    "is officially retired."
                ),
                category=FeedCategory.DEADLINE,
                regulation="PCI DSS",
                jurisdiction="Global",
                impact_score=9.0,
                source="PCI Security Standards Council",
                source_url="https://www.pcisecuritystandards.org/v4",
                ai_analysis=(
                    "Key changes in v4.0 include customised validation approaches, "
                    "enhanced authentication requirements (MFA everywhere), and new "
                    "e-commerce security provisions. Organisations must complete their "
                    "transition before the deadline to avoid non-compliance findings."
                ),
                action_items=[
                    "Complete gap assessment against PCI DSS 4.0 requirements",
                    "Implement enhanced authentication controls",
                    "Update self-assessment questionnaire or prepare for QSA audit",
                ],
                published_at=datetime(2025, 3, 1, 8, 0, tzinfo=UTC),
            ),
            IntelArticle(
                title="UK ICO Launches Consultation on AI and Data Protection",
                summary=(
                    "The UK Information Commissioner's Office opened a public consultation "
                    "on the intersection of AI systems and UK data protection law, "
                    "focusing on lawful basis for AI training and automated decision-making."
                ),
                category=FeedCategory.OPINION,
                regulation="UK GDPR",
                jurisdiction="UK",
                impact_score=6.5,
                source="UK ICO",
                source_url="https://ico.org.uk/ai-consultation",
                ai_analysis=(
                    "The consultation addresses critical questions about legitimate "
                    "interest as a lawful basis for AI training data. Responses may shape "
                    "future ICO guidance diverging from EU EDPB positions post-Brexit."
                ),
                action_items=[
                    "Submit consultation response by deadline",
                    "Review lawful basis assessments for AI training activities",
                    "Monitor for divergence from EU AI Act requirements",
                ],
                published_at=datetime(2025, 3, 10, 11, 0, tzinfo=UTC),
            ),
            IntelArticle(
                title="Singapore PDPC Updates Advisory Guidelines on Data Intermediaries",
                summary=(
                    "The Personal Data Protection Commission of Singapore released "
                    "updated advisory guidelines clarifying obligations of data "
                    "intermediaries and processors under the PDPA."
                ),
                category=FeedCategory.GUIDANCE,
                regulation="PDPA",
                jurisdiction="SG",
                impact_score=6.0,
                source="PDPC Singapore",
                source_url="https://www.pdpc.gov.sg/guidelines",
                ai_analysis=(
                    "The updated guidelines introduce clearer distinctions between "
                    "data intermediaries and full data controllers. Cloud service "
                    "providers operating in Singapore should review their contractual "
                    "arrangements to ensure alignment with the updated framework."
                ),
                action_items=[
                    "Review data intermediary status under updated guidelines",
                    "Update data processing agreements for Singapore operations",
                ],
                published_at=datetime(2025, 3, 15, 7, 0, tzinfo=UTC),
            ),
        ]
        for article in articles:
            self._articles[article.id] = article

        logger.info("Regulatory intel feed seeded", article_count=len(self._articles))

    async def get_feed(
        self,
        category: FeedCategory | None = None,
        jurisdiction: str | None = None,
        limit: int = 20,
    ) -> list[IntelArticle]:
        """Get regulatory intelligence feed with optional filters."""
        articles = list(self._articles.values())

        if category is not None:
            articles = [a for a in articles if a.category == category]
        if jurisdiction is not None:
            articles = [a for a in articles if a.jurisdiction == jurisdiction]

        articles.sort(key=lambda a: a.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return articles[:limit]

    async def subscribe(self, user_id: str, preferences: dict) -> FeedPreferences:
        """Subscribe a user to the regulatory intelligence feed."""
        categories = [
            FeedCategory(c) for c in preferences.get("categories", [])
            if c in FeedCategory.__members__.values() or c in [e.value for e in FeedCategory]
        ]

        prefs = FeedPreferences(
            user_id=user_id,
            categories=categories,
            jurisdictions=preferences.get("jurisdictions", []),
            frameworks=preferences.get("frameworks", []),
            format=ContentFormat(preferences.get("format", "summary")),
            delivery=preferences.get("delivery", ["email"]),
            digest_frequency=preferences.get("digest_frequency", "daily"),
        )
        self._subscriptions[user_id] = prefs

        logger.info("User subscribed to feed", user_id=user_id)
        return prefs

    async def generate_digest(self, user_id: str, period: str) -> DigestReport:
        """Generate a digest report for a user."""
        prefs = self._subscriptions.get(user_id)
        articles = list(self._articles.values())

        if prefs:
            if prefs.categories:
                articles = [a for a in articles if a.category in prefs.categories]
            if prefs.jurisdictions:
                articles = [a for a in articles if a.jurisdiction in prefs.jurisdictions]

        articles.sort(key=lambda a: a.impact_score, reverse=True)

        highlights = [
            f"[{a.category.value.upper()}] {a.title} (impact: {a.impact_score})"
            for a in articles[:5]
        ]

        digest = DigestReport(
            user_id=user_id,
            period=period,
            articles=articles,
            highlights=highlights,
            generated_at=datetime.now(UTC),
        )
        self._digests[digest.id] = digest
        self._digests_sent += 1

        logger.info("Digest generated", user_id=user_id, period=period, article_count=len(articles))
        return digest

    async def list_articles(self, limit: int = 50) -> list[IntelArticle]:
        """List all articles."""
        articles = list(self._articles.values())
        articles.sort(key=lambda a: a.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return articles[:limit]

    async def get_stats(self) -> IntelFeedStats:
        """Get regulatory intelligence feed statistics."""
        articles = list(self._articles.values())

        by_category: dict[str, int] = {}
        by_jurisdiction: dict[str, int] = {}
        for article in articles:
            by_category[article.category.value] = by_category.get(article.category.value, 0) + 1
            by_jurisdiction[article.jurisdiction] = by_jurisdiction.get(article.jurisdiction, 0) + 1

        return IntelFeedStats(
            total_articles=len(articles),
            by_category=by_category,
            by_jurisdiction=by_jurisdiction,
            subscribers=len(self._subscriptions),
            digests_sent=self._digests_sent,
        )
