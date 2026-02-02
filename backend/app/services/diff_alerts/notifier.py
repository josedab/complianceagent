"""Alert notification service for Slack, Teams, and email."""

import json
from datetime import datetime
from typing import Any

import httpx
import structlog

from app.services.diff_alerts.models import (
    AlertSeverity,
    NotificationConfig,
    RegulatoryAlert,
)

logger = structlog.get_logger()


class AlertNotifier:
    """Service for sending alert notifications to various channels."""

    def __init__(self, config: NotificationConfig):
        self.config = config

    async def send_alert(self, alert: RegulatoryAlert) -> dict[str, bool]:
        """
        Send alert to all configured channels.
        
        Returns dict of channel -> success status
        """
        results = {}
        
        # Check minimum severity
        severity_order = {
            AlertSeverity.LOW: 0,
            AlertSeverity.MEDIUM: 1,
            AlertSeverity.HIGH: 2,
            AlertSeverity.CRITICAL: 3,
        }
        
        if severity_order.get(alert.severity, 0) < severity_order.get(self.config.min_severity, 0):
            logger.debug("Alert below minimum severity threshold", 
                        alert_severity=alert.severity.value,
                        min_severity=self.config.min_severity.value)
            return {}

        # Send to Slack
        if self.config.slack_webhook_url:
            results["slack"] = await self._send_slack(alert)

        # Send to Teams
        if self.config.teams_webhook_url:
            results["teams"] = await self._send_teams(alert)

        # Send email
        if self.config.email_recipients:
            results["email"] = await self._send_email(alert)

        return results

    async def _send_slack(self, alert: RegulatoryAlert) -> bool:
        """Send alert to Slack via webhook."""
        if not self.config.slack_webhook_url:
            return False

        # Build Slack message
        severity_emoji = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.HIGH: "⚠️",
            AlertSeverity.MEDIUM: "📢",
            AlertSeverity.LOW: "ℹ️",
        }
        emoji = severity_emoji.get(alert.severity, "📋")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Regulatory Change Alert",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Regulation:*\n{alert.regulation_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{alert.severity.value.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Framework:*\n{alert.framework}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Jurisdiction:*\n{alert.jurisdiction}"
                    }
                ]
            },
        ]
        
        # Add impact summary if available
        if alert.impact_analysis:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{alert.impact_analysis.summary}"
                }
            })
            
            if alert.impact_analysis.key_changes:
                changes_text = "\n".join(f"• {c}" for c in alert.impact_analysis.key_changes[:5])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Key Changes:*\n{changes_text}"
                    }
                })

        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✓ Acknowledge",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": str(alert.id),
                    "action_id": "acknowledge_alert"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Details",
                        "emoji": True
                    },
                    "url": f"https://complianceagent.ai/alerts/{alert.id}",
                    "action_id": "view_alert"
                }
            ]
        })

        payload = {
            "blocks": blocks,
            "text": f"Regulatory Change Alert: {alert.regulation_name}",
        }
        
        if self.config.slack_channel:
            payload["channel"] = self.config.slack_channel

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.slack_webhook_url,
                    json=payload,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info("Slack notification sent", alert_id=str(alert.id))
                return True
        except Exception as e:
            logger.error("Slack notification failed", error=str(e))
            return False

    async def _send_teams(self, alert: RegulatoryAlert) -> bool:
        """Send alert to Microsoft Teams via webhook."""
        if not self.config.teams_webhook_url:
            return False

        # Build Teams Adaptive Card
        severity_color = {
            AlertSeverity.CRITICAL: "attention",
            AlertSeverity.HIGH: "warning",
            AlertSeverity.MEDIUM: "accent",
            AlertSeverity.LOW: "good",
        }
        
        facts = [
            {"title": "Regulation", "value": alert.regulation_name},
            {"title": "Severity", "value": alert.severity.value.upper()},
            {"title": "Framework", "value": alert.framework},
            {"title": "Jurisdiction", "value": alert.jurisdiction},
        ]
        
        body = [
            {
                "type": "TextBlock",
                "size": "Large",
                "weight": "Bolder",
                "text": "🔔 Regulatory Change Alert",
                "color": severity_color.get(alert.severity, "default")
            },
            {
                "type": "FactSet",
                "facts": facts
            }
        ]
        
        if alert.impact_analysis:
            body.append({
                "type": "TextBlock",
                "text": alert.impact_analysis.summary,
                "wrap": True
            })

        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": body,
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "View Details",
                                "url": f"https://complianceagent.ai/alerts/{alert.id}"
                            }
                        ]
                    }
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.teams_webhook_url,
                    json=card,
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info("Teams notification sent", alert_id=str(alert.id))
                return True
        except Exception as e:
            logger.error("Teams notification failed", error=str(e))
            return False

    async def _send_email(self, alert: RegulatoryAlert) -> bool:
        """Send alert via email (placeholder - integrate with email service)."""
        if not self.config.email_recipients:
            return False

        # In production, integrate with SendGrid, AWS SES, etc.
        logger.info(
            "Email notification would be sent",
            alert_id=str(alert.id),
            recipients=self.config.email_recipients,
        )
        return True

    def format_alert_message(self, alert: RegulatoryAlert) -> str:
        """Format alert as plain text message."""
        lines = [
            f"REGULATORY CHANGE ALERT",
            f"========================",
            f"",
            f"Regulation: {alert.regulation_name}",
            f"Severity: {alert.severity.value.upper()}",
            f"Framework: {alert.framework}",
            f"Jurisdiction: {alert.jurisdiction}",
            f"Detected: {alert.created_at.isoformat()}",
        ]
        
        if alert.impact_analysis:
            lines.extend([
                f"",
                f"IMPACT SUMMARY",
                f"--------------",
                alert.impact_analysis.summary,
                f"",
                f"KEY CHANGES:",
            ])
            for change in alert.impact_analysis.key_changes:
                lines.append(f"  • {change}")
            
            lines.extend([
                f"",
                f"RECOMMENDED ACTIONS:",
            ])
            for action in alert.impact_analysis.recommended_actions:
                lines.append(f"  • {action}")

        if alert.diff:
            lines.extend([
                f"",
                f"CHANGE METRICS",
                f"--------------",
                f"Lines added: {alert.diff.additions_count}",
                f"Lines removed: {alert.diff.deletions_count}",
                f"Similarity: {alert.diff.similarity_ratio:.0%}",
            ])

        return "\n".join(lines)
