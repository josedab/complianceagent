"""Pattern Marketplace Service - Multi-tenant marketplace for compliance patterns."""

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pattern_marketplace.models import (
    CompliancePattern,
    LicenseType,
    MarketplaceStats,
    PatternCategory,
    PatternInstallation,
    PatternPurchase,
    PatternRating,
    PatternType,
    PatternVersion,
    PublisherProfile,
    PublishStatus,
)


logger = structlog.get_logger()


class PatternMarketplaceService:
    """Service for the Compliance Pattern Marketplace.

    Enables organizations to publish, discover, and install compliance patterns.
    Supports monetization through paid patterns and revenue sharing.
    """

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id

        # In-memory storage (would be database in production)
        self._patterns: dict[UUID, CompliancePattern] = {}
        self._installations: dict[UUID, PatternInstallation] = {}
        self._ratings: dict[UUID, list[PatternRating]] = {}
        self._publishers: dict[UUID, PublisherProfile] = {}
        self._purchases: dict[UUID, PatternPurchase] = {}

        # Initialize with some sample patterns
        self._init_sample_patterns()

    def _init_sample_patterns(self) -> None:
        """Initialize sample marketplace patterns."""
        samples = [
            CompliancePattern(
                slug="gdpr-pii-detection",
                name="GDPR PII Detection Pattern",
                description="Detect potential PII exposure in code (emails, names, addresses)",
                category=PatternCategory.DATA_PRIVACY,
                pattern_type=PatternType.CODE_PATTERN,
                regulations=["GDPR", "CCPA"],
                languages=["python", "javascript", "typescript", "java"],
                tags=["pii", "privacy", "detection"],
                content={
                    "patterns": [
                        {
                            "name": "email_exposure",
                            "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                            "message": "Potential email address exposure detected",
                            "severity": "warning",
                        },
                        {
                            "name": "hardcoded_name",
                            "pattern": r"(first_?name|last_?name|full_?name)\s*=\s*['\"][^'\"]+['\"]",
                            "message": "Hardcoded personal name detected",
                            "severity": "warning",
                        },
                    ],
                },
                publisher_name="ComplianceAgent Official",
                publisher_verified=True,
                license_type=LicenseType.FREE,
                status=PublishStatus.PUBLISHED,
                published_at=datetime.now(UTC),
                downloads=1250,
                avg_rating=4.7,
                rating_count=89,
            ),
            CompliancePattern(
                slug="hipaa-phi-handler",
                name="HIPAA PHI Handler Template",
                description="Secure template for handling Protected Health Information",
                category=PatternCategory.HEALTHCARE,
                pattern_type=PatternType.TEMPLATE,
                regulations=["HIPAA"],
                languages=["python"],
                tags=["phi", "healthcare", "encryption", "logging"],
                content={
                    "code": '''
class PHIHandler:
    """Secure handler for Protected Health Information (PHI).

    Implements HIPAA-compliant data handling with encryption,
    audit logging, and access controls.
    """

    def __init__(self, encryption_key: bytes, audit_logger: AuditLogger):
        self._encryption = Fernet(encryption_key)
        self._audit = audit_logger

    def store_phi(self, patient_id: str, data: dict, user_id: str) -> str:
        """Store PHI with encryption and audit trail."""
        # Encrypt sensitive data
        encrypted = self._encryption.encrypt(json.dumps(data).encode())

        # Log access
        self._audit.log(
            event_type="phi_access",
            action="store",
            patient_id=patient_id,
            user_id=user_id,
            timestamp=datetime.utcnow(),
        )

        # Store with minimum necessary principle
        return self._storage.put(patient_id, encrypted)

    def retrieve_phi(self, patient_id: str, user_id: str, purpose: str) -> dict:
        """Retrieve PHI with access logging."""
        # Verify access authorization
        if not self._verify_access(user_id, patient_id, purpose):
            raise UnauthorizedAccessError("Access denied to PHI")

        # Log access
        self._audit.log(
            event_type="phi_access",
            action="retrieve",
            patient_id=patient_id,
            user_id=user_id,
            purpose=purpose,
            timestamp=datetime.utcnow(),
        )

        # Retrieve and decrypt
        encrypted = self._storage.get(patient_id)
        return json.loads(self._encryption.decrypt(encrypted))
''',
                    "placeholders": ["encryption_key", "audit_logger"],
                    "imports": [
                        "from cryptography.fernet import Fernet",
                        "import json",
                        "from datetime import datetime",
                    ],
                },
                publisher_name="HealthTech Compliance",
                publisher_verified=True,
                license_type=LicenseType.COMMERCIAL,
                price=49.99,
                price_type="one_time",
                status=PublishStatus.PUBLISHED,
                published_at=datetime.now(UTC),
                downloads=342,
                avg_rating=4.9,
                rating_count=28,
            ),
            CompliancePattern(
                slug="pci-dss-tokenization",
                name="PCI-DSS Card Tokenization",
                description="Secure payment card tokenization following PCI-DSS v4.0",
                category=PatternCategory.FINANCIAL,
                pattern_type=PatternType.TEMPLATE,
                regulations=["PCI-DSS"],
                languages=["python", "javascript"],
                tags=["payment", "tokenization", "cards", "security"],
                content={
                    "code": '''
class CardTokenizer:
    """PCI-DSS compliant card tokenization service."""

    def tokenize(self, card_number: str) -> str:
        """Tokenize a card number, returning a non-sensitive token."""
        # Validate card format
        if not self._validate_card(card_number):
            raise InvalidCardError("Invalid card number format")

        # Generate secure token
        token = self._generate_token()

        # Store mapping in secure vault (HSM)
        self._vault.store(token, self._encrypt(card_number))

        # Log tokenization (without card data)
        self._audit.log("card_tokenized", token=token[:8] + "...")

        return token

    def get_last_four(self, token: str) -> str:
        """Get last 4 digits for display purposes only."""
        card = self._vault.retrieve(token)
        return card[-4:]
''',
                    "placeholders": ["vault_connection", "encryption_key"],
                },
                publisher_name="FinSecure Patterns",
                publisher_verified=True,
                license_type=LicenseType.COMMERCIAL,
                price=99.99,
                price_type="one_time",
                status=PublishStatus.PUBLISHED,
                published_at=datetime.now(UTC),
                downloads=567,
                avg_rating=4.8,
                rating_count=45,
            ),
            CompliancePattern(
                slug="eu-ai-act-risk-assessment",
                name="EU AI Act Risk Assessment Checklist",
                description="Comprehensive checklist for AI system risk classification under EU AI Act",
                category=PatternCategory.AI_SAFETY,
                pattern_type=PatternType.CHECKLIST,
                regulations=["EU AI Act"],
                languages=[],
                tags=["ai", "risk", "assessment", "eu"],
                content={
                    "checklist": [
                        {
                            "category": "Prohibited Practices",
                            "items": [
                                "Does the system use subliminal manipulation?",
                                "Does it exploit vulnerabilities of specific groups?",
                                "Is it used for social scoring by public authorities?",
                                "Is it real-time biometric identification in public spaces?",
                            ],
                        },
                        {
                            "category": "High-Risk Classification",
                            "items": [
                                "Is it used in critical infrastructure?",
                                "Is it used in education/vocational training?",
                                "Is it used in employment/worker management?",
                                "Is it used for access to essential services?",
                                "Is it used in law enforcement?",
                                "Is it used in migration/border control?",
                            ],
                        },
                        {
                            "category": "Transparency Requirements",
                            "items": [
                                "Are users informed they are interacting with AI?",
                                "Is AI-generated content clearly labeled?",
                                "Are deep fakes clearly disclosed?",
                            ],
                        },
                    ],
                },
                publisher_name="ComplianceAgent Official",
                publisher_verified=True,
                license_type=LicenseType.FREE,
                status=PublishStatus.PUBLISHED,
                published_at=datetime.now(UTC),
                downloads=2100,
                avg_rating=4.6,
                rating_count=156,
            ),
            CompliancePattern(
                slug="sox-audit-logging",
                name="SOX Compliant Audit Logging",
                description="Financial audit logging pattern for SOX compliance",
                category=PatternCategory.AUDIT_TRAIL,
                pattern_type=PatternType.CODE_PATTERN,
                regulations=["SOX"],
                languages=["python", "java"],
                tags=["audit", "logging", "financial", "tamper-proof"],
                content={
                    "patterns": [
                        {
                            "name": "financial_transaction_logging",
                            "pattern": r"(balance|amount|transaction|payment|invoice)",
                            "message": "Financial data modification should be audit logged",
                            "severity": "error",
                        },
                    ],
                    "template": '''
@audit_logged(event_type="financial_modification")
def modify_financial_record(record_id: str, changes: dict, user: User) -> Record:
    """Modify financial record with full audit trail."""
    with transaction.atomic():
        # Get current state
        old_state = Record.objects.get(id=record_id).to_dict()

        # Apply changes
        record = Record.objects.get(id=record_id)
        for key, value in changes.items():
            setattr(record, key, value)
        record.save()

        # Create audit entry
        AuditLog.create(
            record_type="financial_record",
            record_id=record_id,
            old_state=old_state,
            new_state=record.to_dict(),
            changed_by=user.id,
            changed_at=datetime.utcnow(),
            hash=compute_hash(old_state, record.to_dict()),
        )

        return record
''',
                },
                publisher_name="AuditPro Patterns",
                publisher_verified=True,
                license_type=LicenseType.COMMERCIAL,
                price=79.99,
                price_type="one_time",
                status=PublishStatus.PUBLISHED,
                published_at=datetime.now(UTC),
                downloads=423,
                avg_rating=4.5,
                rating_count=32,
            ),
        ]

        for pattern in samples:
            self._patterns[pattern.id] = pattern

    # ========================================================================
    # Pattern Discovery
    # ========================================================================

    def search_patterns(
        self,
        query: str | None = None,
        category: PatternCategory | None = None,
        pattern_type: PatternType | None = None,
        regulations: list[str] | None = None,
        languages: list[str] | None = None,
        license_types: list[LicenseType] | None = None,
        free_only: bool = False,
        sort_by: str = "downloads",  # downloads, rating, newest
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CompliancePattern], int]:
        """Search and filter patterns in the marketplace."""
        patterns = [
            p for p in self._patterns.values()
            if p.status == PublishStatus.PUBLISHED
        ]

        # Apply filters
        if query:
            query_lower = query.lower()
            patterns = [
                p for p in patterns
                if query_lower in p.name.lower()
                or query_lower in p.description.lower()
                or any(query_lower in tag for tag in p.tags)
            ]

        if category:
            patterns = [p for p in patterns if p.category == category]

        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        if regulations:
            patterns = [
                p for p in patterns
                if any(r in p.regulations for r in regulations)
            ]

        if languages:
            patterns = [
                p for p in patterns
                if any(lang in p.languages for lang in languages)
            ]

        if license_types:
            patterns = [p for p in patterns if p.license_type in license_types]

        if free_only:
            patterns = [p for p in patterns if p.license_type == LicenseType.FREE]

        total = len(patterns)

        # Sort
        if sort_by == "downloads":
            patterns.sort(key=lambda p: p.downloads, reverse=True)
        elif sort_by == "rating":
            patterns.sort(key=lambda p: p.avg_rating, reverse=True)
        elif sort_by == "newest":
            patterns.sort(key=lambda p: p.published_at or p.created_at, reverse=True)

        # Paginate
        patterns = patterns[offset:offset + limit]

        return patterns, total

    def get_pattern(self, pattern_id: UUID) -> CompliancePattern | None:
        """Get a pattern by ID."""
        return self._patterns.get(pattern_id)

    def get_pattern_by_slug(self, slug: str) -> CompliancePattern | None:
        """Get a pattern by slug."""
        for pattern in self._patterns.values():
            if pattern.slug == slug:
                return pattern
        return None

    def get_featured_patterns(self, limit: int = 10) -> list[CompliancePattern]:
        """Get featured/trending patterns."""
        patterns = [
            p for p in self._patterns.values()
            if p.status == PublishStatus.PUBLISHED and p.publisher_verified
        ]
        # Sort by a combination of downloads and rating
        patterns.sort(key=lambda p: p.downloads * p.avg_rating, reverse=True)
        return patterns[:limit]

    def get_patterns_by_regulation(self, regulation: str) -> list[CompliancePattern]:
        """Get all patterns for a specific regulation."""
        return [
            p for p in self._patterns.values()
            if p.status == PublishStatus.PUBLISHED and regulation in p.regulations
        ]

    # ========================================================================
    # Pattern Publishing
    # ========================================================================

    def create_pattern(
        self,
        name: str,
        description: str,
        category: PatternCategory,
        pattern_type: PatternType,
        content: dict[str, Any],
        regulations: list[str] | None = None,
        languages: list[str] | None = None,
        tags: list[str] | None = None,
        license_type: LicenseType = LicenseType.FREE,
        price: float = 0.0,
    ) -> CompliancePattern:
        """Create a new pattern (draft)."""
        slug = self._generate_slug(name)

        pattern = CompliancePattern(
            slug=slug,
            name=name,
            description=description,
            category=category,
            pattern_type=pattern_type,
            content=content,
            regulations=regulations or [],
            languages=languages or [],
            tags=tags or [],
            license_type=license_type,
            price=price,
            publisher_org_id=self.organization_id,
            status=PublishStatus.DRAFT,
        )

        # Add initial version
        pattern.versions.append(PatternVersion(
            version="1.0.0",
            changelog="Initial version",
            content=content,
        ))

        self._patterns[pattern.id] = pattern

        logger.info(
            "Pattern created",
            pattern_id=str(pattern.id),
            name=name,
            organization_id=str(self.organization_id),
        )

        return pattern

    def update_pattern(
        self,
        pattern_id: UUID,
        updates: dict[str, Any],
    ) -> CompliancePattern | None:
        """Update a pattern."""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return None

        # Verify ownership
        if pattern.publisher_org_id != self.organization_id:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(pattern, key) and key not in ["id", "created_at", "publisher_org_id"]:
                if key == "category" and isinstance(value, str):
                    value = PatternCategory(value)
                elif key == "pattern_type" and isinstance(value, str):
                    value = PatternType(value)
                elif key == "license_type" and isinstance(value, str):
                    value = LicenseType(value)
                setattr(pattern, key, value)

        pattern.updated_at = datetime.now(UTC)
        return pattern

    def publish_pattern(self, pattern_id: UUID) -> CompliancePattern | None:
        """Submit a pattern for review/publication."""
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.publisher_org_id != self.organization_id:
            return None

        if pattern.status == PublishStatus.DRAFT:
            # In a real implementation, this would go to pending review
            # For now, auto-publish
            pattern.status = PublishStatus.PUBLISHED
            pattern.published_at = datetime.now(UTC)

            logger.info(
                "Pattern published",
                pattern_id=str(pattern_id),
                name=pattern.name,
            )

        return pattern

    def add_version(
        self,
        pattern_id: UUID,
        version: str,
        changelog: str,
        content: dict[str, Any],
    ) -> CompliancePattern | None:
        """Add a new version to a pattern."""
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.publisher_org_id != self.organization_id:
            return None

        pattern.versions.append(PatternVersion(
            version=version,
            changelog=changelog,
            content=content,
        ))
        pattern.current_version = version
        pattern.content = content
        pattern.updated_at = datetime.now(UTC)

        return pattern

    def fork_pattern(self, pattern_id: UUID, new_name: str) -> CompliancePattern | None:
        """Fork an existing pattern."""
        original = self._patterns.get(pattern_id)
        if not original or original.status != PublishStatus.PUBLISHED:
            return None

        forked = CompliancePattern(
            slug=self._generate_slug(new_name),
            name=new_name,
            description=f"Forked from {original.name}",
            long_description=original.long_description,
            category=original.category,
            pattern_type=original.pattern_type,
            regulations=original.regulations.copy(),
            languages=original.languages.copy(),
            tags=original.tags.copy(),
            content=original.content.copy(),
            publisher_org_id=self.organization_id,
            license_type=LicenseType.FREE,  # Forks start as free
            forked_from=original.id,
            status=PublishStatus.DRAFT,
        )

        self._patterns[forked.id] = forked
        original.fork_count += 1

        return forked

    def _generate_slug(self, name: str) -> str:
        """Generate a URL-safe slug from name."""
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')

        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while any(p.slug == slug for p in self._patterns.values()):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    # ========================================================================
    # Installation & Usage
    # ========================================================================

    def install_pattern(
        self,
        pattern_id: UUID,
        custom_config: dict[str, Any] | None = None,
    ) -> PatternInstallation | None:
        """Install a pattern for the organization."""
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.status != PublishStatus.PUBLISHED:
            return None

        # Check if already installed
        for inst in self._installations.values():
            if inst.pattern_id == pattern_id and inst.organization_id == self.organization_id:
                return inst

        # Check license requirements
        if pattern.license_type == LicenseType.COMMERCIAL:
            # Check if purchased
            purchased = any(
                p.pattern_id == pattern_id and p.organization_id == self.organization_id
                for p in self._purchases.values()
            )
            if not purchased:
                return None

        installation = PatternInstallation(
            pattern_id=pattern_id,
            organization_id=self.organization_id,
            installed_version=pattern.current_version,
            custom_config=custom_config or {},
        )

        self._installations[installation.id] = installation
        pattern.downloads += 1
        pattern.active_users += 1

        logger.info(
            "Pattern installed",
            pattern_id=str(pattern_id),
            organization_id=str(self.organization_id),
        )

        return installation

    def uninstall_pattern(self, pattern_id: UUID) -> bool:
        """Uninstall a pattern."""
        to_remove = None
        for inst_id, inst in self._installations.items():
            if inst.pattern_id == pattern_id and inst.organization_id == self.organization_id:
                to_remove = inst_id
                break

        if to_remove:
            del self._installations[to_remove]
            pattern = self._patterns.get(pattern_id)
            if pattern:
                pattern.active_users = max(0, pattern.active_users - 1)
            return True

        return False

    def get_installed_patterns(self) -> list[tuple[PatternInstallation, CompliancePattern]]:
        """Get all patterns installed by the organization."""
        result = []
        for inst in self._installations.values():
            if inst.organization_id == self.organization_id:
                pattern = self._patterns.get(inst.pattern_id)
                if pattern:
                    result.append((inst, pattern))
        return result

    def update_installation_config(
        self,
        installation_id: UUID,
        config: dict[str, Any],
    ) -> PatternInstallation | None:
        """Update installation configuration."""
        installation = self._installations.get(installation_id)
        if not installation or installation.organization_id != self.organization_id:
            return None

        installation.custom_config.update(config)
        return installation

    # ========================================================================
    # Ratings & Reviews
    # ========================================================================

    def rate_pattern(
        self,
        pattern_id: UUID,
        rating: int,
        review: str = "",
        user_id: UUID | None = None,
    ) -> PatternRating | None:
        """Rate and review a pattern."""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return None

        if rating < 1 or rating > 5:
            return None

        pattern_rating = PatternRating(
            pattern_id=pattern_id,
            user_id=user_id,
            organization_id=self.organization_id,
            rating=rating,
            review=review,
        )

        if pattern_id not in self._ratings:
            self._ratings[pattern_id] = []
        self._ratings[pattern_id].append(pattern_rating)

        # Update pattern average
        all_ratings = self._ratings[pattern_id]
        pattern.avg_rating = sum(r.rating for r in all_ratings) / len(all_ratings)
        pattern.rating_count = len(all_ratings)

        return pattern_rating

    def get_pattern_ratings(
        self,
        pattern_id: UUID,
        limit: int = 50,
    ) -> list[PatternRating]:
        """Get ratings for a pattern."""
        ratings = self._ratings.get(pattern_id, [])
        ratings.sort(key=lambda r: r.created_at, reverse=True)
        return ratings[:limit]

    # ========================================================================
    # Purchasing & Revenue
    # ========================================================================

    def purchase_pattern(
        self,
        pattern_id: UUID,
        user_id: UUID | None = None,
        stripe_payment_id: str = "",
    ) -> PatternPurchase | None:
        """Record a pattern purchase."""
        pattern = self._patterns.get(pattern_id)
        if not pattern or pattern.license_type == LicenseType.FREE:
            return None

        purchase = PatternPurchase(
            pattern_id=pattern_id,
            organization_id=self.organization_id,
            user_id=user_id,
            price_paid=pattern.price,
            license_type=pattern.license_type,
            stripe_payment_id=stripe_payment_id,
        )

        self._purchases[purchase.id] = purchase

        logger.info(
            "Pattern purchased",
            pattern_id=str(pattern_id),
            organization_id=str(self.organization_id),
            price=pattern.price,
        )

        return purchase

    def get_purchases(self) -> list[PatternPurchase]:
        """Get all purchases by the organization."""
        return [
            p for p in self._purchases.values()
            if p.organization_id == self.organization_id
        ]

    # ========================================================================
    # Publisher Management
    # ========================================================================

    def create_publisher_profile(
        self,
        display_name: str,
        description: str = "",
        website: str = "",
        support_email: str = "",
    ) -> PublisherProfile:
        """Create a publisher profile for the organization."""
        profile = PublisherProfile(
            organization_id=self.organization_id,
            display_name=display_name,
            description=description,
            website=website,
            support_email=support_email,
        )

        self._publishers[profile.id] = profile
        return profile

    def get_publisher_profile(self) -> PublisherProfile | None:
        """Get the publisher profile for the organization."""
        for profile in self._publishers.values():
            if profile.organization_id == self.organization_id:
                return profile
        return None

    def get_publisher_patterns(self) -> list[CompliancePattern]:
        """Get all patterns published by the organization."""
        return [
            p for p in self._patterns.values()
            if p.publisher_org_id == self.organization_id
        ]

    def get_publisher_earnings(self) -> dict[str, Any]:
        """Get earnings summary for the publisher."""
        patterns = self.get_publisher_patterns()
        pattern_ids = {p.id for p in patterns}

        total_earnings = 0.0
        purchases = []

        for purchase in self._purchases.values():
            if purchase.pattern_id in pattern_ids and not purchase.refunded:
                # Calculate publisher share (70% default)
                earnings = purchase.price_paid * 0.7
                total_earnings += earnings
                purchases.append({
                    "pattern_id": str(purchase.pattern_id),
                    "amount": earnings,
                    "date": purchase.purchased_at.isoformat(),
                })

        return {
            "total_earnings": total_earnings,
            "pending_payout": total_earnings,  # Simplified
            "purchases": purchases,
            "total_downloads": sum(p.downloads for p in patterns),
        }

    # ========================================================================
    # Marketplace Statistics
    # ========================================================================

    def get_marketplace_stats(self) -> MarketplaceStats:
        """Get overall marketplace statistics."""
        published = [p for p in self._patterns.values() if p.status == PublishStatus.PUBLISHED]

        stats = MarketplaceStats(
            total_patterns=len(published),
            total_publishers=len({p.publisher_org_id for p in published if p.publisher_org_id}),
            total_downloads=sum(p.downloads for p in published),
            total_revenue=sum(p.price_paid for p in self._purchases.values()),
        )

        # By category
        for pattern in published:
            cat = pattern.category.value
            stats.patterns_by_category[cat] = stats.patterns_by_category.get(cat, 0) + 1
            stats.downloads_by_category[cat] = stats.downloads_by_category.get(cat, 0) + pattern.downloads

        # By regulation
        for pattern in published:
            for reg in pattern.regulations:
                stats.patterns_by_regulation[reg] = stats.patterns_by_regulation.get(reg, 0) + 1

        # Top patterns
        top = sorted(published, key=lambda p: p.downloads, reverse=True)[:5]
        stats.top_patterns = [{"name": p.name, "downloads": p.downloads} for p in top]

        # Trending (recent + downloads)
        trending = sorted(
            published,
            key=lambda p: p.downloads * (1.0 if not p.published_at else 1.0),
            reverse=True,
        )[:5]
        stats.trending_patterns = [{"name": p.name, "downloads": p.downloads} for p in trending]

        return stats


def get_pattern_marketplace_service(
    db: AsyncSession,
    organization_id: UUID | None = None,
) -> PatternMarketplaceService:
    """Factory function to create Pattern Marketplace service."""
    return PatternMarketplaceService(db=db, organization_id=organization_id)
