"""Regulatory Intel Feed models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class FeedCategory(str, Enum):
    """Categories for regulatory intelligence articles."""

    BREAKING = "breaking"
    ANALYSIS = "analysis"
    ENFORCEMENT = "enforcement"
    GUIDANCE = "guidance"
    OPINION = "opinion"
    DEADLINE = "deadline"


class ContentFormat(str, Enum):
    """Content format preferences."""

    SUMMARY = "summary"
    FULL_ARTICLE = "full_article"
    DIGEST = "digest"
    ALERT = "alert"


@dataclass
class IntelArticle:
    """A regulatory intelligence article."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    summary: str = ""
    category: FeedCategory = FeedCategory.ANALYSIS
    regulation: str = ""
    jurisdiction: str = ""
    impact_score: float = 0.0
    source: str = ""
    source_url: str = ""
    ai_analysis: str = ""
    action_items: list[str] = field(default_factory=list)
    published_at: datetime | None = None


@dataclass
class FeedPreferences:
    """User preferences for the regulatory intelligence feed."""

    user_id: str = ""
    categories: list[FeedCategory] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    format: ContentFormat = ContentFormat.SUMMARY
    delivery: list[str] = field(default_factory=list)
    digest_frequency: str = "daily"


@dataclass
class DigestReport:
    """A compiled digest of regulatory intelligence articles."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    period: str = ""
    articles: list[IntelArticle] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class IntelFeedStats:
    """Statistics for the regulatory intelligence feed."""

    total_articles: int = 0
    by_category: dict = field(default_factory=dict)
    by_jurisdiction: dict = field(default_factory=dict)
    subscribers: int = 0
    digests_sent: int = 0
