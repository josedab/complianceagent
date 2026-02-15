"""Compliance-as-Code Policy Marketplace API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.policy_marketplace.models import (
    PolicyLanguage,
    PricingModel,
)
from app.services.policy_marketplace.service import PolicyMarketplaceService


router = APIRouter()

_service = PolicyMarketplaceService()


# --- Pydantic request/response models ---


class PolicyFileInput(BaseModel):
    """A policy file within a pack."""

    path: str
    language: str
    content: str
    description: str = ""


class CreatePackRequest(BaseModel):
    """Request to create a new policy pack."""

    creator_id: UUID
    title: str
    description: str
    regulations: list[str]
    languages: list[str]
    pricing_model: str = "free"
    price_usd: float = 0.0
    files: list[PolicyFileInput] = Field(default_factory=list)


class PurchaseRequest(BaseModel):
    """Request to purchase a policy pack."""

    user_id: UUID


class ReviewRequest(BaseModel):
    """Request to submit a review."""

    user_id: UUID
    rating: float = Field(ge=1.0, le=5.0)
    comment: str = ""


class RegisterCreatorRequest(BaseModel):
    """Request to register as a creator."""

    user_id: UUID
    display_name: str
    bio: str = ""
    expertise: list[str] = Field(default_factory=list)


class ValidatePolicyRequest(BaseModel):
    """Request to validate a policy file."""

    content: str
    language: str


class TestPolicyRequest(BaseModel):
    """Request to test a policy against scenarios."""

    content: str
    language: str
    test_scenarios: list[dict] | None = Field(
        default=None,
        description="Test scenarios with name, input, and expected outcome",
    )


# --- Helpers ---


def _parse_pricing_model(value: str) -> PricingModel:
    """Parse pricing model string to enum."""
    try:
        return PricingModel(value.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid pricing model: {value}")


def _parse_languages(values: list[str]) -> list[PolicyLanguage]:
    """Parse language strings to enums."""
    result = []
    for v in values:
        try:
            result.append(PolicyLanguage(v.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid language: {v}")
    return result


def _pack_to_dict(pack) -> dict:
    """Convert a PolicyPack to a JSON-serializable dict."""
    return {
        "id": str(pack.id),
        "creator_id": str(pack.creator_id),
        "title": pack.title,
        "description": pack.description,
        "version": pack.version,
        "regulations": pack.regulations,
        "languages": [lang.value for lang in pack.languages],
        "pricing_model": pack.pricing_model.value,
        "price_usd": pack.price_usd,
        "revenue_share_pct": pack.revenue_share_pct,
        "status": pack.status.value,
        "downloads": pack.downloads,
        "rating": pack.rating,
        "review_count": pack.review_count,
        "tags": pack.tags,
        "created_at": pack.created_at.isoformat(),
        "updated_at": pack.updated_at.isoformat(),
    }


# --- Endpoints ---


@router.get("/packs")
async def list_packs(
    category: str | None = None,
    regulation: str | None = None,
    language: str | None = None,
    pricing: str | None = None,
    sort: str = "popular",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List policy packs with filtering and sorting."""
    packs = await _service.list_packs(
        category=category,
        regulation=regulation,
        language=language,
        pricing=pricing,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return {
        "packs": [_pack_to_dict(p) for p in packs],
        "total": len(packs),
    }


@router.get("/packs/{pack_id}")
async def get_pack(pack_id: UUID):
    """Get policy pack details."""
    pack = await _service.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Policy pack not found")
    return _pack_to_dict(pack)


@router.post("/packs")
async def create_pack(request: CreatePackRequest):
    """Create a new policy pack."""
    from app.services.policy_marketplace.models import PolicyFile

    languages = _parse_languages(request.languages)
    pricing = _parse_pricing_model(request.pricing_model)
    files = [
        PolicyFile(
            path=f.path,
            language=PolicyLanguage(f.language.lower()),
            content=f.content,
            description=f.description,
        )
        for f in request.files
    ]
    pack = await _service.create_pack(
        creator_id=request.creator_id,
        title=request.title,
        description=request.description,
        regulations=request.regulations,
        languages=languages,
        pricing_model=pricing,
        price_usd=request.price_usd,
        files=files,
    )
    return _pack_to_dict(pack)


@router.put("/packs/{pack_id}/publish")
async def publish_pack(pack_id: UUID):
    """Publish a draft policy pack to the marketplace."""
    try:
        pack = await _service.publish_pack(pack_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _pack_to_dict(pack)


@router.post("/packs/{pack_id}/purchase")
async def purchase_pack(pack_id: UUID, request: PurchaseRequest):
    """Purchase a policy pack."""
    try:
        purchase = await _service.purchase_pack(request.user_id, pack_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": str(purchase.id),
        "user_id": str(purchase.user_id),
        "pack_id": str(purchase.pack_id),
        "price_usd": purchase.price_usd,
        "creator_payout_usd": purchase.creator_payout_usd,
        "platform_fee_usd": purchase.platform_fee_usd,
        "purchased_at": purchase.purchased_at.isoformat(),
    }


@router.get("/packs/{pack_id}/download")
async def download_pack(pack_id: UUID, user_id: UUID = Query(...)):
    """Download the latest version of a policy pack."""
    try:
        version = await _service.download_pack(user_id, pack_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": str(version.id),
        "pack_id": str(version.pack_id),
        "version": version.version,
        "changelog": version.changelog,
        "files": [
            {
                "path": f.path,
                "language": f.language.value,
                "content": f.content,
                "description": f.description,
            }
            for f in version.files
        ],
        "published_at": version.published_at.isoformat(),
    }


@router.post("/packs/{pack_id}/reviews")
async def submit_review(pack_id: UUID, request: ReviewRequest):
    """Submit a review for a policy pack."""
    try:
        review = await _service.submit_review(
            request.user_id, pack_id, request.rating, request.comment
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": str(review.id),
        "pack_id": str(review.pack_id),
        "user_id": str(review.user_id),
        "rating": review.rating,
        "comment": review.comment,
        "verified_purchase": review.verified_purchase,
        "created_at": review.created_at.isoformat(),
    }


@router.get("/packs/{pack_id}/reviews")
async def get_reviews(
    pack_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get reviews for a policy pack."""
    reviews = await _service.get_reviews(pack_id, limit=limit)
    return {
        "reviews": [
            {
                "id": str(r.id),
                "pack_id": str(r.pack_id),
                "user_id": str(r.user_id),
                "rating": r.rating,
                "comment": r.comment,
                "verified_purchase": r.verified_purchase,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
        "total": len(reviews),
    }


@router.get("/creators/{creator_id}")
async def get_creator_profile(creator_id: UUID):
    """Get a creator's public profile."""
    profile = await _service.get_creator_profile(creator_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Creator not found")
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "display_name": profile.display_name,
        "bio": profile.bio,
        "expertise": profile.expertise,
        "published_packs": profile.published_packs,
        "total_downloads": profile.total_downloads,
        "total_earnings_usd": profile.total_earnings_usd,
        "verified": profile.verified,
        "joined_at": profile.joined_at.isoformat(),
    }


@router.post("/creators/register")
async def register_creator(request: RegisterCreatorRequest):
    """Register as a marketplace creator."""
    try:
        profile = await _service.register_creator(
            request.user_id, request.display_name, request.bio, request.expertise
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "display_name": profile.display_name,
        "bio": profile.bio,
        "expertise": profile.expertise,
        "published_packs": profile.published_packs,
        "total_downloads": profile.total_downloads,
        "total_earnings_usd": profile.total_earnings_usd,
        "verified": profile.verified,
        "joined_at": profile.joined_at.isoformat(),
    }


@router.get("/creators/{creator_id}/earnings")
async def get_creator_earnings(creator_id: UUID):
    """Get a creator's earnings breakdown."""
    try:
        earnings = await _service.get_creator_earnings(creator_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return earnings


@router.get("/stats")
async def get_marketplace_stats():
    """Get aggregate marketplace statistics."""
    stats = await _service.get_marketplace_stats()
    return {
        "total_packs": stats.total_packs,
        "total_creators": stats.total_creators,
        "total_downloads": stats.total_downloads,
        "total_gmv_usd": stats.total_gmv_usd,
        "top_categories": stats.top_categories,
    }


@router.get("/bundles")
async def list_bundles():
    """List available policy pack bundles."""
    bundles = await _service.list_bundles()
    return {
        "bundles": [
            {
                "id": str(b.id),
                "name": b.name,
                "description": b.description,
                "packs": b.packs,
                "bundle_price_usd": b.bundle_price_usd,
                "savings_pct": b.savings_pct,
            }
            for b in bundles
        ],
        "total": len(bundles),
    }


@router.post("/validate")
async def validate_policy(request: ValidatePolicyRequest):
    """Validate a policy file for syntax and best practices."""
    result = await _service.validate_policy(request.content, request.language)
    return result


@router.post("/test")
async def test_policy(request: TestPolicyRequest):
    """Test a policy against scenarios to verify behavior.

    Runs validation first, then executes test scenarios. If no scenarios
    are provided, runs default compliance test cases.
    """
    result = await _service.test_policy(
        content=request.content,
        language=request.language,
        test_scenarios=request.test_scenarios,
    )
    return result


@router.get("/search")
async def search_packs(
    q: str = Query(..., description="Search query"),
    regulation: str | None = None,
    pricing: str | None = None,
):
    """Search policy packs by text query."""
    filters = {}
    if regulation:
        filters["regulation"] = regulation
    if pricing:
        filters["pricing"] = pricing
    packs = await _service.search_packs(q, filters=filters or None)
    return {
        "packs": [_pack_to_dict(p) for p in packs],
        "total": len(packs),
        "query": q,
    }
