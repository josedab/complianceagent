"""Localization Engine models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Language(str, Enum):
    """Supported languages."""

    EN = "en"
    DE = "de"
    FR = "fr"
    ES = "es"
    PT = "pt"
    JA = "ja"
    ZH = "zh"


class TranslationStatus(str, Enum):
    """Status of a translation entry."""

    TRANSLATED = "translated"
    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"
    MACHINE_TRANSLATED = "machine_translated"


@dataclass
class TranslationEntry:
    """A single translation entry for a UI key."""

    key: str = ""
    source_text: str = ""
    translated_text: str = ""
    language: Language = Language.EN
    status: TranslationStatus = TranslationStatus.PENDING
    context: str = ""
    last_updated: datetime | None = None


@dataclass
class LocaleConfig:
    """Configuration for a supported locale."""

    language: Language = Language.EN
    display_name: str = ""
    rtl: bool = False
    date_format: str = ""
    number_format: str = ""
    enabled: bool = True


@dataclass
class TranslationBundle:
    """A bundle of translations for a given language."""

    language: Language = Language.EN
    entries: list[TranslationEntry] = field(default_factory=list)
    total_keys: int = 0
    translated_keys: int = 0
    coverage_pct: float = 0.0
    last_exported: datetime | None = None


@dataclass
class LocalizationStats:
    """Statistics for the localization engine."""

    total_keys: int = 0
    languages_supported: int = 0
    by_language: dict[str, float] = field(default_factory=dict)
    machine_translated_pct: float = 0.0
    needs_review: int = 0
