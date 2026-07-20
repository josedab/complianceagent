"""Compliance Agents Marketplace Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_state import AgentMarketplaceRecord
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

_SEED_AGENT_BY_SLUG = {agent.slug: agent for agent in _SEED_AGENTS}


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _record_to_installation(record: AgentMarketplaceRecord) -> AgentInstallation:
    meta = record.agent_metadata or {}
    agent_id = UUID(meta["agent_id"]) if meta.get("agent_id") else UUID(int=0)
    return AgentInstallation(
        id=record.id,
        agent_id=agent_id,
        organization_id=str(record.organization_id),
        status=InstallStatus(record.status),
        config=meta.get("config", {}),
        installed_at=record.created_at,
        last_executed_at=_parse_datetime(meta.get("last_executed_at")),
        execution_count=meta.get("execution_count", 0),
    )


def _record_to_review(payload: dict) -> AgentReview:
    return AgentReview(
        id=UUID(payload["id"]),
        agent_id=UUID(payload["agent_id"]),
        reviewer=payload.get("reviewer", ""),
        rating=payload.get("rating", 5),
        comment=payload.get("comment", ""),
        created_at=_parse_datetime(payload.get("created_at")),
    )


class AgentsMarketplaceService:
    """Marketplace for third-party compliance agents."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id
        self._agents: dict[str, MarketplaceAgent] = dict(_SEED_AGENT_BY_SLUG)

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
        results = [
            agent for agent in self._agents.values() if agent.status == AgentStatus.PUBLISHED
        ]
        if query:
            q = query.lower()
            results = [
                agent
                for agent in results
                if q in agent.name.lower()
                or q in agent.description.lower()
                or q in " ".join(agent.tags)
            ]
        if category:
            results = [agent for agent in results if agent.category == category]
        if framework:
            results = [agent for agent in results if framework in agent.frameworks]
        return sorted(results, key=lambda agent: agent.downloads, reverse=True)[:limit]

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
        install_org_id = UUID(organization_id)
        installation = AgentInstallation(
            agent_id=agent.id,
            organization_id=organization_id,
            config=config or {},
            installed_at=datetime.now(UTC),
        )
        record = AgentMarketplaceRecord(
            id=installation.id,
            organization_id=install_org_id,
            name=agent.name,
            description=agent.description,
            agent_type=agent.category.value,
            version=agent.version,
            status=installation.status.value,
            capabilities=list(agent.frameworks),
            rating=agent.rating,
            install_count=1,
            agent_metadata={
                "slug": agent.slug,
                "agent_id": str(agent.id),
                "author": agent.author,
                "mcp_tool_name": agent.mcp_tool_name,
                "tags": agent.tags,
                "frameworks": agent.frameworks,
                "config": installation.config,
                "execution_count": 0,
                "reviews": [],
            },
        )
        self.db.add(record)
        await self.db.flush()
        agent.downloads += 1
        logger.info("Agent installed", slug=slug, org=organization_id)
        return _record_to_installation(record)

    async def uninstall_agent(self, installation_id: UUID) -> bool:
        stmt = select(AgentMarketplaceRecord).where(
            AgentMarketplaceRecord.id == installation_id,
            AgentMarketplaceRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return False
        record.status = InstallStatus.UNINSTALLED.value
        await self.db.flush()
        return True

    async def list_installations(
        self, organization_id: str | None = None
    ) -> list[AgentInstallation]:
        target_org_id = UUID(organization_id) if organization_id else self.organization_id
        stmt = select(AgentMarketplaceRecord).where(
            AgentMarketplaceRecord.organization_id == target_org_id
        )
        result = await self.db.execute(stmt)
        return [
            _record_to_installation(record)
            for record in result.scalars().all()
            if record.status == InstallStatus.INSTALLED.value
        ]

    async def rate_agent(
        self, slug: str, reviewer: str, rating: int, comment: str = ""
    ) -> AgentReview | None:
        stmt = select(AgentMarketplaceRecord).where(
            AgentMarketplaceRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        matching = [
            record
            for record in result.scalars().all()
            if (record.agent_metadata or {}).get("slug") == slug
        ]
        if not matching:
            return None

        target = max(matching, key=lambda record: record.created_at)
        meta = dict(target.agent_metadata or {})
        review = AgentReview(
            agent_id=UUID(meta.get("agent_id", str(target.id))),
            reviewer=reviewer,
            rating=max(1, min(5, rating)),
            comment=comment,
            created_at=datetime.now(UTC),
        )
        reviews = list(meta.get("reviews", []))
        reviews.append(
            {
                "id": str(review.id),
                "agent_id": str(review.agent_id),
                "reviewer": review.reviewer,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
        )
        meta["reviews"] = reviews
        target.agent_metadata = meta
        target.rating = round(sum(item["rating"] for item in reviews) / len(reviews), 1)
        await self.db.flush()
        return review

    async def get_reviews(self, slug: str) -> list[AgentReview]:
        stmt = select(AgentMarketplaceRecord).where(
            AgentMarketplaceRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        reviews: list[AgentReview] = []
        for record in result.scalars().all():
            meta = record.agent_metadata or {}
            if meta.get("slug") != slug:
                continue
            reviews.extend(_record_to_review(item) for item in meta.get("reviews", []))
        return sorted(
            reviews,
            key=lambda review: review.created_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

    async def get_stats(self) -> MarketplaceStats:
        installations = await self.list_installations()
        published = [
            agent for agent in self._agents.values() if agent.status == AgentStatus.PUBLISHED
        ]
        by_cat: dict[str, int] = {}
        for agent in published:
            by_cat[agent.category.value] = by_cat.get(agent.category.value, 0) + 1
        top = sorted(published, key=lambda agent: agent.downloads, reverse=True)[:5]
        return MarketplaceStats(
            total_agents=len(self._agents),
            published_agents=len(published),
            total_installations=len(installations),
            total_executions=sum(installation.execution_count for installation in installations),
            by_category=by_cat,
            top_agents=[
                {"name": agent.name, "downloads": agent.downloads, "rating": agent.rating}
                for agent in top
            ],
        )
