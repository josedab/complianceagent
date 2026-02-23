"""Mobile Backend Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mobile_backend.models import (
    DevicePlatform,
    DeviceRegistration,
    MobileDashboard,
    MobileStats,
    NotificationType,
    PushNotification,
    PushPriority,
)


logger = structlog.get_logger()


class MobileBackendService:
    """Service for managing mobile app backend operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._devices: dict[UUID, DeviceRegistration] = {}
        self._notifications: dict[UUID, PushNotification] = {}

    async def register_device(
        self,
        user_id: str,
        platform: DevicePlatform,
        device_token: str,
    ) -> DeviceRegistration:
        """Register a mobile device for push notifications."""
        log = logger.bind(user_id=user_id, platform=platform.value)
        log.info("device.register.start")

        device = DeviceRegistration(
            id=uuid4(),
            user_id=user_id,
            platform=platform,
            device_token=device_token,
            push_enabled=True,
            registered_at=datetime.now(UTC),
        )

        self._devices[device.id] = device
        log.info("device.registered", device_id=str(device.id))
        return device

    async def unregister_device(self, device_id: UUID) -> None:
        """Unregister a mobile device."""
        log = logger.bind(device_id=str(device_id))

        if device_id not in self._devices:
            log.warning("device.unregister.not_found")
            raise ValueError(f"Device {device_id} not found")

        del self._devices[device_id]
        log.info("device.unregistered")

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        priority: PushPriority = PushPriority.NORMAL,
        data: dict | None = None,
    ) -> PushNotification:
        """Send a push notification to a user."""
        log = logger.bind(
            user_id=user_id,
            notification_type=notification_type.value,
            priority=priority.value,
        )
        log.info("notification.send.start")

        notification = PushNotification(
            id=uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            priority=priority,
            data=data or {},
            sent=True,
            sent_at=datetime.now(UTC),
        )

        self._notifications[notification.id] = notification
        log.info("notification.sent", notification_id=str(notification.id))
        return notification

    async def get_dashboard(self, user_id: str) -> MobileDashboard:
        """Get the mobile dashboard data for a user."""
        logger.info("dashboard.get", user_id=user_id)

        return MobileDashboard(
            user_id=user_id,
            overall_score=82.5,
            score_trend="improving",
            active_incidents=3,
            pending_approvals=2,
            recent_badges=[
                "GDPR Champion",
                "First Scan Complete",
                "Zero Violations Week",
            ],
            top_violations=[
                {
                    "id": "v1",
                    "rule": "Data retention exceeded",
                    "severity": "high",
                    "count": 5,
                },
                {
                    "id": "v2",
                    "rule": "Missing encryption at rest",
                    "severity": "medium",
                    "count": 3,
                },
                {
                    "id": "v3",
                    "rule": "Consent record not found",
                    "severity": "high",
                    "count": 2,
                },
            ],
        )

    async def list_notifications(
        self, user_id: str, limit: int = 20
    ) -> list[PushNotification]:
        """List notifications for a user."""
        user_notifications = [
            n for n in self._notifications.values() if n.user_id == user_id
        ]
        user_notifications.sort(
            key=lambda n: n.sent_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )
        return user_notifications[:limit]

    async def list_devices(self, user_id: str) -> list[DeviceRegistration]:
        """List registered devices for a user."""
        return [d for d in self._devices.values() if d.user_id == user_id]

    async def get_stats(self) -> MobileStats:
        """Get aggregate mobile backend statistics."""
        devices = list(self._devices.values())
        by_platform: dict[str, int] = {}
        push_enabled = 0

        for device in devices:
            by_platform[device.platform.value] = (
                by_platform.get(device.platform.value, 0) + 1
            )
            if device.push_enabled:
                push_enabled += 1

        unique_users = {d.user_id for d in devices}

        return MobileStats(
            registered_devices=len(devices),
            by_platform=by_platform,
            notifications_sent=len(self._notifications),
            push_enabled=push_enabled,
            active_users_24h=len(unique_users),
        )
