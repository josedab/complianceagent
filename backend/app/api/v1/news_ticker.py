"""API endpoints for Regulatory News Ticker with Slack/Teams Alerts."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.news_ticker import (
    NewsTickerService,
    SlackWebhookConfig,
    TeamsWebhookConfig,
)


logger = structlog.get_logger()
router = APIRouter()


# ── Request / Response Schemas ──────────────────────────────────────

class NewsItemSchema(BaseModel):
    id: str = Field(..., description="Unique news item identifier")
    title: str = Field(..., description="Headline of the regulatory news")
    summary: str = Field(..., description="Brief summary")
    category: str = Field(..., description="News category")
    severity: str = Field(..., description="Severity level")
    source_url: str = Field(..., description="Link to source")
    source_name: str = Field(..., description="Source name")
    jurisdictions: list[str] = Field(default_factory=list, description="Affected jurisdictions")
    affected_regulations: list[str] = Field(default_factory=list, description="Affected regulations")
    affected_industries: list[str] = Field(default_factory=list, description="Affected industries")
    published_at: str | None = Field(None, description="ISO 8601 publication timestamp")
    relevance_score: float = Field(..., description="Relevance score 0-1")
    impact_summary: str = Field("", description="Impact analysis")
    action_required: bool = Field(False, description="Whether action is required")
    tags: list[str] = Field(default_factory=list, description="Tags")


class NewsFeedSchema(BaseModel):
    items: list[NewsItemSchema] = Field(default_factory=list, description="News items")
    total: int = Field(0, description="Total matching items")
    unread_count: int = Field(0, description="Unread items")
    filters_applied: dict = Field(default_factory=dict, description="Active filters")


class NotificationPreferenceRequest(BaseModel):
    channel: str = Field(default="in_app", description="Notification channel")
    enabled: bool = Field(default=True, description="Enable notifications")
    min_severity: str = Field(default="medium", description="Minimum severity to notify")
    jurisdictions: list[str] = Field(default_factory=list, description="Filter by jurisdictions")
    regulations: list[str] = Field(default_factory=list, description="Filter by regulations")
    industries: list[str] = Field(default_factory=list, description="Filter by industries")
    max_per_day: int = Field(default=20, description="Max notifications per day")
    quiet_hours_start: str | None = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: str | None = Field(None, description="Quiet hours end (HH:MM)")


class NotificationPreferenceSchema(BaseModel):
    id: str = Field(..., description="Preference ID")
    channel: str = Field(..., description="Notification channel")
    enabled: bool = Field(..., description="Enabled status")
    min_severity: str = Field(..., description="Minimum severity")
    jurisdictions: list[str] = Field(default_factory=list, description="Jurisdiction filter")
    regulations: list[str] = Field(default_factory=list, description="Regulation filter")
    industries: list[str] = Field(default_factory=list, description="Industry filter")
    max_per_day: int = Field(..., description="Max daily notifications")
    quiet_hours_start: str | None = Field(None, description="Quiet hours start")
    quiet_hours_end: str | None = Field(None, description="Quiet hours end")


class SlackTestRequest(BaseModel):
    webhook_url: str = Field(..., description="Slack webhook URL")
    channel: str = Field(default="", description="Slack channel")
    bot_name: str = Field(default="ComplianceAgent", description="Bot display name")
    icon_emoji: str = Field(default=":shield:", description="Bot icon emoji")


class TeamsTestRequest(BaseModel):
    webhook_url: str = Field(..., description="Teams webhook URL")
    channel_name: str = Field(default="", description="Teams channel name")


class DigestSchema(BaseModel):
    id: str = Field(..., description="Digest ID")
    period: str = Field(..., description="Digest period")
    item_count: int = Field(..., description="Number of items")
    summary: str = Field(..., description="Digest summary")
    generated_at: str | None = Field(None, description="Generation timestamp")


class DismissRequest(BaseModel):
    feedback: str | None = Field(None, description="Optional dismissal feedback")


class FeedbackRequest(BaseModel):
    relevant: bool = Field(..., description="Whether the item was relevant")


# ── Helpers ─────────────────────────────────────────────────────────

def _item_to_schema(item) -> NewsItemSchema:
    return NewsItemSchema(
        id=str(item.id),
        title=item.title,
        summary=item.summary,
        category=item.category.value,
        severity=item.severity.value,
        source_url=item.source_url,
        source_name=item.source_name,
        jurisdictions=item.jurisdictions,
        affected_regulations=item.affected_regulations,
        affected_industries=item.affected_industries,
        published_at=item.published_at.isoformat() if item.published_at else None,
        relevance_score=item.relevance_score,
        impact_summary=item.impact_summary,
        action_required=item.action_required,
        tags=item.tags,
    )


# Placeholder org/user IDs for demo (matches existing codebase pattern)
_DEMO_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
_DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000002")


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("/feed", response_model=NewsFeedSchema, summary="Get regulatory news feed")
async def get_feed(
    db: DB,
    copilot: CopilotDep,
    severity: str | None = None,
    category: str | None = None,
    jurisdiction: str | None = None,
    regulation: str | None = None,
    industry: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> NewsFeedSchema:
    service = NewsTickerService(db=db, copilot_client=copilot)
    filters: dict = {}
    if severity:
        filters["severity"] = severity
    if category:
        filters["category"] = category
    if jurisdiction:
        filters["jurisdiction"] = jurisdiction
    if regulation:
        filters["regulation"] = regulation
    if industry:
        filters["industry"] = industry
    if search:
        filters["search"] = search

    feed = await service.get_feed(
        org_id=_DEMO_ORG_ID, filters=filters, limit=limit, offset=offset
    )
    return NewsFeedSchema(
        items=[_item_to_schema(i) for i in feed.items],
        total=feed.total,
        unread_count=feed.unread_count,
        filters_applied=feed.filters_applied,
    )


@router.get("/breaking", response_model=list[NewsItemSchema], summary="Get breaking news")
async def get_breaking_news(
    db: DB,
    copilot: CopilotDep,
    since_hours: int = 24,
) -> list[NewsItemSchema]:
    service = NewsTickerService(db=db, copilot_client=copilot)
    items = await service.get_breaking_news(org_id=_DEMO_ORG_ID, since_hours=since_hours)
    return [_item_to_schema(i) for i in items]


@router.get("/item/{item_id}", response_model=NewsItemSchema, summary="Get specific news item")
async def get_news_item(item_id: UUID, db: DB, copilot: CopilotDep) -> NewsItemSchema:
    service = NewsTickerService(db=db, copilot_client=copilot)
    item = await service.get_news_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News item not found")
    return _item_to_schema(item)


@router.get(
    "/preferences",
    response_model=NotificationPreferenceSchema | None,
    summary="Get notification preferences",
)
async def get_preferences(db: DB, copilot: CopilotDep) -> NotificationPreferenceSchema | None:
    service = NewsTickerService(db=db, copilot_client=copilot)
    pref = await service.get_notification_preferences(
        org_id=_DEMO_ORG_ID, user_id=_DEMO_USER_ID
    )
    if not pref:
        return None
    return NotificationPreferenceSchema(
        id=str(pref.id),
        channel=pref.channel.value,
        enabled=pref.enabled,
        min_severity=pref.min_severity.value,
        jurisdictions=pref.jurisdictions,
        regulations=pref.regulations,
        industries=pref.industries,
        max_per_day=pref.max_per_day,
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
    )


@router.put(
    "/preferences",
    response_model=NotificationPreferenceSchema,
    summary="Update notification preferences",
)
async def update_preferences(
    request: NotificationPreferenceRequest, db: DB, copilot: CopilotDep
) -> NotificationPreferenceSchema:
    service = NewsTickerService(db=db, copilot_client=copilot)
    pref = await service.set_notification_preferences(
        org_id=_DEMO_ORG_ID,
        user_id=_DEMO_USER_ID,
        prefs=request.model_dump(exclude_none=True),
    )
    return NotificationPreferenceSchema(
        id=str(pref.id),
        channel=pref.channel.value,
        enabled=pref.enabled,
        min_severity=pref.min_severity.value,
        jurisdictions=pref.jurisdictions,
        regulations=pref.regulations,
        industries=pref.industries,
        max_per_day=pref.max_per_day,
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
    )


@router.post("/slack/test", summary="Test Slack webhook")
async def test_slack_webhook(
    request: SlackTestRequest, db: DB, copilot: CopilotDep
) -> dict:
    service = NewsTickerService(db=db, copilot_client=copilot)
    config = SlackWebhookConfig(
        webhook_url=request.webhook_url,
        channel=request.channel,
        bot_name=request.bot_name,
        icon_emoji=request.icon_emoji,
    )
    # Use the first news item as a test payload
    items = await service.get_breaking_news(org_id=_DEMO_ORG_ID, since_hours=720)
    if not items:
        raise HTTPException(status_code=400, detail="No news items available for test")
    success = await service.send_slack_notification(config, items[0])
    return {"success": success, "message": "Test notification sent to Slack", "test_item": items[0].title}


@router.post("/teams/test", summary="Test Teams webhook")
async def test_teams_webhook(
    request: TeamsTestRequest, db: DB, copilot: CopilotDep
) -> dict:
    service = NewsTickerService(db=db, copilot_client=copilot)
    config = TeamsWebhookConfig(
        webhook_url=request.webhook_url,
        channel_name=request.channel_name,
    )
    items = await service.get_breaking_news(org_id=_DEMO_ORG_ID, since_hours=720)
    if not items:
        raise HTTPException(status_code=400, detail="No news items available for test")
    success = await service.send_teams_notification(config, items[0])
    return {"success": success, "message": "Test notification sent to Teams", "test_item": items[0].title}


@router.get("/digest", response_model=DigestSchema, summary="Get or generate news digest")
async def get_digest(
    db: DB,
    copilot: CopilotDep,
    period: str = "daily",
) -> DigestSchema:
    service = NewsTickerService(db=db, copilot_client=copilot)
    digest = await service.generate_digest(org_id=_DEMO_ORG_ID, period=period)
    return DigestSchema(
        id=str(digest.id),
        period=digest.period,
        item_count=len(digest.items),
        summary=digest.summary,
        generated_at=digest.generated_at.isoformat() if digest.generated_at else None,
    )


@router.post("/item/{item_id}/read", summary="Mark news item as read")
async def mark_as_read(item_id: UUID, db: DB, copilot: CopilotDep) -> dict:
    service = NewsTickerService(db=db, copilot_client=copilot)
    success = await service.mark_as_read(item_id=item_id, user_id=_DEMO_USER_ID)
    return {"success": success, "item_id": str(item_id)}


@router.post("/item/{item_id}/dismiss", summary="Dismiss news item")
async def dismiss_item(
    item_id: UUID, db: DB, copilot: CopilotDep, request: DismissRequest | None = None
) -> dict:
    service = NewsTickerService(db=db, copilot_client=copilot)
    feedback = request.feedback if request else None
    success = await service.dismiss_news(
        item_id=item_id, user_id=_DEMO_USER_ID, feedback=feedback
    )
    return {"success": success, "item_id": str(item_id)}


@router.post("/item/{item_id}/feedback", summary="Submit relevance feedback")
async def submit_feedback(
    item_id: UUID, request: FeedbackRequest, db: DB, copilot: CopilotDep
) -> dict:
    service = NewsTickerService(db=db, copilot_client=copilot)
    await service.submit_relevance_feedback(
        item_id=item_id, user_id=_DEMO_USER_ID, relevant=request.relevant
    )
    return {"success": True, "item_id": str(item_id), "relevant": request.relevant}
