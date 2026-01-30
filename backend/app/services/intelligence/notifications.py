"""Notification Service - Multi-channel notification delivery."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
import structlog

from app.services.intelligence.models import (
    CustomerProfile,
    IntelligenceAlert,
    IntelligenceDigest,
    NotificationChannel,
    NotificationFrequency,
    NotificationPreference,
    RegulatoryUpdate,
    RelevanceScore,
    UpdateSeverity,
)


logger = structlog.get_logger()


class NotificationService:
    """Multi-channel notification service for regulatory alerts."""

    def __init__(self):
        self._preferences: dict[UUID, list[NotificationPreference]] = {}
        self._pending_alerts: dict[UUID, list[IntelligenceAlert]] = {}
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()

    def set_preferences(
        self,
        organization_id: UUID,
        preferences: list[NotificationPreference],
    ) -> None:
        """Set notification preferences for an organization."""
        self._preferences[organization_id] = preferences

    def get_preferences(
        self,
        organization_id: UUID,
    ) -> list[NotificationPreference]:
        """Get notification preferences for an organization."""
        return self._preferences.get(organization_id, [])

    async def send_alert(
        self,
        alert: IntelligenceAlert,
        preferences: list[NotificationPreference] | None = None,
    ) -> dict[str, bool]:
        """Send an alert through configured channels.
        
        Returns dict of channel -> success status.
        """
        if not alert.organization_id:
            return {}
        
        prefs = preferences or self.get_preferences(alert.organization_id)
        results: dict[str, bool] = {}
        
        for pref in prefs:
            if not pref.is_active:
                continue
            
            # Check severity threshold
            if not self._meets_severity_threshold(alert, pref):
                continue
            
            # Check frequency (immediate vs batched)
            if pref.frequency != NotificationFrequency.IMMEDIATE:
                self._queue_for_batch(alert, pref)
                results[f"{pref.channel.value}_batched"] = True
                continue
            
            # Send immediately
            success = await self._send_to_channel(alert, pref)
            results[pref.channel.value] = success
            
            if success:
                alert.channels_sent.append(pref.channel)
        
        if alert.channels_sent:
            alert.sent_at = datetime.utcnow()
        
        return results

    async def send_digest(
        self,
        digest: IntelligenceDigest,
        preferences: list[NotificationPreference] | None = None,
    ) -> dict[str, bool]:
        """Send a digest summary through configured channels."""
        if not digest.organization_id:
            return {}
        
        prefs = preferences or self.get_preferences(digest.organization_id)
        results: dict[str, bool] = {}
        
        # Create a digest alert
        alert = IntelligenceAlert(
            organization_id=digest.organization_id,
            title=f"Regulatory Intelligence Digest ({digest.period_start.date()} - {digest.period_end.date()})",
            body=self._format_digest_body(digest),
            action_required=f"Review {digest.critical_count + digest.high_count} high-priority updates" if (digest.critical_count + digest.high_count) > 0 else "No immediate action required",
        )
        
        for pref in prefs:
            if not pref.is_active:
                continue
            
            # Digests go to all channels
            success = await self._send_to_channel(alert, pref)
            results[pref.channel.value] = success
        
        return results

    async def process_batch(
        self,
        organization_id: UUID,
        frequency: NotificationFrequency,
    ) -> int:
        """Process batched alerts for an organization.
        
        Returns number of alerts sent.
        """
        key = f"{organization_id}:{frequency.value}"
        pending = self._pending_alerts.pop(organization_id, [])
        
        if not pending:
            return 0
        
        # Create digest from pending alerts
        digest = IntelligenceDigest(
            organization_id=organization_id,
            period_start=min(a.created_at for a in pending),
            period_end=max(a.created_at for a in pending),
            total_updates=len(pending),
            critical_count=sum(1 for a in pending if a.update and a.update.severity == UpdateSeverity.CRITICAL),
            high_count=sum(1 for a in pending if a.update and a.update.severity == UpdateSeverity.HIGH),
            alerts=pending,
        )
        
        await self.send_digest(digest)
        return len(pending)

    def create_alert_from_update(
        self,
        update: RegulatoryUpdate,
        relevance: RelevanceScore | None = None,
        organization_id: UUID | None = None,
    ) -> IntelligenceAlert:
        """Create an alert from a regulatory update."""
        title = f"[{update.severity.value.upper()}] {update.title}"
        
        body = f"**{update.framework}** - {update.jurisdiction}\n\n"
        body += f"{update.summary}\n\n"
        
        if update.effective_date:
            body += f"📅 Effective: {update.effective_date.date()}\n"
        
        if relevance and relevance.overall_score >= 0.5:
            body += f"\n🎯 Relevance: {relevance.overall_score:.0%}\n"
            body += f"{relevance.explanation}\n"
        
        body += f"\n🔗 [Read more]({update.url})" if update.url else ""
        
        action_required = ""
        if update.severity == UpdateSeverity.CRITICAL:
            action_required = "Immediate review required"
        elif update.severity == UpdateSeverity.HIGH:
            action_required = "Review within 7 days"
        elif update.severity == UpdateSeverity.MEDIUM:
            action_required = "Add to compliance backlog"
        
        return IntelligenceAlert(
            update=update,
            relevance=relevance,
            organization_id=organization_id,
            title=title,
            body=body,
            action_required=action_required,
            deadline=update.effective_date,
        )

    async def _send_to_channel(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Send alert to a specific channel."""
        try:
            if pref.channel == NotificationChannel.EMAIL:
                return await self._send_email(alert, pref)
            elif pref.channel == NotificationChannel.SLACK:
                return await self._send_slack(alert, pref)
            elif pref.channel == NotificationChannel.TEAMS:
                return await self._send_teams(alert, pref)
            elif pref.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(alert, pref)
            elif pref.channel == NotificationChannel.IN_APP:
                return await self._send_in_app(alert, pref)
            return False
        except Exception as e:
            logger.error(f"Failed to send {pref.channel.value} notification: {e}")
            return False

    async def _send_email(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Send email notification.
        
        In production, would use email service (SendGrid, SES, etc.)
        """
        logger.info(
            "Email notification",
            org_id=str(alert.organization_id),
            title=alert.title,
        )
        # Email sending would be implemented here
        return True

    async def _send_slack(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Send Slack notification via webhook."""
        if not pref.slack_channel:
            return False
        
        # Format for Slack
        severity_emoji = {
            UpdateSeverity.CRITICAL: "🔴",
            UpdateSeverity.HIGH: "🟠",
            UpdateSeverity.MEDIUM: "🟡",
            UpdateSeverity.LOW: "🔵",
            UpdateSeverity.INFO: "⚪",
        }
        
        emoji = severity_emoji.get(
            alert.update.severity if alert.update else UpdateSeverity.INFO,
            "ℹ️"
        )
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.title}",
                    "emoji": True,
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.body[:2000],
                }
            },
        ]
        
        if alert.action_required:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Required:* {alert.action_required}",
                }
            })
        
        if alert.deadline:
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"📅 Deadline: {alert.deadline.strftime('%Y-%m-%d')}",
                }]
            })
        
        payload = {
            "channel": pref.slack_channel,
            "blocks": blocks,
        }
        
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        
        # In production, would use actual Slack webhook URL
        # For now, just log the intent
        logger.info("Slack notification prepared", channel=pref.slack_channel)
        return True

    async def _send_teams(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Send Microsoft Teams notification via webhook."""
        if not pref.teams_channel:
            return False
        
        # Format for Teams Adaptive Card
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": self._get_severity_color(alert.update.severity if alert.update else UpdateSeverity.INFO),
            "summary": alert.title,
            "sections": [{
                "activityTitle": alert.title,
                "facts": [],
                "markdown": True,
                "text": alert.body[:2000],
            }],
        }
        
        if alert.update:
            card["sections"][0]["facts"].append({
                "name": "Framework",
                "value": alert.update.framework,
            })
            card["sections"][0]["facts"].append({
                "name": "Jurisdiction",
                "value": alert.update.jurisdiction,
            })
        
        if alert.action_required:
            card["sections"][0]["facts"].append({
                "name": "Action Required",
                "value": alert.action_required,
            })
        
        logger.info("Teams notification prepared", channel=pref.teams_channel)
        return True

    async def _send_webhook(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Send generic webhook notification."""
        if not pref.webhook_url:
            return False
        
        payload = {
            "event": "regulatory_alert",
            "alert_id": str(alert.id),
            "organization_id": str(alert.organization_id) if alert.organization_id else None,
            "title": alert.title,
            "body": alert.body,
            "action_required": alert.action_required,
            "deadline": alert.deadline.isoformat() if alert.deadline else None,
            "created_at": alert.created_at.isoformat(),
            "update": {
                "id": str(alert.update.id) if alert.update else None,
                "framework": alert.update.framework if alert.update else None,
                "jurisdiction": alert.update.jurisdiction if alert.update else None,
                "severity": alert.update.severity.value if alert.update else None,
                "url": alert.update.url if alert.update else None,
            } if alert.update else None,
            "relevance": {
                "score": alert.relevance.overall_score if alert.relevance else None,
                "explanation": alert.relevance.explanation if alert.relevance else None,
            } if alert.relevance else None,
        }
        
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        
        try:
            response = await self._http_client.post(
                pref.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            return response.status_code < 400
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return False

    async def _send_in_app(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Store notification for in-app display.
        
        In production, would store in database and potentially use WebSocket.
        """
        logger.info(
            "In-app notification stored",
            org_id=str(alert.organization_id),
            alert_id=str(alert.id),
        )
        return True

    def _meets_severity_threshold(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> bool:
        """Check if alert meets preference's severity threshold."""
        if not alert.update:
            return True
        
        severity_order = [
            UpdateSeverity.CRITICAL,
            UpdateSeverity.HIGH,
            UpdateSeverity.MEDIUM,
            UpdateSeverity.LOW,
            UpdateSeverity.INFO,
        ]
        
        alert_idx = severity_order.index(alert.update.severity)
        threshold_idx = severity_order.index(pref.min_severity)
        
        return alert_idx <= threshold_idx

    def _queue_for_batch(
        self,
        alert: IntelligenceAlert,
        pref: NotificationPreference,
    ) -> None:
        """Queue alert for batch processing."""
        if alert.organization_id:
            if alert.organization_id not in self._pending_alerts:
                self._pending_alerts[alert.organization_id] = []
            self._pending_alerts[alert.organization_id].append(alert)

    def _format_digest_body(self, digest: IntelligenceDigest) -> str:
        """Format digest for notification body."""
        body = f"## Regulatory Intelligence Summary\n\n"
        body += f"**Period:** {digest.period_start.date()} to {digest.period_end.date()}\n\n"
        body += f"**Total Updates:** {digest.total_updates}\n"
        body += f"- 🔴 Critical: {digest.critical_count}\n"
        body += f"- 🟠 High: {digest.high_count}\n"
        body += f"- 🟡 Medium: {digest.medium_count}\n\n"
        
        if digest.summary:
            body += digest.summary + "\n\n"
        
        # Top alerts
        if digest.alerts:
            body += "### Top Updates\n"
            for alert in digest.alerts[:5]:
                if alert.update:
                    body += f"- [{alert.update.severity.value.upper()}] {alert.update.title}\n"
        
        return body

    def _get_severity_color(self, severity: UpdateSeverity) -> str:
        """Get hex color for severity level."""
        colors = {
            UpdateSeverity.CRITICAL: "FF0000",
            UpdateSeverity.HIGH: "FF6600",
            UpdateSeverity.MEDIUM: "FFCC00",
            UpdateSeverity.LOW: "0066FF",
            UpdateSeverity.INFO: "999999",
        }
        return colors.get(severity, "999999")


# Global notification service instance
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create the notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
