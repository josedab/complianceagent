"""Policy Marketplace Service - Community marketplace for compliance policy packs."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.services.policy_marketplace.models import (
    CreatorProfile,
    MarketplaceStats,
    PolicyBundle,
    PolicyFile,
    PolicyLanguage,
    PolicyPack,
    PolicyPackStatus,
    PolicyPackVersion,
    PolicyReview,
    PricingModel,
    Purchase,
)


logger = structlog.get_logger()

# --- Sample creator IDs ---
_CREATOR_1 = UUID("a1000000-0000-0000-0000-000000000001")
_CREATOR_2 = UUID("a2000000-0000-0000-0000-000000000002")
_CREATOR_3 = UUID("a3000000-0000-0000-0000-000000000003")

# --- Sample policy packs ---
SAMPLE_PACKS: list[PolicyPack] = [
    PolicyPack(
        id=UUID("b1000000-0000-0000-0000-000000000001"),
        creator_id=_CREATOR_1,
        title="GDPR Data Protection Essentials",
        description="Comprehensive OPA/Rego policies for GDPR Articles 5-9 covering data minimization, purpose limitation, and consent management.",
        version="2.1.0",
        regulations=["GDPR"],
        languages=[PolicyLanguage.REGO, PolicyLanguage.YAML],
        pricing_model=PricingModel.ONE_TIME,
        price_usd=49.99,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=3420,
        rating=4.8,
        review_count=87,
        tags=["gdpr", "data-protection", "privacy", "eu"],
    ),
    PolicyPack(
        id=UUID("b2000000-0000-0000-0000-000000000002"),
        creator_id=_CREATOR_2,
        title="HIPAA Security Rule Pack",
        description="Complete HIPAA Security Rule policy set covering administrative, physical, and technical safeguards for ePHI protection.",
        version="3.0.1",
        regulations=["HIPAA"],
        languages=[PolicyLanguage.REGO, PolicyLanguage.PYTHON],
        pricing_model=PricingModel.SUBSCRIPTION,
        price_usd=29.99,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=2180,
        rating=4.7,
        review_count=54,
        tags=["hipaa", "healthcare", "phi", "security"],
    ),
    PolicyPack(
        id=UUID("b3000000-0000-0000-0000-000000000003"),
        creator_id=_CREATOR_1,
        title="PCI-DSS v4.0 Complete Controls",
        description="All 12 PCI-DSS v4.0 requirement domains as executable policies with automated evidence collection hooks.",
        version="4.0.0",
        regulations=["PCI-DSS"],
        languages=[PolicyLanguage.REGO, PolicyLanguage.YAML, PolicyLanguage.JSON],
        pricing_model=PricingModel.ONE_TIME,
        price_usd=79.99,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=1560,
        rating=4.9,
        review_count=42,
        tags=["pci-dss", "payments", "cardholder-data", "security"],
    ),
    PolicyPack(
        id=UUID("b4000000-0000-0000-0000-000000000004"),
        creator_id=_CREATOR_3,
        title="SOC 2 Type II Trust Services",
        description="Policies mapping to all five SOC 2 Trust Services Criteria: security, availability, processing integrity, confidentiality, and privacy.",
        version="2.0.0",
        regulations=["SOC 2"],
        languages=[PolicyLanguage.REGO, PolicyLanguage.PYTHON],
        pricing_model=PricingModel.SUBSCRIPTION,
        price_usd=39.99,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=2890,
        rating=4.6,
        review_count=68,
        tags=["soc2", "trust-services", "audit", "saas"],
    ),
    PolicyPack(
        id=UUID("b5000000-0000-0000-0000-000000000005"),
        creator_id=_CREATOR_2,
        title="EU AI Act Risk Classification",
        description="Automated risk classification and conformity assessment policies for the EU AI Act covering prohibited, high-risk, and limited-risk AI systems.",
        version="1.2.0",
        regulations=["EU AI Act"],
        languages=[PolicyLanguage.PYTHON, PolicyLanguage.YAML],
        pricing_model=PricingModel.ONE_TIME,
        price_usd=59.99,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=980,
        rating=4.5,
        review_count=23,
        tags=["eu-ai-act", "artificial-intelligence", "risk-classification", "eu"],
    ),
    PolicyPack(
        id=UUID("b6000000-0000-0000-0000-000000000006"),
        creator_id=_CREATOR_3,
        title="ISO 27001 Annex A Controls",
        description="Policy-as-code implementation of all 93 ISO 27001:2022 Annex A controls with gap analysis automation.",
        version="1.0.0",
        regulations=["ISO 27001"],
        languages=[PolicyLanguage.REGO, PolicyLanguage.YAML],
        pricing_model=PricingModel.ONE_TIME,
        price_usd=69.99,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=1230,
        rating=4.7,
        review_count=31,
        tags=["iso-27001", "information-security", "isms", "annex-a"],
    ),
    PolicyPack(
        id=UUID("b7000000-0000-0000-0000-000000000007"),
        creator_id=_CREATOR_1,
        title="Kubernetes CIS Benchmark Policies",
        description="OPA/Rego policies implementing the CIS Kubernetes Benchmark v1.8 for cluster hardening and workload security.",
        version="1.8.0",
        regulations=["CIS Benchmarks"],
        languages=[PolicyLanguage.REGO],
        pricing_model=PricingModel.FREE,
        price_usd=0.0,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=5640,
        rating=4.9,
        review_count=134,
        tags=["kubernetes", "cis", "container-security", "opa"],
    ),
    PolicyPack(
        id=UUID("b8000000-0000-0000-0000-000000000008"),
        creator_id=_CREATOR_2,
        title="NIST CSF 2.0 Governance Policies",
        description="Full NIST Cybersecurity Framework 2.0 implementation covering Govern, Identify, Protect, Detect, Respond, and Recover functions.",
        version="2.0.0",
        regulations=["NIST CSF"],
        languages=[PolicyLanguage.REGO, PolicyLanguage.PYTHON, PolicyLanguage.YAML],
        pricing_model=PricingModel.USAGE_BASED,
        price_usd=0.10,
        revenue_share_pct=70.0,
        status=PolicyPackStatus.PUBLISHED,
        downloads=1870,
        rating=4.6,
        review_count=45,
        tags=["nist", "cybersecurity", "csf", "governance"],
    ),
]

SAMPLE_CREATORS: list[CreatorProfile] = [
    CreatorProfile(
        id=UUID("c1000000-0000-0000-0000-000000000001"),
        user_id=_CREATOR_1,
        display_name="PolicyForge Labs",
        bio="Enterprise compliance automation experts specializing in OPA/Rego policy development.",
        expertise=["GDPR", "PCI-DSS", "Kubernetes", "OPA"],
        published_packs=3,
        total_downloads=10620,
        total_earnings_usd=8450.00,
        verified=True,
    ),
    CreatorProfile(
        id=UUID("c2000000-0000-0000-0000-000000000002"),
        user_id=_CREATOR_2,
        display_name="HealthSec Compliance",
        bio="Healthcare and AI compliance specialists with 15+ years in regulated industries.",
        expertise=["HIPAA", "EU AI Act", "NIST", "Healthcare"],
        published_packs=3,
        total_downloads=5030,
        total_earnings_usd=6200.00,
        verified=True,
    ),
    CreatorProfile(
        id=UUID("c3000000-0000-0000-0000-000000000003"),
        user_id=_CREATOR_3,
        display_name="AuditReady",
        bio="Making audit preparation painless with automated compliance checks and evidence collection.",
        expertise=["SOC 2", "ISO 27001", "Audit Automation"],
        published_packs=2,
        total_downloads=4120,
        total_earnings_usd=5100.00,
        verified=True,
    ),
]

SAMPLE_BUNDLES: list[PolicyBundle] = [
    PolicyBundle(
        id=UUID("d1000000-0000-0000-0000-000000000001"),
        name="Enterprise Compliance Starter",
        description="Essential policy packs for enterprise compliance: GDPR, SOC 2, and ISO 27001.",
        packs=["b1000000-0000-0000-0000-000000000001", "b4000000-0000-0000-0000-000000000004", "b6000000-0000-0000-0000-000000000006"],
        bundle_price_usd=129.99,
        savings_pct=19.0,
    ),
    PolicyBundle(
        id=UUID("d2000000-0000-0000-0000-000000000002"),
        name="Healthcare & AI Pack",
        description="Complete policy coverage for healthcare organizations adopting AI: HIPAA and EU AI Act.",
        packs=["b2000000-0000-0000-0000-000000000002", "b5000000-0000-0000-0000-000000000005"],
        bundle_price_usd=74.99,
        savings_pct=17.0,
    ),
]


class PolicyMarketplaceService:
    """Service for managing the compliance policy pack marketplace."""

    def __init__(self, db: Any = None):
        self._db = db
        self._packs: dict[UUID, PolicyPack] = {p.id: p for p in SAMPLE_PACKS}
        self._creators: dict[UUID, CreatorProfile] = {c.user_id: c for c in SAMPLE_CREATORS}
        self._reviews: dict[UUID, list[PolicyReview]] = {}
        self._purchases: dict[UUID, list[Purchase]] = {}
        self._bundles: dict[UUID, PolicyBundle] = {b.id: b for b in SAMPLE_BUNDLES}
        self._versions: dict[UUID, PolicyPackVersion] = {}

    async def list_packs(
        self,
        category: str | None = None,
        regulation: str | None = None,
        language: str | None = None,
        pricing: str | None = None,
        sort: str = "popular",
        limit: int = 20,
        offset: int = 0,
    ) -> list[PolicyPack]:
        """List policy packs with optional filtering and sorting."""
        logger.info("listing_policy_packs", category=category, regulation=regulation, sort=sort)

        packs = [p for p in self._packs.values() if p.status == PolicyPackStatus.PUBLISHED]

        if regulation:
            packs = [p for p in packs if regulation.upper() in [r.upper() for r in p.regulations]]
        if language:
            try:
                lang = PolicyLanguage(language.lower())
                packs = [p for p in packs if lang in p.languages]
            except ValueError:
                pass
        if pricing:
            try:
                pm = PricingModel(pricing.lower())
                packs = [p for p in packs if p.pricing_model == pm]
            except ValueError:
                pass
        if category:
            packs = [p for p in packs if category.lower() in [t.lower() for t in p.tags]]

        sort_keys = {
            "popular": lambda p: p.downloads,
            "rating": lambda p: p.rating,
            "newest": lambda p: p.created_at.timestamp(),
            "price_asc": lambda p: p.price_usd,
            "price_desc": lambda p: -p.price_usd,
        }
        key_fn = sort_keys.get(sort, sort_keys["popular"])
        packs.sort(key=key_fn, reverse=sort not in ("price_asc",))

        return packs[offset : offset + limit]

    async def get_pack(self, pack_id: UUID) -> PolicyPack | None:
        """Get a single policy pack by ID."""
        logger.info("getting_policy_pack", pack_id=str(pack_id))
        return self._packs.get(pack_id)

    async def search_packs(self, query: str, filters: dict[str, Any] | None = None) -> list[PolicyPack]:
        """Search policy packs by text query."""
        logger.info("searching_policy_packs", query=query)
        q = query.lower()
        results = [
            p
            for p in self._packs.values()
            if p.status == PolicyPackStatus.PUBLISHED
            and (
                q in p.title.lower()
                or q in p.description.lower()
                or any(q in t.lower() for t in p.tags)
                or any(q in r.lower() for r in p.regulations)
            )
        ]
        if filters:
            if filters.get("regulation"):
                results = [p for p in results if filters["regulation"].upper() in [r.upper() for r in p.regulations]]
            if filters.get("pricing"):
                try:
                    pm = PricingModel(filters["pricing"].lower())
                    results = [p for p in results if p.pricing_model == pm]
                except ValueError:
                    pass
        results.sort(key=lambda p: p.downloads, reverse=True)
        return results

    async def create_pack(
        self,
        creator_id: UUID,
        title: str,
        description: str,
        regulations: list[str],
        languages: list[PolicyLanguage],
        pricing_model: PricingModel,
        price_usd: float,
        files: list[PolicyFile],
    ) -> PolicyPack:
        """Create a new policy pack in draft status."""
        logger.info("creating_policy_pack", creator_id=str(creator_id), title=title)

        pack = PolicyPack(
            creator_id=creator_id,
            title=title,
            description=description,
            regulations=regulations,
            languages=languages,
            pricing_model=pricing_model,
            price_usd=price_usd,
            status=PolicyPackStatus.DRAFT,
        )
        self._packs[pack.id] = pack

        version = PolicyPackVersion(
            pack_id=pack.id,
            version=pack.version,
            changelog="Initial release",
            files=files,
        )
        self._versions[version.id] = version

        # Update creator stats
        creator = self._creators.get(creator_id)
        if creator:
            creator.published_packs += 1

        return pack

    async def publish_pack(self, pack_id: UUID) -> PolicyPack:
        """Publish a draft pack to the marketplace."""
        logger.info("publishing_policy_pack", pack_id=str(pack_id))
        pack = self._packs.get(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")
        if pack.status not in (PolicyPackStatus.DRAFT, PolicyPackStatus.UNDER_REVIEW):
            raise ValueError(f"Pack {pack_id} cannot be published from status {pack.status}")
        pack.status = PolicyPackStatus.PUBLISHED
        pack.updated_at = datetime.utcnow()
        return pack

    async def purchase_pack(self, user_id: UUID, pack_id: UUID) -> Purchase:
        """Purchase a policy pack and calculate revenue share."""
        logger.info("purchasing_policy_pack", user_id=str(user_id), pack_id=str(pack_id))
        pack = self._packs.get(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")
        if pack.status != PolicyPackStatus.PUBLISHED:
            raise ValueError(f"Pack {pack_id} is not available for purchase")

        creator_payout = round(pack.price_usd * (pack.revenue_share_pct / 100.0), 2)
        platform_fee = round(pack.price_usd - creator_payout, 2)

        purchase = Purchase(
            user_id=user_id,
            pack_id=pack_id,
            price_usd=pack.price_usd,
            creator_payout_usd=creator_payout,
            platform_fee_usd=platform_fee,
        )
        self._purchases.setdefault(pack_id, []).append(purchase)

        # Update creator earnings
        creator = self._creators.get(pack.creator_id)
        if creator:
            creator.total_earnings_usd += creator_payout

        return purchase

    async def download_pack(self, user_id: UUID, pack_id: UUID) -> PolicyPackVersion:
        """Download the latest version of a policy pack."""
        logger.info("downloading_policy_pack", user_id=str(user_id), pack_id=str(pack_id))
        pack = self._packs.get(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")

        pack.downloads += 1

        # Update creator download count
        creator = self._creators.get(pack.creator_id)
        if creator:
            creator.total_downloads += 1

        # Return existing version or generate a sample one
        for v in self._versions.values():
            if v.pack_id == pack_id:
                return v

        return PolicyPackVersion(
            pack_id=pack_id,
            version=pack.version,
            changelog="Latest release",
            files=[
                PolicyFile(
                    path="policies/main.rego",
                    language=PolicyLanguage.REGO,
                    content="package compliance\n\ndefault allow = false\n\nallow {\n    input.compliant == true\n}",
                    description="Main policy entrypoint",
                ),
            ],
        )

    async def submit_review(
        self, user_id: UUID, pack_id: UUID, rating: float, comment: str
    ) -> PolicyReview:
        """Submit a review for a purchased policy pack."""
        logger.info("submitting_review", user_id=str(user_id), pack_id=str(pack_id), rating=rating)
        pack = self._packs.get(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")

        # Check verified purchase
        pack_purchases = self._purchases.get(pack_id, [])
        verified = any(p.user_id == user_id for p in pack_purchases)

        review = PolicyReview(
            pack_id=pack_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            verified_purchase=verified,
        )
        self._reviews.setdefault(pack_id, []).append(review)

        # Update pack rating
        all_reviews = self._reviews[pack_id]
        pack.rating = round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
        pack.review_count = len(all_reviews)

        return review

    async def get_reviews(self, pack_id: UUID, limit: int = 20) -> list[PolicyReview]:
        """Get reviews for a policy pack."""
        logger.info("getting_reviews", pack_id=str(pack_id))
        reviews = self._reviews.get(pack_id, [])
        return sorted(reviews, key=lambda r: r.created_at, reverse=True)[:limit]

    async def get_creator_profile(self, creator_id: UUID) -> CreatorProfile | None:
        """Get a creator's public profile."""
        logger.info("getting_creator_profile", creator_id=str(creator_id))
        return self._creators.get(creator_id)

    async def register_creator(
        self, user_id: UUID, display_name: str, bio: str, expertise: list[str]
    ) -> CreatorProfile:
        """Register a new marketplace creator."""
        logger.info("registering_creator", user_id=str(user_id), display_name=display_name)
        if user_id in self._creators:
            raise ValueError(f"Creator already registered for user {user_id}")

        profile = CreatorProfile(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
            expertise=expertise,
        )
        self._creators[user_id] = profile
        return profile

    async def get_creator_earnings(self, creator_id: UUID) -> dict:
        """Get detailed earnings breakdown for a creator."""
        logger.info("getting_creator_earnings", creator_id=str(creator_id))
        creator = self._creators.get(creator_id)
        if not creator:
            raise ValueError(f"Creator {creator_id} not found")

        # Aggregate purchases for this creator's packs
        creator_packs = [p for p in self._packs.values() if p.creator_id == creator_id]
        total_revenue = 0.0
        total_payout = 0.0
        pack_earnings = []
        for pack in creator_packs:
            purchases = self._purchases.get(pack.id, [])
            revenue = sum(p.price_usd for p in purchases)
            payout = sum(p.creator_payout_usd for p in purchases)
            total_revenue += revenue
            total_payout += payout
            pack_earnings.append({
                "pack_id": str(pack.id),
                "title": pack.title,
                "total_revenue_usd": round(revenue, 2),
                "creator_payout_usd": round(payout, 2),
                "purchases": len(purchases),
                "downloads": pack.downloads,
            })

        return {
            "creator_id": str(creator_id),
            "display_name": creator.display_name,
            "total_earnings_usd": round(creator.total_earnings_usd, 2),
            "total_revenue_usd": round(total_revenue, 2),
            "total_payout_usd": round(total_payout, 2),
            "revenue_share_pct": 70.0,
            "packs": pack_earnings,
        }

    async def get_marketplace_stats(self) -> MarketplaceStats:
        """Get aggregate marketplace statistics."""
        logger.info("getting_marketplace_stats")
        published = [p for p in self._packs.values() if p.status == PolicyPackStatus.PUBLISHED]
        total_downloads = sum(p.downloads for p in published)

        all_purchases = [pur for plist in self._purchases.values() for pur in plist]
        total_gmv = sum(p.price_usd for p in all_purchases)

        # Build top categories from regulation tags
        cat_counts: dict[str, int] = {}
        for pack in published:
            for reg in pack.regulations:
                cat_counts[reg] = cat_counts.get(reg, 0) + pack.downloads
        top_categories = sorted(
            [{"name": k, "downloads": v} for k, v in cat_counts.items()],
            key=lambda x: x["downloads"],
            reverse=True,
        )

        return MarketplaceStats(
            total_packs=len(published),
            total_creators=len(self._creators),
            total_downloads=total_downloads,
            total_gmv_usd=round(total_gmv, 2),
            top_categories=top_categories,
        )

    async def list_bundles(self) -> list[PolicyBundle]:
        """List available policy pack bundles."""
        logger.info("listing_bundles")
        return list(self._bundles.values())

    async def validate_policy(self, content: str, language: str) -> dict:
        """Validate a policy file for syntax and best practices."""
        logger.info("validating_policy", language=language, content_length=len(content))
        try:
            lang = PolicyLanguage(language.lower())
        except ValueError:
            return {
                "valid": False,
                "language": language,
                "errors": [f"Unsupported language: {language}"],
                "warnings": [],
            }

        errors: list[str] = []
        warnings: list[str] = []

        if not content.strip():
            errors.append("Policy content is empty")
        elif len(content) > 100_000:
            errors.append("Policy content exceeds 100KB limit")

        if lang == PolicyLanguage.REGO:
            if "package" not in content:
                errors.append("Rego policy must declare a package")
            if "deny" not in content and "allow" not in content and "violation" not in content:
                warnings.append("Policy does not contain standard rule names (allow, deny, violation)")
        elif lang == PolicyLanguage.YAML:
            if not content.strip().startswith(("---", "apiVersion", "kind", "rules", "policies")):
                warnings.append("YAML policy should start with a recognized document header")
        elif lang == PolicyLanguage.PYTHON:
            if "def " not in content and "class " not in content:
                warnings.append("Python policy should define functions or classes")
        elif lang == PolicyLanguage.JSON:
            import json

            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {e}")

        return {
            "valid": len(errors) == 0,
            "language": lang.value,
            "errors": errors,
            "warnings": warnings,
        }
