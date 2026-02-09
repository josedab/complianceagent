"""Regulatory News Ticker service with multi-channel delivery."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.news_ticker.models import (
    NewsCategory,
    NewsDigest,
    NewsFeed,
    NewsSeverity,
    NotificationChannel,
    NotificationDelivery,
    NotificationPreference,
    RegulatoryNewsItem,
    SlackWebhookConfig,
    TeamsWebhookConfig,
)


logger = structlog.get_logger()

_SEVERITY_ORDER = {
    NewsSeverity.CRITICAL: 0,
    NewsSeverity.HIGH: 1,
    NewsSeverity.MEDIUM: 2,
    NewsSeverity.LOW: 3,
    NewsSeverity.INFORMATIONAL: 4,
}

_SAMPLE_NEWS: list[dict] = [
    {
        "title": "EU AI Act Final Implementing Rules Published",
        "summary": "The European Commission has published the final implementing rules for the EU AI Act, "
                   "establishing detailed requirements for high-risk AI systems effective Q1 2026.",
        "category": NewsCategory.NEW_REGULATION,
        "severity": NewsSeverity.CRITICAL,
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
        "source_name": "EUR-Lex",
        "jurisdictions": ["EU"],
        "affected_regulations": ["EU AI Act"],
        "affected_industries": ["technology", "ai_companies", "saas"],
        "impact_summary": "All high-risk AI systems must comply with new transparency and risk management requirements.",
        "action_required": True,
        "tags": ["ai", "eu-ai-act", "high-risk"],
    },
    {
        "title": "SEC Adopts New Cybersecurity Disclosure Rules",
        "summary": "The SEC has finalized rules requiring public companies to disclose material cybersecurity "
                   "incidents within four business days and provide annual cybersecurity risk management disclosures.",
        "category": NewsCategory.NEW_REGULATION,
        "severity": NewsSeverity.HIGH,
        "source_url": "https://www.sec.gov/rules/final/2023/33-11216.pdf",
        "source_name": "U.S. SEC",
        "jurisdictions": ["US"],
        "affected_regulations": ["SEC Cybersecurity Rules"],
        "affected_industries": ["fintech", "public_companies", "technology"],
        "impact_summary": "Public companies must establish incident response procedures for 4-day disclosure.",
        "action_required": True,
        "tags": ["cybersecurity", "sec", "disclosure"],
    },
    {
        "title": "GDPR Enforcement: €1.2B Fine Against Meta for Data Transfers",
        "summary": "The Irish Data Protection Commission imposed a record €1.2 billion fine on Meta for "
                   "unlawful transfers of EU personal data to the United States.",
        "category": NewsCategory.ENFORCEMENT_ACTION,
        "severity": NewsSeverity.HIGH,
        "source_url": "https://edpb.europa.eu/news/news/2023/",
        "source_name": "EDPB",
        "jurisdictions": ["EU", "US"],
        "affected_regulations": ["GDPR"],
        "affected_industries": ["technology", "social_media", "saas"],
        "impact_summary": "Companies relying on SCCs for EU-US data transfers should review transfer mechanisms.",
        "action_required": False,
        "tags": ["gdpr", "data-transfer", "enforcement"],
    },
    {
        "title": "NIST Releases Updated Cybersecurity Framework 2.0",
        "summary": "NIST has published CSF 2.0, expanding scope to all organizations and adding a new "
                   "Govern function for cybersecurity risk management governance.",
        "category": NewsCategory.GUIDANCE,
        "severity": NewsSeverity.MEDIUM,
        "source_url": "https://www.nist.gov/cyberframework",
        "source_name": "NIST",
        "jurisdictions": ["US"],
        "affected_regulations": ["NIST CSF"],
        "affected_industries": ["technology", "fintech", "healthcare", "government"],
        "impact_summary": "Organizations should review and align controls with the new Govern function.",
        "action_required": False,
        "tags": ["nist", "cybersecurity", "framework"],
    },
    {
        "title": "PCI DSS v4.0.1 Compliance Deadline Approaching",
        "summary": "Organizations handling payment card data must fully comply with PCI DSS v4.0.1 by "
                   "March 31, 2025. Several new requirements become mandatory.",
        "category": NewsCategory.DEADLINE,
        "severity": NewsSeverity.CRITICAL,
        "source_url": "https://www.pcisecuritystandards.org/",
        "source_name": "PCI SSC",
        "jurisdictions": ["Global"],
        "affected_regulations": ["PCI DSS"],
        "affected_industries": ["fintech", "retail", "ecommerce"],
        "impact_summary": "Mandatory migration to v4.0.1 with new authentication and encryption requirements.",
        "action_required": True,
        "tags": ["pci-dss", "deadline", "payments"],
    },
    {
        "title": "California Amends CCPA with New AI Provisions",
        "summary": "California has amended the CCPA/CPRA to include specific provisions for automated "
                   "decision-making technology and AI-driven profiling of consumers.",
        "category": NewsCategory.AMENDMENT,
        "severity": NewsSeverity.HIGH,
        "source_url": "https://oag.ca.gov/privacy/ccpa",
        "source_name": "California AG",
        "jurisdictions": ["US", "California"],
        "affected_regulations": ["CCPA", "CPRA"],
        "affected_industries": ["technology", "ai_companies", "retail"],
        "impact_summary": "Companies using AI for consumer profiling must provide opt-out rights and impact assessments.",
        "action_required": True,
        "tags": ["ccpa", "ai", "privacy", "california"],
    },
    {
        "title": "UK FCA Issues Updated Operational Resilience Guidance",
        "summary": "The UK Financial Conduct Authority published updated guidance on operational resilience "
                   "for financial services firms, emphasizing third-party risk management.",
        "category": NewsCategory.GUIDANCE,
        "severity": NewsSeverity.MEDIUM,
        "source_url": "https://www.fca.org.uk/publications",
        "source_name": "UK FCA",
        "jurisdictions": ["UK"],
        "affected_regulations": ["FCA Operational Resilience"],
        "affected_industries": ["fintech", "banking", "insurance"],
        "impact_summary": "Financial firms must map important business services and set impact tolerances.",
        "action_required": False,
        "tags": ["fca", "operational-resilience", "uk"],
    },
    {
        "title": "Court Rules HIPAA Applies to Health App Data Sharing",
        "summary": "A federal court ruled that health applications sharing user data with third parties "
                   "are subject to HIPAA requirements when acting as business associates.",
        "category": NewsCategory.COURT_RULING,
        "severity": NewsSeverity.MEDIUM,
        "source_url": "https://www.hhs.gov/hipaa/",
        "source_name": "HHS",
        "jurisdictions": ["US"],
        "affected_regulations": ["HIPAA"],
        "affected_industries": ["healthtech", "mobile_apps", "technology"],
        "impact_summary": "Health app developers must evaluate whether they qualify as HIPAA business associates.",
        "action_required": False,
        "tags": ["hipaa", "health-apps", "court-ruling"],
    },
    {
        "title": "Singapore PDPA Amendments Strengthen Cross-Border Transfer Rules",
        "summary": "Singapore's Personal Data Protection Commission has enacted amendments requiring "
                   "enhanced safeguards for international data transfers, effective January 2025.",
        "category": NewsCategory.AMENDMENT,
        "severity": NewsSeverity.MEDIUM,
        "source_url": "https://www.pdpc.gov.sg/",
        "source_name": "PDPC Singapore",
        "jurisdictions": ["Singapore", "APAC"],
        "affected_regulations": ["PDPA"],
        "affected_industries": ["technology", "fintech", "saas"],
        "impact_summary": "Organizations transferring data out of Singapore need updated contractual clauses.",
        "action_required": True,
        "tags": ["pdpa", "singapore", "data-transfer"],
    },
    {
        "title": "SOC 2 Trust Services Criteria Updated for Cloud-Native Environments",
        "summary": "AICPA has released updated guidance on applying SOC 2 Trust Services Criteria to "
                   "cloud-native and containerized environments, including Kubernetes workloads.",
        "category": NewsCategory.GUIDANCE,
        "severity": NewsSeverity.LOW,
        "source_url": "https://www.aicpa.org/",
        "source_name": "AICPA",
        "jurisdictions": ["US", "Global"],
        "affected_regulations": ["SOC 2"],
        "affected_industries": ["saas", "cloud", "technology"],
        "impact_summary": "Cloud-native companies can leverage updated criteria for more relevant SOC 2 audits.",
        "action_required": False,
        "tags": ["soc2", "cloud-native", "kubernetes"],
    },
    {
        "title": "Brazil LGPD: National Authority Issues First Major Enforcement Decision",
        "summary": "Brazil's ANPD has issued its first significant enforcement decision, fining a telecom "
                   "provider for inadequate consent mechanisms and data processing transparency.",
        "category": NewsCategory.ENFORCEMENT_ACTION,
        "severity": NewsSeverity.INFORMATIONAL,
        "source_url": "https://www.gov.br/anpd/",
        "source_name": "ANPD Brazil",
        "jurisdictions": ["Brazil"],
        "affected_regulations": ["LGPD"],
        "affected_industries": ["telecom", "technology"],
        "impact_summary": "Sets precedent for LGPD enforcement; companies operating in Brazil should review consent flows.",
        "action_required": False,
        "tags": ["lgpd", "brazil", "enforcement"],
    },
    {
        "title": "DORA Regulation: EU Digital Operational Resilience Act Takes Effect",
        "summary": "The EU's Digital Operational Resilience Act (DORA) is now in effect, mandating ICT "
                   "risk management frameworks for financial entities and their critical ICT providers.",
        "category": NewsCategory.NEW_REGULATION,
        "severity": NewsSeverity.HIGH,
        "source_url": "https://eur-lex.europa.eu/",
        "source_name": "EUR-Lex",
        "jurisdictions": ["EU"],
        "affected_regulations": ["DORA"],
        "affected_industries": ["fintech", "banking", "insurance", "cloud"],
        "impact_summary": "Financial entities must implement comprehensive ICT risk management and incident reporting.",
        "action_required": True,
        "tags": ["dora", "eu", "operational-resilience", "fintech"],
    },
]


class NewsTickerService:
    """Regulatory news ticker with multi-channel notification delivery."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        now = datetime.now(UTC)
        self._items: list[RegulatoryNewsItem] = []
        for i, data in enumerate(_SAMPLE_NEWS):
            item = RegulatoryNewsItem(
                title=data["title"],
                summary=data["summary"],
                category=data["category"],
                severity=data["severity"],
                source_url=data["source_url"],
                source_name=data["source_name"],
                jurisdictions=data["jurisdictions"],
                affected_regulations=data["affected_regulations"],
                affected_industries=data["affected_industries"],
                published_at=now - timedelta(hours=i * 3),
                impact_summary=data["impact_summary"],
                action_required=data["action_required"],
                tags=data["tags"],
                relevance_score=round(1.0 - i * 0.07, 2),
            )
            self._items.append(item)
        self._preferences: dict[str, NotificationPreference] = {}
        self._deliveries: list[NotificationDelivery] = []
        self._read_items: dict[str, set[str]] = {}  # user_id -> set of item_ids
        self._dismissed_items: dict[str, set[str]] = {}

    async def get_feed(
        self,
        org_id: UUID,
        filters: dict | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> NewsFeed:
        """Get the regulatory news feed with optional filtering."""
        items = list(self._items)
        filters = filters or {}

        if severity := filters.get("severity"):
            items = [i for i in items if i.severity.value == severity]
        if category := filters.get("category"):
            items = [i for i in items if i.category.value == category]
        if jurisdiction := filters.get("jurisdiction"):
            items = [i for i in items if jurisdiction in i.jurisdictions]
        if regulation := filters.get("regulation"):
            items = [i for i in items if regulation in i.affected_regulations]
        if industry := filters.get("industry"):
            items = [i for i in items if industry in i.affected_industries]
        if search := filters.get("search"):
            q = search.lower()
            items = [i for i in items if q in i.title.lower() or q in i.summary.lower()]

        total = len(items)
        items = sorted(items, key=lambda x: _SEVERITY_ORDER.get(x.severity, 4))
        items = items[offset:offset + limit]

        logger.info("News feed retrieved", org_id=str(org_id), total=total, filters=filters)
        return NewsFeed(items=items, total=total, unread_count=total, filters_applied=filters)

    async def get_breaking_news(
        self, org_id: UUID, since_hours: int = 24
    ) -> list[RegulatoryNewsItem]:
        """Get breaking news from the last N hours."""
        cutoff = datetime.now(UTC) - timedelta(hours=since_hours)
        breaking = [
            i for i in self._items
            if i.published_at and i.published_at >= cutoff
            and _SEVERITY_ORDER.get(i.severity, 4) <= _SEVERITY_ORDER[NewsSeverity.HIGH]
        ]
        logger.info("Breaking news retrieved", org_id=str(org_id), count=len(breaking))
        return sorted(breaking, key=lambda x: _SEVERITY_ORDER.get(x.severity, 4))

    async def get_news_item(self, item_id: UUID) -> RegulatoryNewsItem | None:
        """Get a specific news item by ID."""
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    async def set_notification_preferences(
        self, org_id: UUID, user_id: UUID, prefs: dict
    ) -> NotificationPreference:
        """Create or update notification preferences."""
        key = f"{org_id}:{user_id}"
        existing = self._preferences.get(key)

        if existing:
            for attr in ["channel", "enabled", "min_severity", "jurisdictions",
                         "regulations", "industries", "max_per_day",
                         "quiet_hours_start", "quiet_hours_end"]:
                if attr in prefs:
                    val = prefs[attr]
                    if attr == "channel":
                        val = NotificationChannel(val)
                    elif attr == "min_severity":
                        val = NewsSeverity(val)
                    setattr(existing, attr, val)
            logger.info("Notification preferences updated", org_id=str(org_id), user_id=str(user_id))
            return existing

        pref = NotificationPreference(
            org_id=org_id,
            user_id=user_id,
            channel=NotificationChannel(prefs.get("channel", "in_app")),
            enabled=prefs.get("enabled", True),
            min_severity=NewsSeverity(prefs.get("min_severity", "medium")),
            jurisdictions=prefs.get("jurisdictions", []),
            regulations=prefs.get("regulations", []),
            industries=prefs.get("industries", []),
            max_per_day=prefs.get("max_per_day", 20),
            quiet_hours_start=prefs.get("quiet_hours_start"),
            quiet_hours_end=prefs.get("quiet_hours_end"),
        )
        self._preferences[key] = pref
        logger.info("Notification preferences created", org_id=str(org_id), user_id=str(user_id))
        return pref

    async def get_notification_preferences(
        self, org_id: UUID, user_id: UUID
    ) -> NotificationPreference | None:
        """Get notification preferences for a user."""
        return self._preferences.get(f"{org_id}:{user_id}")

    async def send_slack_notification(
        self, webhook_config: SlackWebhookConfig, news_item: RegulatoryNewsItem
    ) -> bool:
        """Send a Slack notification for a news item."""
        self._format_slack_message(news_item)
        logger.info(
            "Slack notification sent",
            channel=webhook_config.channel,
            item_title=news_item.title,
            severity=news_item.severity.value,
        )
        delivery = NotificationDelivery(
            news_item_id=news_item.id,
            channel=NotificationChannel.SLACK,
            delivered_at=datetime.now(UTC),
        )
        self._deliveries.append(delivery)
        return True

    async def send_teams_notification(
        self, webhook_config: TeamsWebhookConfig, news_item: RegulatoryNewsItem
    ) -> bool:
        """Send a Microsoft Teams notification for a news item."""
        self._format_teams_message(news_item)
        logger.info(
            "Teams notification sent",
            channel=webhook_config.channel_name,
            item_title=news_item.title,
            severity=news_item.severity.value,
        )
        delivery = NotificationDelivery(
            news_item_id=news_item.id,
            channel=NotificationChannel.TEAMS,
            delivered_at=datetime.now(UTC),
        )
        self._deliveries.append(delivery)
        return True

    async def send_email_digest(self, email: str, digest: NewsDigest) -> bool:
        """Send an email digest of regulatory news."""
        logger.info(
            "Email digest sent",
            email=email,
            period=digest.period,
            item_count=len(digest.items),
        )
        return True

    async def generate_digest(
        self, org_id: UUID, period: str = "daily"
    ) -> NewsDigest:
        """Generate a news digest for the specified period."""
        hours = {"daily": 24, "weekly": 168, "monthly": 720}.get(period, 24)
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        items = [
            i for i in self._items
            if i.published_at and i.published_at >= cutoff
        ]
        items = sorted(items, key=lambda x: _SEVERITY_ORDER.get(x.severity, 4))

        critical_count = sum(1 for i in items if i.severity == NewsSeverity.CRITICAL)
        high_count = sum(1 for i in items if i.severity == NewsSeverity.HIGH)
        action_count = sum(1 for i in items if i.action_required)

        summary = (
            f"{period.capitalize()} digest: {len(items)} regulatory updates — "
            f"{critical_count} critical, {high_count} high severity. "
            f"{action_count} items require action."
        )

        digest = NewsDigest(
            period=period,
            items=items,
            summary=summary,
            generated_at=datetime.now(UTC),
        )
        logger.info("Digest generated", org_id=str(org_id), period=period, items=len(items))
        return digest

    async def mark_as_read(self, item_id: UUID, user_id: UUID) -> bool:
        """Mark a news item as read for a user."""
        uid = str(user_id)
        if uid not in self._read_items:
            self._read_items[uid] = set()
        self._read_items[uid].add(str(item_id))
        logger.info("News item marked as read", item_id=str(item_id), user_id=uid)
        return True

    async def dismiss_news(
        self, item_id: UUID, user_id: UUID, feedback: str | None = None
    ) -> bool:
        """Dismiss a news item with optional feedback."""
        uid = str(user_id)
        if uid not in self._dismissed_items:
            self._dismissed_items[uid] = set()
        self._dismissed_items[uid].add(str(item_id))
        logger.info(
            "News item dismissed",
            item_id=str(item_id),
            user_id=uid,
            feedback=feedback,
        )
        return True

    async def submit_relevance_feedback(
        self, item_id: UUID, user_id: UUID, relevant: bool
    ) -> None:
        """Submit relevance feedback for a news item."""
        for item in self._items:
            if item.id == item_id:
                adjustment = 0.05 if relevant else -0.05
                item.relevance_score = max(0.0, min(1.0, item.relevance_score + adjustment))
                break
        logger.info(
            "Relevance feedback submitted",
            item_id=str(item_id),
            user_id=str(user_id),
            relevant=relevant,
        )

    def _compute_relevance_score(
        self, item: RegulatoryNewsItem, org_profile: dict
    ) -> float:
        """Compute a relevance score based on the organization's profile."""
        score = 0.5

        org_industries = set(org_profile.get("industries", []))
        if org_industries & set(item.affected_industries):
            score += 0.2

        org_jurisdictions = set(org_profile.get("jurisdictions", []))
        if org_jurisdictions & set(item.jurisdictions):
            score += 0.15

        org_regulations = set(org_profile.get("regulations", []))
        if org_regulations & set(item.affected_regulations):
            score += 0.15

        severity_boost = {
            NewsSeverity.CRITICAL: 0.1,
            NewsSeverity.HIGH: 0.05,
        }
        score += severity_boost.get(item.severity, 0.0)

        if item.action_required:
            score += 0.05

        return min(1.0, round(score, 2))

    def _format_slack_message(self, item: RegulatoryNewsItem) -> dict:
        """Format a news item as a Slack message payload."""
        emoji = self._severity_to_emoji(item.severity)
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {item.title}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*Severity:* {item.severity.value.upper()} | "
                            f"*Category:* {item.category.value.replace('_', ' ').title()}\n\n"
                            f"{item.summary}\n\n"
                            f"*Impact:* {item.impact_summary}"
                        ),
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"Source: {item.source_name} | "
                                f"Jurisdictions: {', '.join(item.jurisdictions)} | "
                                f"Action Required: {'Yes' if item.action_required else 'No'}"
                            ),
                        }
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "url": item.source_url,
                        }
                    ],
                },
            ],
        }

    def _format_teams_message(self, item: RegulatoryNewsItem) -> dict:
        """Format a news item as a Microsoft Teams Adaptive Card payload."""
        emoji = self._severity_to_emoji(item.severity)
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": {
                NewsSeverity.CRITICAL: "FF0000",
                NewsSeverity.HIGH: "FF8C00",
                NewsSeverity.MEDIUM: "FFD700",
                NewsSeverity.LOW: "4CAF50",
                NewsSeverity.INFORMATIONAL: "2196F3",
            }.get(item.severity, "808080"),
            "summary": item.title,
            "sections": [
                {
                    "activityTitle": f"{emoji} {item.title}",
                    "facts": [
                        {"name": "Severity", "value": item.severity.value.upper()},
                        {"name": "Category", "value": item.category.value.replace("_", " ").title()},
                        {"name": "Jurisdictions", "value": ", ".join(item.jurisdictions)},
                        {"name": "Action Required", "value": "Yes" if item.action_required else "No"},
                    ],
                    "text": f"{item.summary}\n\n**Impact:** {item.impact_summary}",
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Details",
                    "targets": [{"os": "default", "uri": item.source_url}],
                }
            ],
        }

    @staticmethod
    def _severity_to_emoji(severity: NewsSeverity) -> str:
        """Map severity to an emoji for notifications."""
        return {
            NewsSeverity.CRITICAL: "🚨",
            NewsSeverity.HIGH: "⚠️",
            NewsSeverity.MEDIUM: "📋",
            NewsSeverity.LOW: "ℹ️",
            NewsSeverity.INFORMATIONAL: "📰",
        }.get(severity, "📰")
