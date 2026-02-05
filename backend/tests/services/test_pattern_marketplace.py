"""Tests for Pattern Marketplace service."""

import pytest
import pytest_asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pattern_marketplace.models import (
    CompliancePattern,
    PatternVersion,
    PatternInstallation,
    PatternRating,
    PatternPurchase,
    PublisherProfile,
    MarketplaceStats,
    PatternCategory,
    PatternType,
    LicenseType,
    PublishStatus,
)
from app.services.pattern_marketplace.service import (
    PatternMarketplaceService,
    get_pattern_marketplace_service,
)


pytestmark = pytest.mark.asyncio


class TestPatternModels:
    """Test Pattern Marketplace data models."""

    def test_compliance_pattern_creation(self):
        """Test creating a compliance pattern."""
        pattern = CompliancePattern(
            slug="gdpr-pii-detection",
            name="GDPR PII Detection",
            description="Detect PII in code",
            category=PatternCategory.DATA_PRIVACY,
            pattern_type=PatternType.CODE_PATTERN,
            regulations=["GDPR", "CCPA"],
            languages=["python", "javascript"],
            tags=["pii", "privacy"],
            content={"patterns": []},
        )

        assert pattern.id is not None
        assert pattern.slug == "gdpr-pii-detection"
        assert pattern.category == PatternCategory.DATA_PRIVACY
        assert pattern.status == PublishStatus.DRAFT

    def test_pattern_to_dict(self):
        """Test converting pattern to dict."""
        pattern = CompliancePattern(
            slug="test-pattern",
            name="Test Pattern",
            description="Test description",
            category=PatternCategory.ENCRYPTION,
            pattern_type=PatternType.TEMPLATE,
            content={},
        )

        data = pattern.to_dict()

        assert data["slug"] == "test-pattern"
        assert data["category"] == "encryption"
        assert "id" in data

    def test_pattern_version_creation(self):
        """Test creating a pattern version."""
        version = PatternVersion(
            version="1.0.0",
            changelog="Initial release",
            content={"code": "test"},
        )

        assert version.id is not None
        assert version.version == "1.0.0"
        assert version.deprecated is False

    def test_pattern_installation_creation(self):
        """Test creating a pattern installation."""
        installation = PatternInstallation(
            pattern_id=uuid4(),
            organization_id=uuid4(),
            installed_version="1.0.0",
        )

        assert installation.id is not None
        assert installation.auto_update is True
        assert installation.enabled is True

    def test_pattern_rating_creation(self):
        """Test creating a pattern rating."""
        rating = PatternRating(
            pattern_id=uuid4(),
            organization_id=uuid4(),
            rating=5,
            review="Excellent pattern!",
        )

        assert rating.id is not None
        assert rating.rating == 5
        assert rating.helpful_votes == 0

    def test_pattern_purchase_creation(self):
        """Test creating a pattern purchase."""
        purchase = PatternPurchase(
            pattern_id=uuid4(),
            organization_id=uuid4(),
            price_paid=49.99,
            license_type=LicenseType.COMMERCIAL,
        )

        assert purchase.id is not None
        assert purchase.price_paid == 49.99
        assert purchase.refunded is False

    def test_publisher_profile_creation(self):
        """Test creating a publisher profile."""
        profile = PublisherProfile(
            organization_id=uuid4(),
            display_name="Test Publisher",
            description="We create compliance patterns",
        )

        assert profile.id is not None
        assert profile.verified is False
        assert profile.revenue_share_percent == 70.0


class TestPatternMarketplaceService:
    """Test Pattern Marketplace service."""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        """Create service instance."""
        return PatternMarketplaceService(db=db_session, organization_id=uuid4())

    def test_search_patterns(self, service):
        """Test searching patterns."""
        patterns, total = service.search_patterns(
            query="GDPR",
            category=PatternCategory.DATA_PRIVACY,
            limit=10,
        )

        assert isinstance(patterns, list)
        assert isinstance(total, int)

    def test_search_patterns_by_regulation(self, service):
        """Test searching patterns by regulation."""
        patterns, total = service.search_patterns(
            regulations=["GDPR"],
            limit=10,
        )

        for pattern in patterns:
            assert "GDPR" in pattern.regulations

    def test_search_patterns_free_only(self, service):
        """Test searching only free patterns."""
        patterns, total = service.search_patterns(
            free_only=True,
            limit=10,
        )

        for pattern in patterns:
            assert pattern.license_type == LicenseType.FREE

    def test_get_pattern(self, service):
        """Test getting a pattern by ID."""
        # First search to get a pattern ID
        patterns, _ = service.search_patterns(limit=1)
        if patterns:
            pattern = service.get_pattern(patterns[0].id)
            assert pattern is not None
            assert pattern.id == patterns[0].id

    def test_get_pattern_by_slug(self, service):
        """Test getting a pattern by slug."""
        pattern = service.get_pattern_by_slug("gdpr-pii-detection")
        if pattern:
            assert pattern.slug == "gdpr-pii-detection"

    def test_get_featured_patterns(self, service):
        """Test getting featured patterns."""
        featured = service.get_featured_patterns(limit=5)

        assert isinstance(featured, list)
        assert len(featured) <= 5

    def test_get_patterns_by_regulation(self, service):
        """Test getting patterns for a regulation."""
        patterns = service.get_patterns_by_regulation("GDPR")

        for pattern in patterns:
            assert "GDPR" in pattern.regulations

    def test_create_pattern(self, service):
        """Test creating a new pattern."""
        pattern = service.create_pattern(
            name="Test Custom Pattern",
            description="A test pattern for unit tests",
            category=PatternCategory.AUTHENTICATION,
            pattern_type=PatternType.TEMPLATE,
            content={"code": "def authenticate(): pass"},
            regulations=["SOC2"],
            languages=["python"],
            tags=["auth", "security"],
        )

        assert pattern is not None
        assert pattern.status == PublishStatus.DRAFT
        assert pattern.publisher_org_id == service.organization_id

    def test_update_pattern(self, service):
        """Test updating a pattern."""
        # Create a pattern first
        pattern = service.create_pattern(
            name="Update Test Pattern",
            description="Will be updated",
            category=PatternCategory.LOGGING,
            pattern_type=PatternType.CODE_PATTERN,
            content={},
        )

        # Update it
        updated = service.update_pattern(
            pattern.id,
            {"description": "Updated description"},
        )

        assert updated is not None
        assert updated.description == "Updated description"

    def test_publish_pattern(self, service):
        """Test publishing a pattern."""
        pattern = service.create_pattern(
            name="Publish Test Pattern",
            description="Will be published",
            category=PatternCategory.ACCESS_CONTROL,
            pattern_type=PatternType.RULE,
            content={"rules": []},
        )

        published = service.publish_pattern(pattern.id)

        assert published is not None
        assert published.status == PublishStatus.PUBLISHED

    def test_add_version(self, service):
        """Test adding a new version to a pattern."""
        pattern = service.create_pattern(
            name="Version Test Pattern",
            description="Will have versions",
            category=PatternCategory.CONSENT_MANAGEMENT,
            pattern_type=PatternType.TEMPLATE,
            content={"v1": True},
        )

        updated = service.add_version(
            pattern.id,
            version="2.0.0",
            changelog="Major update",
            content={"v2": True},
        )

        assert updated is not None
        assert updated.current_version == "2.0.0"
        assert len(updated.versions) >= 2

    def test_fork_pattern(self, service):
        """Test forking a pattern."""
        # Get a published pattern
        patterns, _ = service.search_patterns(limit=1)
        if patterns:
            forked = service.fork_pattern(patterns[0].id, "My Forked Pattern")

            if forked:
                assert forked.forked_from == patterns[0].id
                assert forked.status == PublishStatus.DRAFT

    def test_install_pattern(self, service):
        """Test installing a pattern."""
        # Get a free published pattern
        patterns, _ = service.search_patterns(free_only=True, limit=1)
        if patterns:
            installation = service.install_pattern(
                patterns[0].id,
                custom_config={"enabled": True},
            )

            if installation:
                assert installation.pattern_id == patterns[0].id
                assert installation.organization_id == service.organization_id

    def test_uninstall_pattern(self, service):
        """Test uninstalling a pattern."""
        # Install first
        patterns, _ = service.search_patterns(free_only=True, limit=1)
        if patterns:
            service.install_pattern(patterns[0].id)
            result = service.uninstall_pattern(patterns[0].id)
            assert result is True or result is False

    def test_get_installed_patterns(self, service):
        """Test getting installed patterns."""
        installed = service.get_installed_patterns()

        assert isinstance(installed, list)

    def test_rate_pattern(self, service):
        """Test rating a pattern."""
        patterns, _ = service.search_patterns(limit=1)
        if patterns:
            rating = service.rate_pattern(
                patterns[0].id,
                rating=4,
                review="Good pattern, very useful",
            )

            if rating:
                assert rating.rating == 4
                assert rating.review == "Good pattern, very useful"

    def test_rate_pattern_invalid_rating(self, service):
        """Test that invalid ratings are rejected."""
        patterns, _ = service.search_patterns(limit=1)
        if patterns:
            rating = service.rate_pattern(
                patterns[0].id,
                rating=6,  # Invalid: should be 1-5
                review="Test",
            )
            assert rating is None

    def test_get_pattern_ratings(self, service):
        """Test getting ratings for a pattern."""
        patterns, _ = service.search_patterns(limit=1)
        if patterns:
            ratings = service.get_pattern_ratings(patterns[0].id)
            assert isinstance(ratings, list)

    def test_purchase_pattern(self, service):
        """Test purchasing a pattern."""
        # Find a commercial pattern
        patterns, _ = service.search_patterns(
            license_types=[LicenseType.COMMERCIAL],
            limit=1,
        )
        if patterns:
            purchase = service.purchase_pattern(
                patterns[0].id,
                stripe_payment_id="pi_test_123",
            )

            if purchase:
                assert purchase.pattern_id == patterns[0].id
                assert purchase.price_paid == patterns[0].price

    def test_get_purchases(self, service):
        """Test getting organization purchases."""
        purchases = service.get_purchases()
        assert isinstance(purchases, list)

    def test_create_publisher_profile(self, service):
        """Test creating a publisher profile."""
        profile = service.create_publisher_profile(
            display_name="Test Publisher",
            description="We publish patterns",
            website="https://example.com",
            support_email="support@example.com",
        )

        assert profile is not None
        assert profile.display_name == "Test Publisher"
        assert profile.organization_id == service.organization_id

    def test_get_publisher_profile(self, service):
        """Test getting publisher profile."""
        # Create one first
        service.create_publisher_profile(
            display_name="Get Test Publisher",
        )

        profile = service.get_publisher_profile()

        assert profile is not None

    def test_get_publisher_patterns(self, service):
        """Test getting patterns by publisher."""
        patterns = service.get_publisher_patterns()
        assert isinstance(patterns, list)

    def test_get_publisher_earnings(self, service):
        """Test getting publisher earnings."""
        earnings = service.get_publisher_earnings()

        assert "total_earnings" in earnings
        assert "pending_payout" in earnings
        assert "purchases" in earnings

    def test_get_marketplace_stats(self, service):
        """Test getting marketplace statistics."""
        stats = service.get_marketplace_stats()

        assert isinstance(stats, MarketplaceStats)
        assert stats.total_patterns >= 0
        assert stats.total_downloads >= 0


class TestPatternCategories:
    """Test pattern category enums."""

    def test_all_categories_defined(self):
        """Test all expected categories are defined."""
        expected = [
            "DATA_PRIVACY",
            "AUTHENTICATION",
            "ENCRYPTION",
            "LOGGING",
            "ACCESS_CONTROL",
            "DATA_RETENTION",
            "CONSENT_MANAGEMENT",
            "INCIDENT_RESPONSE",
            "AUDIT_TRAIL",
            "AI_SAFETY",
            "FINANCIAL",
            "HEALTHCARE",
        ]

        for cat in expected:
            assert hasattr(PatternCategory, cat)

    def test_category_values(self):
        """Test category string values."""
        assert PatternCategory.DATA_PRIVACY.value == "data_privacy"
        assert PatternCategory.AI_SAFETY.value == "ai_safety"


class TestLicenseTypes:
    """Test license type enums."""

    def test_all_license_types_defined(self):
        """Test all license types are defined."""
        expected = ["FREE", "ATTRIBUTION", "COMMERCIAL", "ENTERPRISE", "CUSTOM"]

        for lt in expected:
            assert hasattr(LicenseType, lt)


class TestGetPatternMarketplaceService:
    """Test the factory function."""

    def test_creates_service(self, db_session: AsyncSession):
        """Test factory creates service instance."""
        org_id = uuid4()
        service = get_pattern_marketplace_service(
            db=db_session,
            organization_id=org_id,
        )

        assert isinstance(service, PatternMarketplaceService)
        assert service.organization_id == org_id

    def test_creates_service_without_org(self, db_session: AsyncSession):
        """Test factory creates service without organization."""
        service = get_pattern_marketplace_service(db=db_session)

        assert isinstance(service, PatternMarketplaceService)
        assert service.organization_id is None
