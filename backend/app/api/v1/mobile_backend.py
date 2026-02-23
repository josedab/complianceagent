"""API endpoints for Mobile Backend."""


import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.mobile_backend import MobileBackendService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class RegisterDeviceRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    platform: str = Field(..., description="Device platform (ios, android)")
    device_token: str = Field(..., description="Push notification device token")


class SendNotificationRequest(BaseModel):
    user_id: str = Field(..., description="Target user identifier")
    notification_type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    priority: str = Field(default="normal", description="Priority level (low, normal, high)")


class DeviceSchema(BaseModel):
    id: str
    user_id: str
    platform: str
    device_token: str
    active: bool
    registered_at: str | None


class NotificationSchema(BaseModel):
    id: str
    user_id: str
    notification_type: str
    title: str
    body: str
    priority: str
    read: bool
    sent_at: str | None


class DashboardSchema(BaseModel):
    user_id: str
    compliance_score: float
    pending_alerts: int
    recent_findings: int
    active_scans: int
    notifications_unread: int


class MobileStatsSchema(BaseModel):
    total_devices: int
    total_notifications: int
    active_users: int
    notifications_by_type: dict[str, int]


# --- Endpoints ---


@router.post("/devices", response_model=DeviceSchema, status_code=status.HTTP_201_CREATED, summary="Register device")
async def register_device(request: RegisterDeviceRequest, db: DB) -> DeviceSchema:
    service = MobileBackendService(db=db)
    device = await service.register_device(
        user_id=request.user_id,
        platform=request.platform,
        device_token=request.device_token,
    )
    logger.info("device_registered", user_id=request.user_id, platform=request.platform)
    return DeviceSchema(
        id=str(device.id), user_id=device.user_id, platform=device.platform,
        device_token=device.device_token, active=device.active,
        registered_at=device.registered_at.isoformat() if device.registered_at else None,
    )


@router.delete("/devices/{device_id}", summary="Unregister device")
async def unregister_device(device_id: str, db: DB) -> dict:
    service = MobileBackendService(db=db)
    ok = await service.unregister_device(device_id=device_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    logger.info("device_unregistered", device_id=device_id)
    return {"status": "unregistered", "device_id": device_id}


@router.post("/notifications", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED, summary="Send notification")
async def send_notification(request: SendNotificationRequest, db: DB) -> NotificationSchema:
    service = MobileBackendService(db=db)
    notification = await service.send_notification(
        user_id=request.user_id,
        notification_type=request.notification_type,
        title=request.title,
        body=request.body,
        priority=request.priority,
    )
    logger.info("notification_sent", user_id=request.user_id, notification_type=request.notification_type)
    return NotificationSchema(
        id=str(notification.id), user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title, body=notification.body,
        priority=notification.priority, read=notification.read,
        sent_at=notification.sent_at.isoformat() if notification.sent_at else None,
    )


@router.get("/dashboard/{user_id}", response_model=DashboardSchema, summary="Get user dashboard")
async def get_dashboard(user_id: str, db: DB) -> DashboardSchema:
    service = MobileBackendService(db=db)
    dashboard = await service.get_dashboard(user_id=user_id)
    if not dashboard:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return DashboardSchema(
        user_id=dashboard.user_id,
        compliance_score=dashboard.compliance_score,
        pending_alerts=dashboard.pending_alerts,
        recent_findings=dashboard.recent_findings,
        active_scans=dashboard.active_scans,
        notifications_unread=dashboard.notifications_unread,
    )


@router.get("/notifications/{user_id}", response_model=list[NotificationSchema], summary="List user notifications")
async def list_notifications(user_id: str, db: DB) -> list[NotificationSchema]:
    service = MobileBackendService(db=db)
    notifications = await service.list_notifications(user_id=user_id)
    return [
        NotificationSchema(
            id=str(n.id), user_id=n.user_id, notification_type=n.notification_type,
            title=n.title, body=n.body, priority=n.priority, read=n.read,
            sent_at=n.sent_at.isoformat() if n.sent_at else None,
        )
        for n in notifications
    ]


@router.get("/stats", response_model=MobileStatsSchema, summary="Get mobile stats")
async def get_stats(db: DB) -> MobileStatsSchema:
    service = MobileBackendService(db=db)
    s = await service.get_stats()
    return MobileStatsSchema(
        total_devices=s.total_devices,
        total_notifications=s.total_notifications,
        active_users=s.active_users,
        notifications_by_type=s.notifications_by_type,
    )
