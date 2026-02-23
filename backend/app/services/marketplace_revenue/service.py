"""Marketplace Revenue Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.marketplace_revenue.models import (
    AgentListing,
    Payout,
    PayoutStatus,
    RevenueModel,
    RevenueReport,
    RevenueStats,
)


logger = structlog.get_logger()


def _build_seed_listings() -> dict[UUID, AgentListing]:
    """Build seed marketplace listings with revenue data."""
    listings_data = [
        {
            "agent_slug": "gdpr-scanner-pro",
            "author": "compliance-labs",
            "revenue_model": RevenueModel.SUBSCRIPTION,
            "price_usd": 49.99,
            "listing_fee_usd": 0.0,
            "monthly_revenue": 4999.00,
            "total_revenue": 29994.00,
            "subscribers": 100,
            "featured": True,
        },
        {
            "agent_slug": "hipaa-audit-agent",
            "author": "healthtech-tools",
            "revenue_model": RevenueModel.USAGE_BASED,
            "price_usd": 0.05,
            "listing_fee_usd": 99.00,
            "monthly_revenue": 2350.00,
            "total_revenue": 14100.00,
            "subscribers": 47,
            "featured": True,
        },
        {
            "agent_slug": "pci-checker",
            "author": "securedev",
            "revenue_model": RevenueModel.PAID_LISTING,
            "price_usd": 199.00,
            "listing_fee_usd": 49.00,
            "monthly_revenue": 1592.00,
            "total_revenue": 9552.00,
            "subscribers": 8,
            "featured": False,
        },
        {
            "agent_slug": "privacy-policy-gen",
            "author": "legal-ai",
            "revenue_model": RevenueModel.SUBSCRIPTION,
            "price_usd": 29.99,
            "listing_fee_usd": 0.0,
            "monthly_revenue": 899.70,
            "total_revenue": 5398.20,
            "subscribers": 30,
            "featured": False,
        },
        {
            "agent_slug": "open-source-license-checker",
            "author": "community-dev",
            "revenue_model": RevenueModel.FREE,
            "price_usd": 0.0,
            "listing_fee_usd": 0.0,
            "monthly_revenue": 0.0,
            "total_revenue": 0.0,
            "subscribers": 250,
            "featured": True,
        },
    ]

    result: dict[UUID, AgentListing] = {}
    for data in listings_data:
        listing = AgentListing(
            id=uuid4(),
            agent_slug=data["agent_slug"],
            author=data["author"],
            revenue_model=data["revenue_model"],
            listing_fee_usd=data["listing_fee_usd"],
            price_usd=data["price_usd"],
            monthly_revenue=data["monthly_revenue"],
            total_revenue=data["total_revenue"],
            subscribers=data["subscribers"],
            featured=data["featured"],
            listed_at=datetime.now(UTC),
        )
        result[listing.id] = listing
    return result


class MarketplaceRevenueService:
    """Service for managing marketplace revenue and agent listings."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._listings: dict[UUID, AgentListing] = _build_seed_listings()
        self._payouts: dict[UUID, Payout] = {}

    async def create_listing(
        self,
        agent_slug: str,
        author: str,
        revenue_model: RevenueModel,
        price_usd: float = 0.0,
        listing_fee: float = 0.0,
    ) -> AgentListing:
        """Create a new marketplace agent listing."""
        log = logger.bind(agent_slug=agent_slug, author=author)
        log.info("listing.create.start")

        listing = AgentListing(
            id=uuid4(),
            agent_slug=agent_slug,
            author=author,
            revenue_model=revenue_model,
            listing_fee_usd=listing_fee,
            price_usd=price_usd,
            listed_at=datetime.now(UTC),
        )

        self._listings[listing.id] = listing
        log.info("listing.created", listing_id=str(listing.id))
        return listing

    async def record_transaction(
        self, listing_id: UUID, amount: float
    ) -> AgentListing:
        """Record a revenue transaction for a listing."""
        log = logger.bind(listing_id=str(listing_id), amount=amount)

        listing = self._listings.get(listing_id)
        if not listing:
            log.warning("listing.not_found")
            raise ValueError(f"Listing {listing_id} not found")

        listing.monthly_revenue += amount
        listing.total_revenue += amount

        log.info(
            "transaction.recorded",
            total_revenue=listing.total_revenue,
        )
        return listing

    async def generate_payout(self, author: str, period: str) -> Payout:
        """Generate a payout for an author for the given period."""
        log = logger.bind(author=author, period=period)
        log.info("payout.generate.start")

        author_listings = [
            l for l in self._listings.values() if l.author == author
        ]
        total_amount = sum(
            l.monthly_revenue * (l.revenue_share_pct / 100.0)
            for l in author_listings
        )

        payout = Payout(
            id=uuid4(),
            author=author,
            amount_usd=round(total_amount, 2),
            period=period,
            status=PayoutStatus.PENDING,
            agents=[l.agent_slug for l in author_listings],
            created_at=datetime.now(UTC),
        )

        self._payouts[payout.id] = payout
        log.info(
            "payout.generated",
            payout_id=str(payout.id),
            amount=payout.amount_usd,
        )
        return payout

    async def generate_revenue_report(self, period: str) -> RevenueReport:
        """Generate a revenue report for the given period."""
        log = logger.bind(period=period)
        log.info("report.generate.start")

        listings = list(self._listings.values())
        total_revenue = sum(l.monthly_revenue for l in listings)
        platform_share = sum(
            l.monthly_revenue * ((100.0 - l.revenue_share_pct) / 100.0)
            for l in listings
        )
        author_total = total_revenue - platform_share

        by_model: dict[str, float] = {}
        for listing in listings:
            model_key = listing.revenue_model.value
            by_model[model_key] = by_model.get(model_key, 0.0) + listing.monthly_revenue

        sorted_listings = sorted(
            listings, key=lambda l: l.monthly_revenue, reverse=True
        )
        top_agents = [
            {
                "agent_slug": l.agent_slug,
                "author": l.author,
                "monthly_revenue": l.monthly_revenue,
                "revenue_model": l.revenue_model.value,
            }
            for l in sorted_listings[:5]
        ]

        report = RevenueReport(
            period=period,
            total_revenue=round(total_revenue, 2),
            platform_share=round(platform_share, 2),
            author_payouts=round(author_total, 2),
            by_model=by_model,
            top_agents=top_agents,
            generated_at=datetime.now(UTC),
        )

        log.info("report.generated", total_revenue=report.total_revenue)
        return report

    async def get_listing(self, agent_slug: str) -> AgentListing:
        """Get a listing by agent slug."""
        for listing in self._listings.values():
            if listing.agent_slug == agent_slug:
                return listing
        raise ValueError(f"Listing '{agent_slug}' not found")

    async def list_listings(
        self, featured_only: bool = False
    ) -> list[AgentListing]:
        """List all marketplace listings."""
        listings = list(self._listings.values())
        if featured_only:
            listings = [l for l in listings if l.featured]
        return listings

    async def get_stats(self) -> RevenueStats:
        """Get aggregate marketplace revenue statistics."""
        listings = list(self._listings.values())
        total = len(listings)
        paid = [l for l in listings if l.revenue_model != RevenueModel.FREE]

        total_revenue = sum(l.total_revenue for l in listings)
        platform_revenue = sum(
            l.total_revenue * ((100.0 - l.revenue_share_pct) / 100.0)
            for l in listings
        )
        author_payouts = total_revenue - platform_revenue

        by_model: dict[str, int] = {}
        for listing in listings:
            model_key = listing.revenue_model.value
            by_model[model_key] = by_model.get(model_key, 0) + 1

        return RevenueStats(
            total_listings=total,
            paid_listings=len(paid),
            total_revenue=round(total_revenue, 2),
            platform_revenue=round(platform_revenue, 2),
            author_payouts=round(author_payouts, 2),
            avg_revenue_per_agent=(
                round(total_revenue / total, 2) if total else 0.0
            ),
            by_revenue_model=by_model,
        )
