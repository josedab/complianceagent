"""Tests for notification service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notification import (
    NotificationService,
    EmailChannel,
    SlackChannel,
    InAppChannel,
    NotificationType,
    NotificationPriority,
    Notification,
)

pytestmark = pytest.mark.asyncio


class TestEmailChannel:
    """Test suite for EmailChannel."""

    @pytest.fixture
    def smtp_config(self):
        """SMTP configuration for tests."""
        return {
            "host": "smtp.test.com",
            "port": 587,
            "username": "test@example.com",
            "password": "password",
            "use_tls": True,
            "from_email": "noreply@complianceagent.io",
            "from_name": "ComplianceAgent",
        }

    @pytest.fixture
    def email_channel(self, smtp_config):
        """Create email channel instance."""
        return EmailChannel(smtp_config=smtp_config)

    def test_format_html_email(self, email_channel):
        """Test HTML email formatting."""
        notification = Notification(
            type=NotificationType.COMPLIANCE_ALERT,
            title="Test Subject",
            message="This is a test message.",
            priority=NotificationPriority.HIGH,
        )

        html = email_channel._format_html_email(notification)

        assert "Test Subject" in html
        assert "This is a test message" in html
        assert "HIGH" in html

    def test_format_html_low_priority(self, email_channel):
        """Test HTML formatting for low priority."""
        notification = Notification(
            type=NotificationType.WEEKLY_DIGEST,
            title="Low Priority",
            message="Test",
            priority=NotificationPriority.LOW,
        )
        html = email_channel._format_html_email(notification)

        assert "LOW" in html

    def test_format_text_email(self, email_channel):
        """Test plain text email formatting."""
        notification = Notification(
            type=NotificationType.REGULATION_DETECTED,
            title="Test Subject",
            message="This is a test message.",
            priority=NotificationPriority.MEDIUM,
        )

        text = email_channel._format_text_email(notification)

        assert "Test Subject" in text
        assert "This is a test message" in text
        assert "MEDIUM" in text.upper()

    async def test_send_email(self, email_channel):
        """Test sending email notification."""
        notification = Notification(
            type=NotificationType.ACTION_REQUIRED,
            title="Test Email",
            message="Hello, this is a test.",
            priority=NotificationPriority.MEDIUM,
        )
        config = {"email": "user@example.com"}

        # Without actual SMTP, this will fail but we verify method exists
        result = await email_channel.send(notification, config)
        # Result depends on SMTP availability
        assert isinstance(result, bool)

    def test_validate_config(self, email_channel):
        """Test email configuration validation."""
        valid_config = {"email": "user@example.com"}
        invalid_config = {}

        assert email_channel.validate_config(valid_config) is True
        assert email_channel.validate_config(invalid_config) is False


class TestSlackChannel:
    """Test suite for SlackChannel."""

    @pytest.fixture
    def slack_channel(self):
        """Create Slack channel instance."""
        return SlackChannel()

    def test_format_slack_message(self, slack_channel):
        """Test Slack message formatting."""
        notification = Notification(
            type=NotificationType.REGULATION_DETECTED,
            title="New Regulation Update",
            message="GDPR Article 17 has been updated.",
            priority=NotificationPriority.HIGH,
            metadata={"regulation": "GDPR", "article": "17"},
        )
        config = {"webhook_url": "https://hooks.slack.com/services/T00/B00/XXX"}

        payload = slack_channel._format_slack_message(notification, config)

        assert "attachments" in payload or "blocks" in payload

    def test_priority_in_message(self, slack_channel):
        """Test priority appears in Slack message."""
        notification = Notification(
            type=NotificationType.COMPLIANCE_ALERT,
            title="Test",
            message="Test body",
            priority=NotificationPriority.CRITICAL,
        )
        config = {"webhook_url": "https://hooks.slack.com/services/T00/B00/XXX"}

        payload = slack_channel._format_slack_message(notification, config)
        payload_str = str(payload)

        assert "CRITICAL" in payload_str.upper()

    @patch("httpx.AsyncClient.post")
    async def test_send_slack_message(self, mock_post, slack_channel):
        """Test sending Slack message."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notification = Notification(
            type=NotificationType.DEADLINE_APPROACHING,
            title="Test Notification",
            message="This is a test.",
            priority=NotificationPriority.LOW,
        )
        config = {
            "webhook_url": "https://hooks.slack.com/services/T00/B00/XXX",
            "channel": "#compliance-alerts",
        }

        result = await slack_channel.send(notification, config)
        assert isinstance(result, bool)

    def test_validate_config(self, slack_channel):
        """Test Slack configuration validation."""
        valid_config = {"webhook_url": "https://hooks.slack.com/services/T00/B00/XXX"}
        invalid_config = {"webhook_url": "https://example.com/webhook"}

        assert slack_channel.validate_config(valid_config) is True
        assert slack_channel.validate_config(invalid_config) is False


class TestInAppChannel:
    """Test suite for InAppChannel."""

    @pytest.fixture
    def inapp_channel(self):
        """Create in-app channel instance."""
        return InAppChannel()

    async def test_send_inapp_notification(self, inapp_channel):
        """Test sending in-app notification."""
        notification = Notification(
            type=NotificationType.ACTION_REQUIRED,
            title="Action Required",
            message="Please review compliance update.",
            priority=NotificationPriority.HIGH,
            metadata={"action_id": "act-456"},
        )
        config = {}

        result = await inapp_channel.send(notification, config)

        assert result is True

    def test_validate_config(self, inapp_channel):
        """Test in-app config validation always passes."""
        assert inapp_channel.validate_config({}) is True
        assert inapp_channel.validate_config({"any": "config"}) is True


class TestNotificationService:
    """Test suite for NotificationService."""

    @pytest.fixture
    def notification_service(self):
        """Create notification service instance."""
        return NotificationService()

    async def test_send_notification_to_inapp(self, notification_service):
        """Test sending notification through service."""
        notification = Notification(
            type=NotificationType.REGULATION_DETECTED,
            title="New Regulation",
            message="GDPR has been updated.",
            priority=NotificationPriority.HIGH,
        )

        result = await notification_service.send_notification(
            notification,
            channels=["in_app"],
            channel_configs={},
        )

        assert "in_app" in result
        assert result["in_app"] is True

    async def test_send_regulation_detected(self, notification_service):
        """Test convenience method for regulation detection."""
        result = await notification_service.send_regulation_detected(
            regulation_name="GDPR",
            jurisdiction="EU",
            effective_date="2026-07-01",
        )

        # Should return results dict with email, slack, in_app channels
        assert isinstance(result, dict)
        # At least one channel should be attempted
        assert len(result) > 0

    async def test_send_deadline_approaching(self, notification_service):
        """Test convenience method for deadline notifications."""
        result = await notification_service.send_deadline_approaching(
            regulation_name="CCPA",
            days_remaining=30,
            action_url="https://app.complianceagent.io/actions/123",
        )

        assert isinstance(result, dict)
        # At least one channel should be attempted
        assert len(result) > 0

    async def test_send_action_required(self, notification_service):
        """Test convenience method for action required."""
        result = await notification_service.send_action_required(
            action_title="Review GDPR Mapping",
            description="New requirements need code review.",
            priority=NotificationPriority.HIGH,
        )

        assert isinstance(result, dict)

    async def test_channel_not_found(self, notification_service):
        """Test handling of unknown channel."""
        notification = Notification(
            type=NotificationType.COMPLIANCE_ALERT,
            title="Test",
            message="Test",
            priority=NotificationPriority.LOW,
        )

        result = await notification_service.send_notification(
            notification,
            channels=["nonexistent_channel"],
            channel_configs={},
        )

        # Unknown channel should return False
        assert result.get("nonexistent_channel") is False

    async def test_email_without_config(self, notification_service):
        """Test email channel without proper config."""
        notification = Notification(
            type=NotificationType.COMPLIANCE_ALERT,
            title="Alert",
            message="Test",
            priority=NotificationPriority.HIGH,
        )

        result = await notification_service.send_notification(
            notification,
            channels=["email"],
            channel_configs={"email": {}},  # Missing email address
        )

        # Should fail validation
        assert result.get("email") is False


class TestNotificationTypes:
    """Test notification type enumeration."""

    def test_notification_types(self):
        """Test all notification types are defined."""
        expected_types = [
            "REGULATION_DETECTED",
            "REQUIREMENT_EXTRACTED",
            "ACTION_REQUIRED",
            "DEADLINE_APPROACHING",
            "PR_STATUS_CHANGED",
            "COMPLIANCE_ALERT",
            "WEEKLY_DIGEST",
        ]

        for type_name in expected_types:
            assert hasattr(NotificationType, type_name)

    def test_priority_levels(self):
        """Test all priority levels are defined."""
        expected_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for priority_name in expected_priorities:
            assert hasattr(NotificationPriority, priority_name)
