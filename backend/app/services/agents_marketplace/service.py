"""Compliance Agents Marketplace Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents_marketplace.models import (
    AgentCategory,
    AgentInstallation,
    AgentReview,
    AgentStatus,
    InstallStatus,
    MarketplaceAgent,
    MarketplaceStats,
)


logger = structlog.get_logger()

_SEED_AGENTS: list[MarketplaceAgent] = [
    MarketplaceAgent(
        name="GDPR Data Flow Scanner",
        slug="gdpr-data-flow-scanner",
        description="Scans codebase for personal data flows and generates GDPR Article 30 records of processing activities.",
        category=AgentCategory.SCANNER,
        author="compliance-tools",
        version="1.2.0",
        mcp_tool_name="marketplace/gdpr-data-flow",
        status=AgentStatus.PUBLISHED,
        downloads=3420,
        rating=4.7,
        rating_count=89,
        tags=["gdpr", "data-flow", "privacy"],
        frameworks=["GDPR"],
        published_at=datetime(2026, 1, 15, tzinfo=UTC),
    ),
    MarketplaceAgent(
        name="HIPAA PHI Detector",
        slug="hipaa-phi-detector",
        description="AI-powered detection of Protected Health Information in code, configs, and logs with remediation suggestions.",
        category=AgentCategory.CHECKER,
        author="healthtech-sec",
        version="2.0.1",
        mcp_tool_name="marketplace/hipaa-phi-detect",
        status=AgentStatus.PUBLISHED,
        downloads=2180,
        rating=4.5,
        rating_count=56,
        tags=["hipaa", "phi", "healthcare"],
        frameworks=["HIPAA"],
        published_at=datetime(2026, 1, 20, tzinfo=UTC),
    ),
    MarketplaceAgent(
        name="PCI-DSS Auto-Fixer",
        slug="pci-dss-auto-fixer",
        description="Automatically generates fixes for PCI-DSS violations including tokenization patterns and encryption upgrades.",
        category=AgentCategory.FIXER,
        author="payment-security",
        version="1.0.3",
        mcp_tool_name="marketplace/pci-auto-fix",
        status=AgentStatus.PUBLISHED,
        downloads=1560,
        rating=4.3,
        rating_count=34,
        tags=["pci-dss", "payments", "auto-fix"],
        frameworks=["PCI-DSS"],
        published_at=datetime(2026, 2, 1, tzinfo=UTC),
    ),
    MarketplaceAgent(
        name="SOC 2 Evidence Reporter",
        slug="soc2-evidence-reporter",
        description="Generates audit-ready SOC 2 Type II evidence packages with automated control mapping and screenshots.",
        category=AgentCategory.REPORTER,
        author="audit-automation",
        version="1.1.0",
        mcp_tool_name="marketplace/soc2-evidence",
        status=AgentStatus.PUBLISHED,
        downloads=980,
        rating=4.8,
        rating_count=22,
        tags=["soc2", "audit", "evidence"],
        frameworks=["SOC 2"],
        published_at=datetime(2026, 2, 5, tzinfo=UTC),
    ),
    MarketplaceAgent(
        name="EU AI Act Risk Classifier",
        slug="eu-ai-act-classifier",
        description="Classifies AI systems by EU AI Act risk levels and generates required documentation and conformity assessments.",
        category=AgentCategory.ANALYZER,
        author="ai-compliance-lab",
        version="0.9.0",
        mcp_tool_name="marketplace/eu-ai-classify",
        status=AgentStatus.PUBLISHED,
        downloads=720,
        rating=4.1,
        rating_count=15,
        tags=["eu-ai-act", "risk", "classification"],
        frameworks=["EU AI Act"],
        published_at=datetime(2026, 2, 10, tzinfo=UTC),
    ),
]


class AgentsMarketplaceService:
    """Marketplace for third-party compliance agents."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._agents: dict[str, MarketplaceAgent] = {a.slug: a for a in _SEED_AGENTS}
        self._installations: list[AgentInstallation] = []
        self._reviews: list[AgentReview] = []

    async def publish_agent(
        self,
        name: str,
        slug: str,
        description: str,
        category: str,
        author: str,
        mcp_tool_name: str = "",
        frameworks: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> MarketplaceAgent:
        now = datetime.now(UTC)
        agent = MarketplaceAgent(
            name=name,
            slug=slug,
            description=description,
            category=AgentCategory(category),
            author=author,
            mcp_tool_name=mcp_tool_name or f"marketplace/{slug}",
            status=AgentStatus.IN_REVIEW,
            frameworks=frameworks or [],
            tags=tags or [],
            created_at=now,
        )
        self._agents[slug] = agent
        logger.info("Agent submitted for review", slug=slug, author=author)
        return agent

    async def approve_agent(self, slug: str) -> MarketplaceAgent | None:
        agent = self._agents.get(slug)
        if not agent:
            return None
        agent.status = AgentStatus.PUBLISHED
        agent.published_at = datetime.now(UTC)
        logger.info("Agent approved", slug=slug)
        return agent

    async def reject_agent(self, slug: str, reason: str = "") -> MarketplaceAgent | None:
        agent = self._agents.get(slug)
        if not agent:
            return None
        agent.status = AgentStatus.REJECTED
        return agent

    def search_agents(
        self,
        query: str = "",
        category: AgentCategory | None = None,
        framework: str | None = None,
        limit: int = 20,
    ) -> list[MarketplaceAgent]:
        results = [a for a in self._agents.values() if a.status == AgentStatus.PUBLISHED]
        if query:
            q = query.lower()
            results = [a for a in results if q in a.name.lower() or q in a.description.lower() or q in " ".join(a.tags)]
        if category:
            results = [a for a in results if a.category == category]
        if framework:
            results = [a for a in results if framework in a.frameworks]
        return sorted(results, key=lambda a: a.downloads, reverse=True)[:limit]

    def get_agent(self, slug: str) -> MarketplaceAgent | None:
        return self._agents.get(slug)

    async def install_agent(
        self,
        slug: str,
        organization_id: str,
        config: dict | None = None,
    ) -> AgentInstallation | None:
        agent = self._agents.get(slug)
        if not agent or agent.status != AgentStatus.PUBLISHED:
            return None
        installation = AgentInstallation(
            agent_id=agent.id,
            organization_id=organization_id,
            config=config or {},
            installed_at=datetime.now(UTC),
        )
        agent.downloads += 1
        self._installations.append(installation)
        logger.info("Agent installed", slug=slug, org=organization_id)
        return installation

    async def uninstall_agent(self, installation_id: UUID) -> bool:
        for inst in self._installations:
            if inst.id == installation_id:
                inst.status = InstallStatus.UNINSTALLED
                return True
        return False

    def list_installations(self, organization_id: str | None = None) -> list[AgentInstallation]:
        results = self._installations
        if organization_id:
            results = [i for i in results if i.organization_id == organization_id]
        return [i for i in results if i.status == InstallStatus.INSTALLED]

    async def rate_agent(self, slug: str, reviewer: str, rating: int, comment: str = "") -> AgentReview | None:
        agent = self._agents.get(slug)
        if not agent:
            return None
        review = AgentReview(
            agent_id=agent.id,
            reviewer=reviewer,
            rating=max(1, min(5, rating)),
            comment=comment,
            created_at=datetime.now(UTC),
        )
        self._reviews.append(review)
        agent_reviews = [r for r in self._reviews if r.agent_id == agent.id]
        agent.rating = round(sum(r.rating for r in agent_reviews) / len(agent_reviews), 1)
        agent.rating_count = len(agent_reviews)
        return review

    def get_reviews(self, slug: str) -> list[AgentReview]:
        agent = self._agents.get(slug)
        if not agent:
            return []
        return [r for r in self._reviews if r.agent_id == agent.id]

    def get_stats(self) -> MarketplaceStats:
        published = [a for a in self._agents.values() if a.status == AgentStatus.PUBLISHED]
        by_cat: dict[str, int] = {}
        for a in published:
            by_cat[a.category.value] = by_cat.get(a.category.value, 0) + 1
        top = sorted(published, key=lambda a: a.downloads, reverse=True)[:5]
        return MarketplaceStats(
            total_agents=len(self._agents),
            published_agents=len(published),
            total_installations=sum(1 for i in self._installations if i.status == InstallStatus.INSTALLED),
            total_executions=sum(i.execution_count for i in self._installations),
            by_category=by_cat,
            top_agents=[{"name": a.name, "downloads": a.downloads, "rating": a.rating} for a in top],
        )
