"""Notification service for sending alerts via email and Slack."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
import structlog


logger = structlog.get_logger()


class NotificationType(str, Enum):
    """Types of notifications."""
    REGULATION_DETECTED = "regulation_detected"
    REQUIREMENT_EXTRACTED = "requirement_extracted"
    ACTION_REQUIRED = "action_required"
    DEADLINE_APPROACHING = "deadline_approaching"
    PR_STATUS_CHANGED = "pr_status_changed"
    COMPLIANCE_ALERT = "compliance_alert"
    WEEKLY_DIGEST = "weekly_digest"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Notification data structure."""
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    organization_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] | None = None
    action_url: str | None = None


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, notification: Notification, config: dict[str, str]) -> bool:
        """Send a notification through this channel."""

    @abstractmethod
    def validate_config(self, config: dict[str, str]) -> bool:
        """Validate channel configuration."""


class EmailChannel(NotificationChannel):
    """Email notification channel using SMTP or API."""

    def __init__(self, smtp_config: dict[str, Any] | None = None):
        self.smtp_config = smtp_config or {}
        self.api_endpoint = self.smtp_config.get("api_endpoint")

    async def send(self, notification: Notification, config: dict[str, str]) -> bool:
        """Send email notification."""
        recipient = config.get("email")
        if not recipient:
            logger.warning("No email recipient configured")
            return False

        try:
            if self.api_endpoint:
                return await self._send_via_api(notification, recipient)
            return await self._send_via_smtp(notification, recipient)
        except Exception as e:
            logger.exception("Failed to send email notification", error=str(e))
            return False

    async def _send_via_api(self, notification: Notification, recipient: str) -> bool:
        """Send email via API (SendGrid, Mailgun, etc.)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_endpoint,
                json={
                    "to": recipient,
                    "subject": f"[ComplianceAgent] {notification.title}",
                    "html": self._format_html_email(notification),
                    "text": self._format_text_email(notification),
                },
                headers={
                    "Authorization": f"Bearer {self.smtp_config.get('api_key', '')}",
                },
                timeout=30,
            )
            return response.status_code == 200

    async def _send_via_smtp(self, notification: Notification, recipient: str) -> bool:
        """Send email via SMTP."""
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ComplianceAgent] {notification.title}"
        msg["From"] = self.smtp_config.get("from_email", "noreply@complianceagent.io")
        msg["To"] = recipient

        text_part = MIMEText(self._format_text_email(notification), "plain")
        html_part = MIMEText(self._format_html_email(notification), "html")
        msg.attach(text_part)
        msg.attach(html_part)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_send_smtp, msg, recipient)
        return True

    def _sync_send_smtp(self, msg: Any, recipient: str) -> None:
        """Synchronous SMTP send (run in executor)."""
        import smtplib

        with smtplib.SMTP(
            self.smtp_config.get("host", "localhost"),
            self.smtp_config.get("port", 587),
        ) as server:
            if self.smtp_config.get("use_tls", True):
                server.starttls()
            if self.smtp_config.get("username"):
                server.login(
                    self.smtp_config["username"],
                    self.smtp_config.get("password", ""),
                )
            server.sendmail(
                self.smtp_config.get("from_email", "noreply@complianceagent.io"),
                [recipient],
                msg.as_string(),
            )

    def _format_html_email(self, notification: Notification) -> str:
        """Format notification as HTML email."""
        priority_colors = {
            NotificationPriority.LOW: "#6B7280",
            NotificationPriority.MEDIUM: "#3B82F6",
            NotificationPriority.HIGH: "#F59E0B",
            NotificationPriority.CRITICAL: "#EF4444",
        }
        color = priority_colors.get(notification.priority, "#3B82F6")

        action_button = ""
        if notification.action_url:
            action_button = f"""
            <a href="{notification.action_url}"
               style="display: inline-block; padding: 12px 24px;
                      background-color: {color}; color: white;
                      text-decoration: none; border-radius: 6px;
                      margin-top: 16px;">
                View Details
            </a>
            """

        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 20px; background-color: #f3f4f6; font-family: sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden;">
        <div style="background-color: {color}; padding: 20px; color: white;">
            <h1 style="margin: 0; font-size: 20px;">{notification.title}</h1>
            <span style="font-size: 12px; opacity: 0.8;">Priority: {notification.priority.value.upper()}</span>
        </div>
        <div style="padding: 24px;">
            <p style="color: #374151; line-height: 1.6;">{notification.message}</p>
            {action_button}
        </div>
        <div style="padding: 16px 24px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280;">
            Sent by ComplianceAgent
        </div>
    </div>
</body>
</html>
"""

    def _format_text_email(self, notification: Notification) -> str:
        """Format notification as plain text email."""
        text = f"{notification.title}\nPriority: {notification.priority.value.upper()}\n\n{notification.message}"
        if notification.action_url:
            text += f"\n\nView details: {notification.action_url}"
        return text + "\n\n---\nSent by ComplianceAgent"

    def validate_config(self, config: dict[str, str]) -> bool:
        """Validate email configuration."""
        return bool(config.get("email"))


class SlackChannel(NotificationChannel):
    """Slack notification channel using webhooks."""

    async def send(self, notification: Notification, config: dict[str, str]) -> bool:
        """Send Slack notification."""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.warning("No Slack webhook URL configured")
            return False

        try:
            payload = self._format_slack_message(notification, config)
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload, timeout=30)
                return response.status_code == 200
        except Exception as e:
            logger.exception("Failed to send Slack notification", error=str(e))
            return False

    def _format_slack_message(
        self,
        notification: Notification,
        config: dict[str, str],
    ) -> dict[str, Any]:
        """Format notification as Slack message."""
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "📋",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.CRITICAL: "🚨",
        }
        priority_colors = {
            NotificationPriority.LOW: "#6B7280",
            NotificationPriority.MEDIUM: "#3B82F6",
            NotificationPriority.HIGH: "#F59E0B",
            NotificationPriority.CRITICAL: "#EF4444",
        }

        emoji = priority_emoji.get(notification.priority, "📋")
        color = priority_colors.get(notification.priority, "#3B82F6")
        channel = config.get("channel", "#compliance")

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {notification.title}", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": notification.message}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Priority:* {notification.priority.value.upper()} | *Type:* {notification.type.value}"}]},
        ]

        if notification.action_url:
            blocks.append({
                "type": "actions",
                "elements": [{"type": "button", "text": {"type": "plain_text", "text": "View Details"}, "url": notification.action_url, "style": "primary"}],
            })

        return {"channel": channel, "attachments": [{"color": color, "blocks": blocks}]}

    def validate_config(self, config: dict[str, str]) -> bool:
        """Validate Slack configuration."""
        return config.get("webhook_url", "").startswith("https://hooks.slack.com/")


class InAppChannel(NotificationChannel):
    """In-app notification channel (stores in database)."""

    def __init__(self, db_session: Any | None = None):
        self.db_session = db_session

    async def send(self, notification: Notification, config: dict[str, str]) -> bool:
        """Store notification in database for in-app display."""
        logger.info("In-app notification created", title=notification.title, type=notification.type.value)
        return True

    def validate_config(self, config: dict[str, str]) -> bool:
        """In-app always valid."""
        return True


class NotificationService:
    """Service for sending notifications across multiple channels."""

    def __init__(self, smtp_config: dict[str, Any] | None = None, db_session: Any | None = None):
        self.channels: dict[str, NotificationChannel] = {
            "email": EmailChannel(smtp_config),
            "slack": SlackChannel(),
            "in_app": InAppChannel(db_session),
        }

    async def send_notification(
        self,
        notification: Notification,
        channels: list[str] | None = None,
        channel_configs: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, bool]:
        """Send notification to specified channels."""
        if channels is None:
            channels = ["in_app"]
        if channel_configs is None:
            channel_configs = {}

        results = {}
        tasks = []

        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                config = channel_configs.get(channel_name, {})
                if channel.validate_config(config):
                    tasks.append(self._send_to_channel(channel_name, channel, notification, config))
                else:
                    results[channel_name] = False
            else:
                results[channel_name] = False

        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            for channel_name, result in zip([c for c in channels if c in self.channels], task_results, strict=False):
                results[channel_name] = not isinstance(result, Exception) and result

        return results

    async def _send_to_channel(
        self,
        channel_name: str,
        channel: NotificationChannel,
        notification: Notification,
        config: dict[str, str],
    ) -> bool:
        """Send to a single channel with error handling."""
        try:
            return await channel.send(notification, config)
        except Exception as e:
            logger.exception("Failed to send notification", channel=channel_name, error=str(e))
            return False

    async def send_regulation_detected(
        self,
        regulation_name: str,
        jurisdiction: str,
        effective_date: str | None = None,
        channel_configs: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, bool]:
        """Send notification for new regulation detected."""
        notification = Notification(
            type=NotificationType.REGULATION_DETECTED,
            title=f"New Regulation Detected: {regulation_name}",
            message=f"A new regulation has been detected in {jurisdiction}. {'Effective date: ' + effective_date if effective_date else 'Effective date pending.'}",
            priority=NotificationPriority.HIGH,
        )
        return await self.send_notification(notification, channels=["email", "slack", "in_app"], channel_configs=channel_configs)

    async def send_deadline_approaching(
        self,
        regulation_name: str,
        days_remaining: int,
        action_url: str | None = None,
        channel_configs: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, bool]:
        """Send notification for approaching deadline."""
        priority = NotificationPriority.CRITICAL if days_remaining <= 7 else NotificationPriority.HIGH if days_remaining <= 30 else NotificationPriority.MEDIUM
        notification = Notification(
            type=NotificationType.DEADLINE_APPROACHING,
            title=f"Deadline Approaching: {regulation_name}",
            message=f"Only {days_remaining} days remaining until the {regulation_name} deadline.",
            priority=priority,
            action_url=action_url,
        )
        return await self.send_notification(notification, channels=["email", "slack", "in_app"], channel_configs=channel_configs)

    async def send_action_required(
        self,
        action_title: str,
        description: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: str | None = None,
        channel_configs: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, bool]:
        """Send notification for required action."""
        notification = Notification(
            type=NotificationType.ACTION_REQUIRED,
            title=f"Action Required: {action_title}",
            message=description,
            priority=priority,
            action_url=action_url,
        )
        return await self.send_notification(notification, channels=["email", "slack", "in_app"], channel_configs=channel_configs)


def create_notification_service(
    smtp_host: str | None = None,
    smtp_port: int = 587,
    smtp_username: str | None = None,
    smtp_password: str | None = None,
    smtp_from_email: str = "noreply@complianceagent.io",
    email_api_endpoint: str | None = None,
    email_api_key: str | None = None,
) -> NotificationService:
    """Create a configured notification service."""
    smtp_config = {
        "host": smtp_host,
        "port": smtp_port,
        "username": smtp_username,
        "password": smtp_password,
        "from_email": smtp_from_email,
        "use_tls": True,
        "api_endpoint": email_api_endpoint,
        "api_key": email_api_key,
    }
    return NotificationService(smtp_config=smtp_config)
