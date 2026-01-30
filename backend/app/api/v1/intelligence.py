"""Regulatory Intelligence Feed API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter(prefix="/intelligence", tags=["Intelligence Feed"])


# ============================================================================
# Request/Response Models
# ============================================================================


class RegulatoryUpdateResponse(BaseModel):
    """A regulatory update."""
    id: str
    source_name: str
    title: str
    summary: str
    url: str
    jurisdiction: str
    framework: str
    update_type: str
    severity: str
    effective_date: datetime | None
    published_date: datetime | None
    detected_at: datetime
    keywords: list[str]


class RelevanceScoreResponse(BaseModel):
    """Relevance score response."""
    update_id: str
    overall_score: float
    jurisdiction_match: float
    regulation_match: float
    keyword_match: float
    urgency_factor: float
    confidence: float
    explanation: str
    matched_criteria: list[str]


class IntelligenceAlertResponse(BaseModel):
    """Alert response."""
    id: str
    title: str
    body: str
    action_required: str
    deadline: datetime | None
    severity: str | None
    relevance_score: float | None
    created_at: datetime
    read_at: datetime | None


class DigestResponse(BaseModel):
    """Digest response."""
    id: str
    period_start: datetime
    period_end: datetime
    total_updates: int
    critical_count: int
    high_count: int
    medium_count: int
    summary: str
    updates: list[RegulatoryUpdateResponse]


class CustomerProfileRequest(BaseModel):
    """Customer profile for relevance scoring."""
    industries: list[str] = Field(default_factory=list)
    jurisdictions: list[str] = Field(default_factory=list)
    applicable_regulations: list[str] = Field(default_factory=list)
    data_types_processed: list[str] = Field(default_factory=list)
    keywords_of_interest: list[str] = Field(default_factory=list)


class NotificationPreferenceRequest(BaseModel):
    """Notification preference request."""
    channel: str  # email, slack, teams, webhook, in_app
    frequency: str = "daily"  # immediate, hourly, daily, weekly
    min_severity: str = "medium"
    min_relevance: float = 0.5
    jurisdictions: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    webhook_url: str | None = None
    slack_channel: str | None = None
    teams_channel: str | None = None


class IngestUpdateRequest(BaseModel):
    """Request to ingest a regulatory update."""
    source: str
    title: str
    summary: str
    content: str = ""
    url: str = ""
    jurisdiction: str
    framework: str
    update_type: str = "new_regulation"
    severity: str = "medium"
    effective_date: str | None = None
    published_date: str | None = None
    keywords: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/updates", response_model=list[RegulatoryUpdateResponse])
async def get_recent_updates(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    hours: int = Query(24, ge=1, le=720),
    jurisdictions: list[str] | None = Query(None),
    frameworks: list[str] | None = Query(None),
    min_severity: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[RegulatoryUpdateResponse]:
    """Get recent regulatory updates.
    
    Retrieves updates from the last N hours with optional filters.
    Updates are sorted by detection time (newest first).
    """
    from app.services.intelligence import IntelligenceFeed, UpdateSeverity
    
    feed = IntelligenceFeed()
    
    severity = None
    if min_severity:
        try:
            severity = UpdateSeverity(min_severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {min_severity}",
            )
    
    updates = await feed.get_recent_updates(
        hours=hours,
        jurisdictions=jurisdictions,
        frameworks=frameworks,
        min_severity=severity,
    )
    
    return [
        RegulatoryUpdateResponse(
            id=str(u.id),
            source_name=u.source_name,
            title=u.title,
            summary=u.summary,
            url=u.url,
            jurisdiction=u.jurisdiction,
            framework=u.framework,
            update_type=u.update_type.value,
            severity=u.severity.value,
            effective_date=u.effective_date,
            published_date=u.published_date,
            detected_at=u.detected_at,
            keywords=u.keywords,
        )
        for u in updates[:limit]
    ]


@router.get("/updates/{update_id}", response_model=RegulatoryUpdateResponse)
async def get_update(
    update_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RegulatoryUpdateResponse:
    """Get a specific regulatory update by ID."""
    from app.services.intelligence import IntelligenceFeed
    
    feed = IntelligenceFeed()
    
    # In production, would query database
    # For now, check cache
    if update_id not in feed._update_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Update {update_id} not found",
        )
    
    u = feed._update_cache[update_id]
    
    return RegulatoryUpdateResponse(
        id=str(u.id),
        source_name=u.source_name,
        title=u.title,
        summary=u.summary,
        url=u.url,
        jurisdiction=u.jurisdiction,
        framework=u.framework,
        update_type=u.update_type.value,
        severity=u.severity.value,
        effective_date=u.effective_date,
        published_date=u.published_date,
        detected_at=u.detected_at,
        keywords=u.keywords,
    )


@router.post("/updates/ingest", response_model=RegulatoryUpdateResponse)
async def ingest_update(
    request: IngestUpdateRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RegulatoryUpdateResponse:
    """Ingest a regulatory update from external source.
    
    Use this endpoint to push updates from crawlers, webhooks,
    or other monitoring systems.
    """
    from app.services.intelligence import IntelligenceFeed
    
    feed = IntelligenceFeed()
    
    update = feed.ingest_update({
        "source": request.source,
        "title": request.title,
        "summary": request.summary,
        "content": request.content,
        "url": request.url,
        "jurisdiction": request.jurisdiction,
        "framework": request.framework,
        "type": request.update_type,
        "severity": request.severity,
        "effective_date": request.effective_date,
        "published_date": request.published_date,
        "keywords": request.keywords,
        "metadata": request.metadata,
    })
    
    return RegulatoryUpdateResponse(
        id=str(update.id),
        source_name=update.source_name,
        title=update.title,
        summary=update.summary,
        url=update.url,
        jurisdiction=update.jurisdiction,
        framework=update.framework,
        update_type=update.update_type.value,
        severity=update.severity.value,
        effective_date=update.effective_date,
        published_date=update.published_date,
        detected_at=update.detected_at,
        keywords=update.keywords,
    )


@router.post("/updates/{update_id}/score", response_model=RelevanceScoreResponse)
async def score_update_relevance(
    update_id: str,
    profile: CustomerProfileRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> RelevanceScoreResponse:
    """Score the relevance of an update for your organization.
    
    Uses ML-powered relevance scoring based on your profile.
    """
    from app.services.intelligence import IntelligenceFeed, RelevanceScorer
    from app.services.intelligence.models import CustomerProfile
    
    feed = IntelligenceFeed()
    scorer = RelevanceScorer()
    
    if update_id not in feed._update_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Update {update_id} not found",
        )
    
    update = feed._update_cache[update_id]
    
    customer_profile = CustomerProfile(
        organization_id=organization.id,
        industries=profile.industries,
        jurisdictions=profile.jurisdictions,
        applicable_regulations=profile.applicable_regulations,
        data_types_processed=profile.data_types_processed,
        keywords_of_interest=profile.keywords_of_interest,
    )
    
    score = scorer.score_update(update, customer_profile)
    
    return RelevanceScoreResponse(
        update_id=str(score.update_id),
        overall_score=score.overall_score,
        jurisdiction_match=score.jurisdiction_match,
        regulation_match=score.regulation_match,
        keyword_match=score.keyword_match,
        urgency_factor=score.urgency_factor,
        confidence=score.confidence,
        explanation=score.explanation,
        matched_criteria=score.matched_criteria,
    )


@router.post("/updates/batch-score")
async def batch_score_updates(
    profile: CustomerProfileRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    hours: int = Query(24, ge=1, le=168),
    min_score: float = Query(0.3, ge=0, le=1),
) -> list[dict[str, Any]]:
    """Score multiple updates and return ranked by relevance."""
    from app.services.intelligence import IntelligenceFeed, RelevanceScorer
    from app.services.intelligence.models import CustomerProfile
    
    feed = IntelligenceFeed()
    scorer = RelevanceScorer()
    
    updates = await feed.get_recent_updates(hours=hours)
    
    customer_profile = CustomerProfile(
        organization_id=organization.id,
        industries=profile.industries,
        jurisdictions=profile.jurisdictions,
        applicable_regulations=profile.applicable_regulations,
        data_types_processed=profile.data_types_processed,
        keywords_of_interest=profile.keywords_of_interest,
    )
    
    scored = scorer.batch_score(updates, customer_profile, min_score)
    
    return [
        {
            "update": {
                "id": str(u.id),
                "title": u.title,
                "framework": u.framework,
                "jurisdiction": u.jurisdiction,
                "severity": u.severity.value,
            },
            "relevance": {
                "score": s.overall_score,
                "explanation": s.explanation,
                "matched_criteria": s.matched_criteria,
            },
        }
        for u, s in scored
    ]


@router.post("/updates/{update_id}/impact")
async def predict_update_impact(
    update_id: str,
    profile: CustomerProfileRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Predict the impact of an update on your organization."""
    from app.services.intelligence import IntelligenceFeed, RelevanceScorer
    from app.services.intelligence.models import CustomerProfile
    
    feed = IntelligenceFeed()
    scorer = RelevanceScorer()
    
    if update_id not in feed._update_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Update {update_id} not found",
        )
    
    update = feed._update_cache[update_id]
    
    customer_profile = CustomerProfile(
        organization_id=organization.id,
        industries=profile.industries,
        jurisdictions=profile.jurisdictions,
        applicable_regulations=profile.applicable_regulations,
        data_types_processed=profile.data_types_processed,
        keywords_of_interest=profile.keywords_of_interest,
    )
    
    return scorer.predict_impact(update, customer_profile)


@router.get("/digest", response_model=DigestResponse)
async def get_intelligence_digest(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    hours: int = Query(24, ge=1, le=168),
) -> DigestResponse:
    """Get a digest of recent regulatory updates."""
    from app.services.intelligence import IntelligenceFeed
    
    feed = IntelligenceFeed()
    updates = await feed.get_recent_updates(hours=hours)
    digest = feed.generate_digest(updates, organization.id)
    
    return DigestResponse(
        id=str(digest.id),
        period_start=digest.period_start,
        period_end=digest.period_end,
        total_updates=digest.total_updates,
        critical_count=digest.critical_count,
        high_count=digest.high_count,
        medium_count=digest.medium_count,
        summary=digest.summary,
        updates=[
            RegulatoryUpdateResponse(
                id=str(u.id),
                source_name=u.source_name,
                title=u.title,
                summary=u.summary,
                url=u.url,
                jurisdiction=u.jurisdiction,
                framework=u.framework,
                update_type=u.update_type.value,
                severity=u.severity.value,
                effective_date=u.effective_date,
                published_date=u.published_date,
                detected_at=u.detected_at,
                keywords=u.keywords,
            )
            for u in digest.updates
        ],
    )


@router.get("/alerts", response_model=list[IntelligenceAlertResponse])
async def get_alerts(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
) -> list[IntelligenceAlertResponse]:
    """Get intelligence alerts for the organization.
    
    Returns alerts sorted by creation time (newest first).
    """
    # In production, would query from database
    return []


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Acknowledge an alert."""
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "acknowledged_by": str(member.user_id),
        "acknowledged_at": datetime.utcnow().isoformat(),
    }


@router.get("/notifications/preferences", response_model=list[NotificationPreferenceRequest])
async def get_notification_preferences(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[dict[str, Any]]:
    """Get notification preferences for the organization."""
    from app.services.intelligence import NotificationService
    
    service = NotificationService()
    prefs = service.get_preferences(organization.id)
    
    return [
        {
            "id": str(p.id),
            "channel": p.channel.value,
            "frequency": p.frequency.value,
            "min_severity": p.min_severity.value,
            "min_relevance": p.min_relevance,
            "jurisdictions": p.jurisdictions,
            "frameworks": p.frameworks,
            "webhook_url": p.webhook_url,
            "slack_channel": p.slack_channel,
            "teams_channel": p.teams_channel,
            "is_active": p.is_active,
        }
        for p in prefs
    ]


@router.post("/notifications/preferences")
async def set_notification_preferences(
    preferences: list[NotificationPreferenceRequest],
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Set notification preferences for the organization."""
    from app.services.intelligence import NotificationService
    from app.services.intelligence.models import (
        NotificationChannel,
        NotificationFrequency,
        NotificationPreference,
        UpdateSeverity,
    )
    
    service = NotificationService()
    
    prefs = [
        NotificationPreference(
            organization_id=organization.id,
            channel=NotificationChannel(p.channel),
            frequency=NotificationFrequency(p.frequency),
            min_severity=UpdateSeverity(p.min_severity),
            min_relevance=p.min_relevance,
            jurisdictions=p.jurisdictions,
            frameworks=p.frameworks,
            webhook_url=p.webhook_url,
            slack_channel=p.slack_channel,
            teams_channel=p.teams_channel,
        )
        for p in preferences
    ]
    
    service.set_preferences(organization.id, prefs)
    
    return {
        "status": "updated",
        "count": len(prefs),
    }


@router.post("/notifications/test")
async def test_notification(
    channel: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    webhook_url: str | None = None,
    slack_channel: str | None = None,
) -> dict[str, Any]:
    """Send a test notification to verify configuration."""
    from app.services.intelligence import NotificationService
    from app.services.intelligence.models import (
        IntelligenceAlert,
        NotificationChannel,
        NotificationPreference,
        NotificationFrequency,
        UpdateSeverity,
    )
    
    service = NotificationService()
    
    test_alert = IntelligenceAlert(
        organization_id=organization.id,
        title="🧪 Test Alert - ComplianceAgent",
        body="This is a test notification from ComplianceAgent Intelligence Feed.\n\nIf you received this, your notification integration is working correctly!",
        action_required="No action required - this is a test",
    )
    
    pref = NotificationPreference(
        organization_id=organization.id,
        channel=NotificationChannel(channel),
        frequency=NotificationFrequency.IMMEDIATE,
        min_severity=UpdateSeverity.INFO,
        webhook_url=webhook_url,
        slack_channel=slack_channel,
    )
    
    async with service:
        result = await service.send_alert(test_alert, [pref])
    
    return {
        "status": "sent" if any(result.values()) else "failed",
        "results": result,
    }


@router.get("/sources")
async def list_regulatory_sources(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[dict[str, Any]]:
    """List available regulatory sources being monitored."""
    from app.services.intelligence import IntelligenceFeed
    
    feed = IntelligenceFeed()
    return feed.get_available_sources()


@router.get("/stream")
async def stream_updates(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> StreamingResponse:
    """Stream regulatory updates in real-time using Server-Sent Events.
    
    Usage with JavaScript:
    ```javascript
    const eventSource = new EventSource('/api/v1/intelligence/stream');
    eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data);
        console.log('New update:', update);
    };
    ```
    """
    import asyncio
    import json
    from uuid import uuid4
    from app.services.intelligence import IntelligenceFeed
    
    feed = IntelligenceFeed()
    
    async def event_generator():
        subscriber_id = uuid4()
        queue = feed.subscribe(subscriber_id)
        
        try:
            # Send initial ping
            yield f"data: {json.dumps({'type': 'connected', 'subscriber_id': str(subscriber_id)})}\n\n"
            
            while True:
                try:
                    # Wait for updates with timeout (for keepalive)
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    data = {
                        "type": "update",
                        "update": {
                            "id": str(update.id),
                            "title": update.title,
                            "framework": update.framework,
                            "jurisdiction": update.jurisdiction,
                            "severity": update.severity.value,
                            "detected_at": update.detected_at.isoformat(),
                        },
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                    
        finally:
            feed.unsubscribe(subscriber_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
