"""Digital Compliance Marketplace Service."""
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.digital_marketplace.models import (
    AssetPurchase,
    AssetStatus,
    AssetType,
    DigitalMarketplaceStats,
    MarketplaceAsset,
    MarketplaceRevenueReport,
    PricingModel,
)


logger = structlog.get_logger()


class DigitalMarketplaceService:
    """Marketplace for buying, selling, and sharing compliance assets."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._assets: list[MarketplaceAsset] = []
        self._purchases: list[AssetPurchase] = []
        self._seed_assets()

    def _seed_assets(self) -> None:
        seed_data = [
            {
                "title": "SOC 2 Type II Policy Bundle",
                "description": "Complete set of SOC 2 policies covering all trust service criteria",
                "asset_type": AssetType.POLICY,
                "author": "CompliancePro",
                "pricing": PricingModel.ONE_TIME,
                "price_usd": 299.99,
                "frameworks": ["SOC2"],
                "tags": ["soc2", "policies", "trust-criteria"],
                "downloads": 1240,
                "rating": 4.8,
                "rating_count": 156,
            },
            {
                "title": "GDPR Evidence Collection Templates",
                "description": "Ready-to-use templates for GDPR evidence gathering and documentation",
                "asset_type": AssetType.EVIDENCE_TEMPLATE,
                "author": "EUCompliance",
                "pricing": PricingModel.FREE,
                "price_usd": 0.0,
                "frameworks": ["GDPR"],
                "tags": ["gdpr", "evidence", "templates"],
                "downloads": 3420,
                "rating": 4.5,
                "rating_count": 289,
            },
            {
                "title": "Zero Trust Architecture Pattern",
                "description": "Reference architecture for zero-trust compliance in cloud environments",
                "asset_type": AssetType.ARCHITECTURE_PATTERN,
                "author": "CloudSecArch",
                "pricing": PricingModel.SUBSCRIPTION,
                "price_usd": 49.99,
                "frameworks": ["SOC2", "ISO27001", "NIST"],
                "tags": ["zero-trust", "architecture", "cloud"],
                "downloads": 876,
                "rating": 4.9,
                "rating_count": 92,
            },
            {
                "title": "HIPAA Security Awareness Training",
                "description": "Interactive training module for HIPAA security awareness",
                "asset_type": AssetType.TRAINING_MODULE,
                "author": "HealthSecEd",
                "pricing": PricingModel.PAY_PER_USE,
                "price_usd": 9.99,
                "frameworks": ["HIPAA"],
                "tags": ["hipaa", "training", "security-awareness"],
                "downloads": 2150,
                "rating": 4.6,
                "rating_count": 340,
            },
            {
                "title": "PCI DSS Compliance Playbook",
                "description": "Step-by-step playbook for achieving and maintaining PCI DSS compliance",
                "asset_type": AssetType.COMPLIANCE_PLAYBOOK,
                "author": "PaymentSecOps",
                "pricing": PricingModel.ONE_TIME,
                "price_usd": 199.99,
                "frameworks": ["PCI-DSS"],
                "tags": ["pci", "playbook", "payments"],
                "downloads": 567,
                "rating": 4.7,
                "rating_count": 78,
            },
            {
                "title": "ISO 27001 Implementation Playbook",
                "description": "Comprehensive playbook for ISO 27001 certification journey",
                "asset_type": AssetType.COMPLIANCE_PLAYBOOK,
                "author": "ISOExperts",
                "pricing": PricingModel.SUBSCRIPTION,
                "price_usd": 79.99,
                "frameworks": ["ISO27001"],
                "tags": ["iso27001", "certification", "isms"],
                "downloads": 1890,
                "rating": 4.8,
                "rating_count": 215,
            },
        ]
        now = datetime.now(UTC)
        for data in seed_data:
            asset = MarketplaceAsset(
                title=data["title"],
                description=data["description"],
                asset_type=data["asset_type"],
                author=data["author"],
                pricing=data["pricing"],
                price_usd=data["price_usd"],
                status=AssetStatus.LISTED,
                downloads=data["downloads"],
                rating=data["rating"],
                rating_count=data["rating_count"],
                frameworks=data["frameworks"],
                tags=data["tags"],
                listed_at=now,
            )
            self._assets.append(asset)

    async def list_asset(
        self,
        title: str,
        asset_type: str,
        author: str,
        pricing: str,
        price_usd: float,
        frameworks: list[str],
        content: dict,
    ) -> MarketplaceAsset:
        asset = MarketplaceAsset(
            title=title,
            description=f"Custom asset: {title}",
            asset_type=AssetType(asset_type),
            author=author,
            pricing=PricingModel(pricing),
            price_usd=price_usd,
            status=AssetStatus.LISTED,
            frameworks=frameworks,
            content=content,
            listed_at=datetime.now(UTC),
        )
        self._assets.append(asset)
        logger.info("Asset listed", title=title, type=asset_type)
        return asset

    def search_assets(
        self,
        query: str,
        asset_type: str | None = None,
        framework: str | None = None,
    ) -> list[MarketplaceAsset]:
        results = [
            a for a in self._assets
            if a.status == AssetStatus.LISTED
        ]
        if query:
            q = query.lower()
            results = [
                a for a in results
                if q in a.title.lower()
                or q in a.description.lower()
                or any(q in t for t in a.tags)
            ]
        if asset_type:
            at = AssetType(asset_type)
            results = [a for a in results if a.asset_type == at]
        if framework:
            results = [a for a in results if framework in a.frameworks]
        return results

    async def purchase_asset(
        self,
        asset_id: UUID,
        buyer_org: str,
    ) -> AssetPurchase | None:
        asset = self._find_asset(asset_id)
        if not asset:
            return None

        purchase = AssetPurchase(
            asset_id=asset_id,
            buyer_org=buyer_org,
            price_paid=asset.price_usd,
            purchased_at=datetime.now(UTC),
        )
        asset.downloads += 1
        self._purchases.append(purchase)

        logger.info(
            "Asset purchased",
            asset_id=str(asset_id),
            buyer=buyer_org,
            price=asset.price_usd,
        )
        return purchase

    async def rate_asset(
        self,
        asset_id: UUID,
        rating: float,
        reviewer: str,
    ) -> MarketplaceAsset | None:
        asset = self._find_asset(asset_id)
        if not asset:
            return None

        total_rating = asset.rating * asset.rating_count + rating
        asset.rating_count += 1
        asset.rating = round(total_rating / asset.rating_count, 2)

        logger.info(
            "Asset rated",
            asset_id=str(asset_id),
            rating=rating,
            reviewer=reviewer,
        )
        return asset

    def generate_report(self, period: str) -> MarketplaceRevenueReport:
        by_type: dict[str, float] = {}
        seller_revenue: dict[str, float] = {}

        for purchase in self._purchases:
            asset = self._find_asset(purchase.asset_id)
            if asset:
                type_key = asset.asset_type.value
                by_type[type_key] = by_type.get(type_key, 0) + purchase.price_paid
                seller_revenue[asset.author] = (
                    seller_revenue.get(asset.author, 0) + purchase.price_paid
                )

        top_sellers = sorted(
            [{"author": k, "revenue": v} for k, v in seller_revenue.items()],
            key=lambda x: x["revenue"],
            reverse=True,
        )[:10]

        total_revenue = sum(p.price_paid for p in self._purchases)
        return MarketplaceRevenueReport(
            period=period,
            total_sales=len(self._purchases),
            total_revenue=round(total_revenue, 2),
            by_asset_type=by_type,
            top_sellers=top_sellers,
            generated_at=datetime.now(UTC),
        )

    def list_assets(
        self,
        asset_type: str | None = None,
    ) -> list[MarketplaceAsset]:
        results = list(self._assets)
        if asset_type:
            at = AssetType(asset_type)
            results = [a for a in results if a.asset_type == at]
        return results

    def get_stats(self) -> DigitalMarketplaceStats:
        by_type: dict[str, int] = {}
        total_rating = 0.0
        rated_count = 0
        listed = 0

        for a in self._assets:
            by_type[a.asset_type.value] = by_type.get(a.asset_type.value, 0) + 1
            if a.status == AssetStatus.LISTED:
                listed += 1
            if a.rating_count > 0:
                total_rating += a.rating
                rated_count += 1

        total_revenue = sum(p.price_paid for p in self._purchases)
        return DigitalMarketplaceStats(
            total_assets=len(self._assets),
            listed_assets=listed,
            total_purchases=len(self._purchases),
            total_revenue=round(total_revenue, 2),
            by_asset_type=by_type,
            avg_rating=round(total_rating / rated_count, 2) if rated_count else 0.0,
        )

    def _find_asset(self, asset_id: UUID) -> MarketplaceAsset | None:
        for a in self._assets:
            if a.id == asset_id:
                return a
        return None
