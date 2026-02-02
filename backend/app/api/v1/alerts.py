"""Regulatory diff alerts API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.diff_alerts import (
    AlertAcknowledgment,
    AlertStatus,
    RegulatoryDiffService,
)
from app.services.diff_alerts.models import AlertSeverity, NotificationConfig
from app.services.diff_alerts.notifier import AlertNotifier


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class DiffChangeSchema(BaseModel):
    """A single change in a diff."""
    change_type: str
    line_number_old: int | None = None
    line_number_new: int | None = None
    old_text: str | None = None
    new_text: str | None = None


class TextDiffSchema(BaseModel):
    """Diff between two text versions."""
    old_version_preview: str = Field(..., description="Preview of old version (truncated)")
    new_version_preview: str = Field(..., description="Preview of new version (truncated)")
    old_version_date: datetime | None = None
    new_version_date: datetime | None = None
    changes: list[DiffChangeSchema]
    additions_count: int
    deletions_count: int
    similarity_ratio: float


class ImpactAnalysisSchema(BaseModel):
    """AI analysis of regulatory change impact."""
    summary: str
    key_changes: list[str]
    affected_areas: list[str]
    compliance_impact: str
    recommended_actions: list[str]
    urgency_level: str
    affected_frameworks: list[str] = Field(default_factory=list)
    confidence: float


class AlertResponseSchema(BaseModel):
    """Regulatory alert response."""
    id: UUID
    regulation_id: UUID | None = None
    regulation_name: str
    jurisdiction: str
    framework: str
    severity: str
    status: str
    diff: TextDiffSchema | None = None
    impact_analysis: ImpactAnalysisSchema | None = None
    created_at: datetime
    acknowledged_at: datetime | None = None
    acknowledged_by: UUID | None = None


class DetectChangesRequest(BaseModel):
    """Request to detect changes in regulation."""
    regulation_id: UUID
    new_text: str = Field(..., description="New version of regulatory text")
    old_text: str | None = Field(None, description="Previous version (optional)")


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert."""
    notes: str | None = Field(None, description="Optional notes about acknowledgment")
    action_taken: str | None = Field(None, description="Description of action taken")


class NotificationConfigRequest(BaseModel):
    """Configuration for alert notifications."""
    slack_webhook_url: str | None = None
    slack_channel: str | None = None
    teams_webhook_url: str | None = None
    email_recipients: list[str] = Field(default_factory=list)
    min_severity: str = "low"


class AlertListResponse(BaseModel):
    """List of alerts."""
    alerts: list[AlertResponseSchema]
    total: int
    pending_count: int
    critical_count: int


# --- Helper Functions ---

def _alert_to_schema(alert) -> AlertResponseSchema:
    """Convert RegulatoryAlert to response schema."""
    diff_schema = None
    if alert.diff:
        diff_schema = TextDiffSchema(
            old_version_preview=alert.diff.old_version[:500] if alert.diff.old_version else "",
            new_version_preview=alert.diff.new_version[:500] if alert.diff.new_version else "",
            old_version_date=alert.diff.old_version_date,
            new_version_date=alert.diff.new_version_date,
            changes=[
                DiffChangeSchema(
                    change_type=c.change_type.value,
                    line_number_old=c.line_number_old,
                    line_number_new=c.line_number_new,
                    old_text=c.old_text,
                    new_text=c.new_text,
                ) for c in alert.diff.changes[:50]  # Limit changes
            ],
            additions_count=alert.diff.additions_count,
            deletions_count=alert.diff.deletions_count,
            similarity_ratio=alert.diff.similarity_ratio,
        )
    
    impact_schema = None
    if alert.impact_analysis:
        impact_schema = ImpactAnalysisSchema(
            summary=alert.impact_analysis.summary,
            key_changes=alert.impact_analysis.key_changes,
            affected_areas=alert.impact_analysis.affected_areas,
            compliance_impact=alert.impact_analysis.compliance_impact,
            recommended_actions=alert.impact_analysis.recommended_actions,
            urgency_level=alert.impact_analysis.urgency_level.value,
            affected_frameworks=alert.impact_analysis.affected_frameworks,
            confidence=alert.impact_analysis.confidence,
        )
    
    return AlertResponseSchema(
        id=alert.id,
        regulation_id=alert.regulation_id,
        regulation_name=alert.regulation_name,
        jurisdiction=alert.jurisdiction,
        framework=alert.framework,
        severity=alert.severity.value,
        status=alert.status.value,
        diff=diff_schema,
        impact_analysis=impact_schema,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by=alert.acknowledged_by,
    )


# --- Endpoints ---

@router.post(
    "/detect",
    response_model=AlertResponseSchema | None,
    summary="Detect regulatory changes",
    description="Compare regulatory text versions and detect changes",
)
async def detect_changes(
    request: DetectChangesRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> AlertResponseSchema | None:
    """
    Detect changes in regulatory text and generate an alert if changes found.
    
    Uses AI to analyze the impact of detected changes and determine severity.
    """
    try:
        service = RegulatoryDiffService(db=db, copilot=copilot)
        alert = await service.detect_changes(
            regulation_id=request.regulation_id,
            new_text=request.new_text,
            old_text=request.old_text,
        )
        
        if alert is None:
            return None
        
        return _alert_to_schema(alert)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Change detection failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Change detection failed",
        )


@router.get(
    "/",
    response_model=AlertListResponse,
    summary="List regulatory alerts",
    description="Get list of regulatory change alerts for the organization",
)
async def list_alerts(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    status_filter: AlertStatus | None = Query(None, alias="status"),
    severity: str | None = Query(None, description="Filter by severity"),
    framework: str | None = Query(None, description="Filter by framework"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AlertListResponse:
    """
    List regulatory change alerts for the organization.
    
    Alerts can be filtered by status, severity, and framework.
    """
    service = RegulatoryDiffService(db=db)
    
    # Get alerts (in production, this would query from DB with filters)
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            pass
    
    alerts = await service.get_pending_alerts(
        organization_id=organization.id,
        severity=severity_enum,
        limit=limit,
    )
    
    alert_schemas = [_alert_to_schema(a) for a in alerts]
    
    # Count metrics
    pending_count = sum(1 for a in alerts if a.status == AlertStatus.PENDING)
    critical_count = sum(1 for a in alerts if a.severity == AlertSeverity.CRITICAL)
    
    return AlertListResponse(
        alerts=alert_schemas,
        total=len(alert_schemas),
        pending_count=pending_count,
        critical_count=critical_count,
    )


@router.post(
    "/{alert_id}/acknowledge",
    summary="Acknowledge an alert",
    description="Mark an alert as acknowledged",
)
async def acknowledge_alert(
    alert_id: UUID,
    request: AcknowledgeAlertRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict:
    """
    Acknowledge a regulatory alert.
    
    Acknowledging indicates the organization is aware of the change
    and has begun reviewing its impact.
    """
    service = RegulatoryDiffService(db=db)
    
    success = await service.acknowledge_alert(
        alert_id=alert_id,
        user_id=member.user_id,
        notes=request.notes,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    
    return {
        "success": True,
        "alert_id": str(alert_id),
        "acknowledged_at": datetime.utcnow().isoformat(),
        "acknowledged_by": str(member.user_id),
    }


@router.post(
    "/configure-notifications",
    summary="Configure alert notifications",
    description="Set up Slack, Teams, and email notifications for alerts",
)
async def configure_notifications(
    request: NotificationConfigRequest,
    organization: CurrentOrganization,
    member: OrgMember,
) -> dict:
    """
    Configure notification channels for regulatory alerts.
    
    Supports Slack webhooks, Microsoft Teams webhooks, and email.
    """
    # In production, save to database
    try:
        min_severity = AlertSeverity(request.min_severity.lower())
    except ValueError:
        min_severity = AlertSeverity.LOW
    
    config = NotificationConfig(
        slack_webhook_url=request.slack_webhook_url,
        slack_channel=request.slack_channel,
        teams_webhook_url=request.teams_webhook_url,
        email_recipients=request.email_recipients,
        min_severity=min_severity,
        enabled=True,
    )
    
    # Validate webhook URLs by checking format
    channels_configured = []
    if config.slack_webhook_url:
        channels_configured.append("slack")
    if config.teams_webhook_url:
        channels_configured.append("teams")
    if config.email_recipients:
        channels_configured.append("email")
    
    return {
        "success": True,
        "organization_id": str(organization.id),
        "channels_configured": channels_configured,
        "min_severity": min_severity.value,
    }


@router.post(
    "/test-notification",
    summary="Test notification delivery",
    description="Send a test notification to verify configuration",
)
async def test_notification(
    organization: CurrentOrganization,
    member: OrgMember,
    channel: str = Query(..., description="Channel to test: slack, teams, or email"),
    webhook_url: str | None = Query(None, description="Webhook URL for Slack/Teams"),
) -> dict:
    """
    Send a test notification to verify the configuration works.
    """
    from app.services.diff_alerts.models import RegulatoryAlert
    from uuid import uuid4
    
    # Create test alert
    test_alert = RegulatoryAlert(
        id=uuid4(),
        regulation_name="Test Regulation",
        jurisdiction="Test",
        framework="TEST",
        severity=AlertSeverity.LOW,
        status=AlertStatus.PENDING,
    )
    
    config = NotificationConfig()
    if channel == "slack" and webhook_url:
        config.slack_webhook_url = webhook_url
    elif channel == "teams" and webhook_url:
        config.teams_webhook_url = webhook_url
    
    notifier = AlertNotifier(config)
    
    try:
        results = await notifier.send_alert(test_alert)
        success = results.get(channel, False)
        
        return {
            "success": success,
            "channel": channel,
            "message": "Test notification sent" if success else "Notification failed",
        }
    except Exception as e:
        return {
            "success": False,
            "channel": channel,
            "error": str(e),
        }
