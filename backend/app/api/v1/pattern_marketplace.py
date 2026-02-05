"""API endpoints for Compliance Pattern Marketplace."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.pattern_marketplace import (
    LicenseType,
    PatternCategory,
    PatternType,
    get_pattern_marketplace_service,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class PatternSearchRequest(BaseModel):
    """Request to search patterns."""

    query: str | None = None
    category: str | None = None
    pattern_type: str | None = None
    regulations: list[str] | None = None
    languages: list[str] | None = None
    license_types: list[str] | None = None
    free_only: bool = False
    sort_by: str = "downloads"


class PatternResponse(BaseModel):
    """Response containing pattern details."""

    id: str
    slug: str
    name: str
    description: str
    long_description: str
    category: str
    pattern_type: str
    regulations: list[str]
    languages: list[str]
    tags: list[str]
    current_version: str
    publisher_name: str
    publisher_verified: bool
    license_type: str
    price: float
    price_type: str
    status: str
    downloads: int
    active_users: int
    avg_rating: float
    rating_count: int
    fork_count: int
    created_at: str
    published_at: str | None


class PatternDetailResponse(PatternResponse):
    """Detailed pattern response with content."""

    content: dict[str, Any]
    versions: list[dict[str, Any]]
    forked_from: str | None


class CreatePatternRequest(BaseModel):
    """Request to create a pattern."""

    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    long_description: str | None = None
    category: str
    pattern_type: str
    content: dict[str, Any]
    regulations: list[str] | None = None
    languages: list[str] | None = None
    tags: list[str] | None = None
    license_type: str = "free"
    price: float = 0.0


class UpdatePatternRequest(BaseModel):
    """Request to update a pattern."""

    name: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = Field(None, min_length=10, max_length=500)
    long_description: str | None = None
    category: str | None = None
    pattern_type: str | None = None
    content: dict[str, Any] | None = None
    regulations: list[str] | None = None
    languages: list[str] | None = None
    tags: list[str] | None = None
    license_type: str | None = None
    price: float | None = None


class AddVersionRequest(BaseModel):
    """Request to add a new version."""

    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    changelog: str
    content: dict[str, Any]


class InstallPatternRequest(BaseModel):
    """Request to install a pattern."""

    custom_config: dict[str, Any] | None = None


class RatePatternRequest(BaseModel):
    """Request to rate a pattern."""

    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class CreatePublisherRequest(BaseModel):
    """Request to create publisher profile."""

    display_name: str = Field(..., min_length=3, max_length=100)
    description: str | None = None
    website: str | None = None
    support_email: str | None = None


class InstallationResponse(BaseModel):
    """Response containing installation details."""

    id: str
    pattern_id: str
    installed_version: str
    auto_update: bool
    enabled: bool
    custom_config: dict[str, Any]
    installed_at: str


class RatingResponse(BaseModel):
    """Response containing rating details."""

    id: str
    rating: int
    review: str
    helpful_votes: int
    created_at: str


class PublisherResponse(BaseModel):
    """Response containing publisher profile."""

    id: str
    display_name: str
    description: str
    website: str
    verified: bool
    total_patterns: int
    total_downloads: int
    avg_rating: float


class MarketplaceStatsResponse(BaseModel):
    """Response containing marketplace statistics."""

    total_patterns: int
    total_publishers: int
    total_downloads: int
    patterns_by_category: dict[str, int]
    patterns_by_regulation: dict[str, int]
    top_patterns: list[dict[str, Any]]
    trending_patterns: list[dict[str, Any]]


# ============================================================================
# Helper Functions
# ============================================================================


def _pattern_to_response(pattern) -> PatternResponse:
    """Convert pattern to response model."""
    return PatternResponse(
        id=str(pattern.id),
        slug=pattern.slug,
        name=pattern.name,
        description=pattern.description,
        long_description=pattern.long_description,
        category=pattern.category.value,
        pattern_type=pattern.pattern_type.value,
        regulations=pattern.regulations,
        languages=pattern.languages,
        tags=pattern.tags,
        current_version=pattern.current_version,
        publisher_name=pattern.publisher_name,
        publisher_verified=pattern.publisher_verified,
        license_type=pattern.license_type.value,
        price=pattern.price,
        price_type=pattern.price_type,
        status=pattern.status.value,
        downloads=pattern.downloads,
        active_users=pattern.active_users,
        avg_rating=pattern.avg_rating,
        rating_count=pattern.rating_count,
        fork_count=pattern.fork_count,
        created_at=pattern.created_at.isoformat(),
        published_at=pattern.published_at.isoformat() if pattern.published_at else None,
    )


def _pattern_to_detail_response(pattern) -> PatternDetailResponse:
    """Convert pattern to detailed response model."""
    return PatternDetailResponse(
        id=str(pattern.id),
        slug=pattern.slug,
        name=pattern.name,
        description=pattern.description,
        long_description=pattern.long_description,
        category=pattern.category.value,
        pattern_type=pattern.pattern_type.value,
        regulations=pattern.regulations,
        languages=pattern.languages,
        tags=pattern.tags,
        current_version=pattern.current_version,
        publisher_name=pattern.publisher_name,
        publisher_verified=pattern.publisher_verified,
        license_type=pattern.license_type.value,
        price=pattern.price,
        price_type=pattern.price_type,
        status=pattern.status.value,
        downloads=pattern.downloads,
        active_users=pattern.active_users,
        avg_rating=pattern.avg_rating,
        rating_count=pattern.rating_count,
        fork_count=pattern.fork_count,
        created_at=pattern.created_at.isoformat(),
        published_at=pattern.published_at.isoformat() if pattern.published_at else None,
        content=pattern.content,
        versions=[v.to_dict() for v in pattern.versions],
        forked_from=str(pattern.forked_from) if pattern.forked_from else None,
    )


# ============================================================================
# Pattern Discovery Endpoints
# ============================================================================


@router.get("/patterns", response_model=dict[str, Any])
async def search_patterns(
    db: DB,
    query: str | None = Query(None),
    category: str | None = Query(None),
    pattern_type: str | None = Query(None),
    regulations: str | None = Query(None),  # Comma-separated
    languages: str | None = Query(None),  # Comma-separated
    free_only: bool = Query(False),
    sort_by: str = Query("downloads"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Search and browse compliance patterns in the marketplace.

    This is a public endpoint - no authentication required.
    """
    service = get_pattern_marketplace_service(db=db)

    # Parse filter values
    cat = PatternCategory(category) if category else None
    ptype = PatternType(pattern_type) if pattern_type else None
    regs = regulations.split(",") if regulations else None
    langs = languages.split(",") if languages else None

    patterns, total = service.search_patterns(
        query=query,
        category=cat,
        pattern_type=ptype,
        regulations=regs,
        languages=langs,
        free_only=free_only,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

    return {
        "patterns": [_pattern_to_response(p) for p in patterns],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/patterns/featured", response_model=list[PatternResponse])
async def get_featured_patterns(
    db: DB,
    limit: int = Query(10, ge=1, le=50),
) -> list[PatternResponse]:
    """Get featured/trending patterns."""
    service = get_pattern_marketplace_service(db=db)
    patterns = service.get_featured_patterns(limit=limit)
    return [_pattern_to_response(p) for p in patterns]


@router.get("/patterns/by-regulation/{regulation}", response_model=list[PatternResponse])
async def get_patterns_by_regulation(
    regulation: str,
    db: DB,
) -> list[PatternResponse]:
    """Get all patterns for a specific regulation."""
    service = get_pattern_marketplace_service(db=db)
    patterns = service.get_patterns_by_regulation(regulation)
    return [_pattern_to_response(p) for p in patterns]


@router.get("/patterns/{pattern_id}", response_model=PatternDetailResponse)
async def get_pattern(
    pattern_id: str,
    db: DB,
) -> PatternDetailResponse:
    """Get detailed information about a pattern."""
    service = get_pattern_marketplace_service(db=db)

    try:
        uuid_id = UUID(pattern_id)
        pattern = service.get_pattern(uuid_id)
    except ValueError:
        # Try by slug
        pattern = service.get_pattern_by_slug(pattern_id)

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found",
        )

    return _pattern_to_detail_response(pattern)


# ============================================================================
# Pattern Publishing Endpoints (Authenticated)
# ============================================================================


@router.post("/patterns", response_model=PatternDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_pattern(
    request: CreatePatternRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PatternDetailResponse:
    """Create a new compliance pattern (draft)."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        category = PatternCategory(request.category)
        pattern_type = PatternType(request.pattern_type)
        license_type = LicenseType(request.license_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid enum value: {e}",
        )

    pattern = service.create_pattern(
        name=request.name,
        description=request.description,
        category=category,
        pattern_type=pattern_type,
        content=request.content,
        regulations=request.regulations,
        languages=request.languages,
        tags=request.tags,
        license_type=license_type,
        price=request.price,
    )

    return _pattern_to_detail_response(pattern)


@router.patch("/patterns/{pattern_id}", response_model=PatternDetailResponse)
async def update_pattern(
    pattern_id: str,
    request: UpdatePatternRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PatternDetailResponse:
    """Update a pattern you own."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    pattern = service.update_pattern(uuid_id, updates)

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found or you don't have permission to edit it",
        )

    return _pattern_to_detail_response(pattern)


@router.post("/patterns/{pattern_id}/publish")
async def publish_pattern(
    pattern_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Publish a draft pattern to the marketplace."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    pattern = service.publish_pattern(uuid_id)
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found or you don't have permission to publish it",
        )

    return {
        "published": True,
        "pattern_id": str(pattern.id),
        "status": pattern.status.value,
    }


@router.post("/patterns/{pattern_id}/versions", response_model=PatternDetailResponse)
async def add_version(
    pattern_id: str,
    request: AddVersionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PatternDetailResponse:
    """Add a new version to a pattern."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    pattern = service.add_version(
        uuid_id,
        version=request.version,
        changelog=request.changelog,
        content=request.content,
    )

    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found or you don't have permission to edit it",
        )

    return _pattern_to_detail_response(pattern)


@router.post("/patterns/{pattern_id}/fork", response_model=PatternDetailResponse)
async def fork_pattern(
    pattern_id: str,
    name: str = Query(..., min_length=3),
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> PatternDetailResponse:
    """Fork an existing pattern."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    pattern = service.fork_pattern(uuid_id, name)
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found or cannot be forked",
        )

    return _pattern_to_detail_response(pattern)


# ============================================================================
# Installation Endpoints
# ============================================================================


@router.post("/patterns/{pattern_id}/install", response_model=InstallationResponse)
async def install_pattern(
    pattern_id: str,
    request: InstallPatternRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> InstallationResponse:
    """Install a pattern for your organization."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    installation = service.install_pattern(uuid_id, custom_config=request.custom_config)
    if not installation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pattern not found, not published, or requires purchase",
        )

    return InstallationResponse(
        id=str(installation.id),
        pattern_id=str(installation.pattern_id),
        installed_version=installation.installed_version,
        auto_update=installation.auto_update,
        enabled=installation.enabled,
        custom_config=installation.custom_config,
        installed_at=installation.installed_at.isoformat(),
    )


@router.delete("/patterns/{pattern_id}/install")
async def uninstall_pattern(
    pattern_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, bool]:
    """Uninstall a pattern from your organization."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    success = service.uninstall_pattern(uuid_id)
    return {"uninstalled": success}


@router.get("/installed", response_model=list[dict[str, Any]])
async def get_installed_patterns(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[dict[str, Any]]:
    """Get all patterns installed by your organization."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)
    installations = service.get_installed_patterns()

    return [
        {
            "installation": inst.to_dict(),
            "pattern": _pattern_to_response(pattern).model_dump(),
        }
        for inst, pattern in installations
    ]


# ============================================================================
# Rating Endpoints
# ============================================================================


@router.post("/patterns/{pattern_id}/ratings", response_model=RatingResponse)
async def rate_pattern(
    pattern_id: str,
    request: RatePatternRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RatingResponse:
    """Rate and review a pattern."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    rating = service.rate_pattern(
        uuid_id,
        rating=request.rating,
        review=request.review or "",
        user_id=member.user_id,
    )

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found",
        )

    return RatingResponse(
        id=str(rating.id),
        rating=rating.rating,
        review=rating.review,
        helpful_votes=rating.helpful_votes,
        created_at=rating.created_at.isoformat(),
    )


@router.get("/patterns/{pattern_id}/ratings", response_model=list[RatingResponse])
async def get_pattern_ratings(
    pattern_id: str,
    db: DB,
    limit: int = Query(50, ge=1, le=100),
) -> list[RatingResponse]:
    """Get ratings for a pattern."""
    service = get_pattern_marketplace_service(db=db)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    ratings = service.get_pattern_ratings(uuid_id, limit=limit)
    return [
        RatingResponse(
            id=str(r.id),
            rating=r.rating,
            review=r.review,
            helpful_votes=r.helpful_votes,
            created_at=r.created_at.isoformat(),
        )
        for r in ratings
    ]


# ============================================================================
# Publisher Endpoints
# ============================================================================


@router.post("/publisher", response_model=PublisherResponse)
async def create_publisher_profile(
    request: CreatePublisherRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PublisherResponse:
    """Create a publisher profile for your organization."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    profile = service.create_publisher_profile(
        display_name=request.display_name,
        description=request.description or "",
        website=request.website or "",
        support_email=request.support_email or "",
    )

    return PublisherResponse(
        id=str(profile.id),
        display_name=profile.display_name,
        description=profile.description,
        website=profile.website,
        verified=profile.verified,
        total_patterns=profile.total_patterns,
        total_downloads=profile.total_downloads,
        avg_rating=profile.avg_rating,
    )


@router.get("/publisher", response_model=PublisherResponse | None)
async def get_publisher_profile(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PublisherResponse | None:
    """Get your organization's publisher profile."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)
    profile = service.get_publisher_profile()

    if not profile:
        return None

    return PublisherResponse(
        id=str(profile.id),
        display_name=profile.display_name,
        description=profile.description,
        website=profile.website,
        verified=profile.verified,
        total_patterns=profile.total_patterns,
        total_downloads=profile.total_downloads,
        avg_rating=profile.avg_rating,
    )


@router.get("/publisher/patterns", response_model=list[PatternResponse])
async def get_my_patterns(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[PatternResponse]:
    """Get all patterns published by your organization."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)
    patterns = service.get_publisher_patterns()
    return [_pattern_to_response(p) for p in patterns]


@router.get("/publisher/earnings")
async def get_publisher_earnings(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get earnings summary for your publisher account."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)
    return service.get_publisher_earnings()


# ============================================================================
# Purchase & Checkout Endpoints
# ============================================================================


class PurchaseCheckoutRequest(BaseModel):
    """Request to initiate pattern purchase checkout."""

    pattern_id: str


class PurchaseCheckoutResponse(BaseModel):
    """Response with checkout session details."""

    checkout_url: str
    session_id: str
    pattern_id: str
    price: float


class SetupPayoutsRequest(BaseModel):
    """Request to set up publisher payouts."""

    email: str


class SetupPayoutsResponse(BaseModel):
    """Response with payout setup details."""

    account_id: str
    onboarding_url: str
    charges_enabled: bool
    payouts_enabled: bool


@router.post("/patterns/{pattern_id}/checkout", response_model=PurchaseCheckoutResponse)
async def create_purchase_checkout(
    pattern_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PurchaseCheckoutResponse:
    """Create a Stripe checkout session to purchase a pattern.

    Returns a checkout URL to redirect the user to complete payment.
    After successful payment, the webhook will create the purchase record.
    """
    from app.services.billing import pattern_purchase_service

    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)

    try:
        uuid_id = UUID(pattern_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pattern ID",
        )

    # Get pattern details
    pattern = service.get_pattern(uuid_id)
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pattern not found",
        )

    # Check if pattern requires purchase
    if pattern.license_type == LicenseType.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This pattern is free. Use the install endpoint instead.",
        )

    # Check if already purchased
    purchases = service.get_purchases()
    if any(p.pattern_id == uuid_id for p in purchases):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pattern already purchased",
        )

    # Get publisher's Stripe Connect account (if they have one)
    publisher_connect_account_id = None
    # In production, would look up the publisher profile's stripe_connect_account_id

    # Create checkout session
    checkout = await pattern_purchase_service.create_purchase_checkout(
        pattern_id=uuid_id,
        pattern_name=pattern.name,
        pattern_description=pattern.description,
        price=pattern.price,
        organization_id=organization.id,
        user_id=member.user_id,
        publisher_connect_account_id=publisher_connect_account_id,
    )

    return PurchaseCheckoutResponse(
        checkout_url=checkout.url,
        session_id=checkout.id,
        pattern_id=str(pattern.id),
        price=checkout.price,
    )


@router.get("/purchases", response_model=list[dict[str, Any]])
async def get_purchases(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[dict[str, Any]]:
    """Get all pattern purchases for your organization."""
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)
    purchases = service.get_purchases()

    result = []
    for purchase in purchases:
        pattern = service.get_pattern(purchase.pattern_id)
        result.append({
            "id": str(purchase.id),
            "pattern_id": str(purchase.pattern_id),
            "pattern_name": pattern.name if pattern else "Unknown",
            "price_paid": purchase.price_paid,
            "license_type": purchase.license_type.value,
            "purchased_at": purchase.purchased_at.isoformat(),
            "refunded": purchase.refunded,
        })

    return result


@router.post("/publisher/setup-payouts", response_model=SetupPayoutsResponse)
async def setup_publisher_payouts(
    request: SetupPayoutsRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SetupPayoutsResponse:
    """Set up Stripe Connect for receiving pattern sale payouts.

    Returns an onboarding URL to complete the Stripe Connect setup.
    """
    from app.services.billing import pattern_purchase_service

    # Verify publisher profile exists
    service = get_pattern_marketplace_service(db=db, organization_id=organization.id)
    profile = service.get_publisher_profile()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create a publisher profile first",
        )

    # Set up Stripe Connect
    account = await pattern_purchase_service.setup_publisher_payouts(
        organization_id=organization.id,
        organization_name=profile.display_name,
        email=request.email,
    )

    return SetupPayoutsResponse(
        account_id=account.id,
        onboarding_url=account.onboarding_url or "",
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
    )


@router.get("/publisher/dashboard-url")
async def get_publisher_dashboard_url(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, str]:
    """Get URL to access the Stripe dashboard for viewing payouts."""
    from sqlalchemy import select

    from app.models.pattern_marketplace import PublisherProfile
    from app.services.billing import pattern_purchase_service

    # Get publisher's Connect account ID
    result = await db.execute(
        select(PublisherProfile).where(
            PublisherProfile.organization_id == organization.id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile or not profile.stripe_connect_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe Connect not set up. Use /publisher/setup-payouts first.",
        )

    url = await pattern_purchase_service.get_publisher_dashboard_url(
        profile.stripe_connect_account_id
    )

    return {"dashboard_url": url}


# ============================================================================
# Marketplace Stats
# ============================================================================


@router.get("/stats", response_model=MarketplaceStatsResponse)
async def get_marketplace_stats(
    db: DB,
) -> MarketplaceStatsResponse:
    """Get overall marketplace statistics."""
    service = get_pattern_marketplace_service(db=db)
    stats = service.get_marketplace_stats()

    return MarketplaceStatsResponse(
        total_patterns=stats.total_patterns,
        total_publishers=stats.total_publishers,
        total_downloads=stats.total_downloads,
        patterns_by_category=stats.patterns_by_category,
        patterns_by_regulation=stats.patterns_by_regulation,
        top_patterns=stats.top_patterns,
        trending_patterns=stats.trending_patterns,
    )


# ============================================================================
# Categories & Metadata
# ============================================================================


@router.get("/categories")
async def list_categories() -> list[dict[str, str]]:
    """List all available pattern categories."""
    return [
        {"value": cat.value, "name": cat.name.replace("_", " ").title()}
        for cat in PatternCategory
    ]


@router.get("/pattern-types")
async def list_pattern_types() -> list[dict[str, str]]:
    """List all available pattern types."""
    return [
        {"value": pt.value, "name": pt.name.replace("_", " ").title()}
        for pt in PatternType
    ]


@router.get("/license-types")
async def list_license_types() -> list[dict[str, str]]:
    """List all available license types."""
    return [
        {"value": lt.value, "name": lt.name.replace("_", " ").title()}
        for lt in LicenseType
    ]
