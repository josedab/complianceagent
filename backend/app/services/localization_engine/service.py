"""Localization Engine Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.localization_engine.models import (
    Language,
    LocaleConfig,
    LocalizationStats,
    TranslationBundle,
    TranslationEntry,
    TranslationStatus,
)


logger = structlog.get_logger()

_LOCALE_CONFIGS: list[LocaleConfig] = [
    LocaleConfig(
        language=Language.EN,
        display_name="English",
        rtl=False,
        date_format="MM/DD/YYYY",
        number_format="1,234.56",
        enabled=True,
    ),
    LocaleConfig(
        language=Language.DE,
        display_name="Deutsch",
        rtl=False,
        date_format="DD.MM.YYYY",
        number_format="1.234,56",
        enabled=True,
    ),
    LocaleConfig(
        language=Language.FR,
        display_name="Français",
        rtl=False,
        date_format="DD/MM/YYYY",
        number_format="1 234,56",
        enabled=True,
    ),
    LocaleConfig(
        language=Language.ES,
        display_name="Español",
        rtl=False,
        date_format="DD/MM/YYYY",
        number_format="1.234,56",
        enabled=True,
    ),
    LocaleConfig(
        language=Language.PT,
        display_name="Português",
        rtl=False,
        date_format="DD/MM/YYYY",
        number_format="1.234,56",
        enabled=True,
    ),
    LocaleConfig(
        language=Language.JA,
        display_name="日本語",
        rtl=False,
        date_format="YYYY/MM/DD",
        number_format="1,234.56",
        enabled=True,
    ),
    LocaleConfig(
        language=Language.ZH,
        display_name="中文",
        rtl=False,
        date_format="YYYY-MM-DD",
        number_format="1,234.56",
        enabled=True,
    ),
]

_SEED_KEYS: dict[str, str] = {
    "dashboard.title": "Dashboard",
    "dashboard.overview": "Overview",
    "settings.title": "Settings",
    "settings.language": "Language",
    "settings.notifications": "Notifications",
    "compliance_score.title": "Compliance Score",
    "compliance_score.trend": "Score Trend",
    "violations.title": "Violations",
    "violations.severity": "Severity",
    "violations.count": "Count",
    "incidents.title": "Incidents",
    "incidents.open": "Open Incidents",
    "incidents.resolved": "Resolved",
    "reports.title": "Reports",
    "reports.generate": "Generate Report",
    "reports.export": "Export",
    "nav.home": "Home",
    "nav.audit": "Audit",
    "nav.policies": "Policies",
    "actions.save": "Save",
    "actions.cancel": "Cancel",
    "actions.delete": "Delete",
}

_PARTIAL_TRANSLATIONS: dict[str, dict[str, str]] = {
    "de": {
        "dashboard.title": "Instrumententafel",
        "dashboard.overview": "Übersicht",
        "settings.title": "Einstellungen",
        "settings.language": "Sprache",
        "compliance_score.title": "Compliance-Bewertung",
        "violations.title": "Verstöße",
        "violations.severity": "Schweregrad",
        "incidents.title": "Vorfälle",
        "reports.title": "Berichte",
        "nav.home": "Startseite",
        "actions.save": "Speichern",
        "actions.cancel": "Abbrechen",
        "actions.delete": "Löschen",
    },
    "fr": {
        "dashboard.title": "Tableau de bord",
        "dashboard.overview": "Aperçu",
        "settings.title": "Paramètres",
        "settings.language": "Langue",
        "compliance_score.title": "Score de conformité",
        "violations.title": "Violations",
        "incidents.title": "Incidents",
        "reports.title": "Rapports",
        "nav.home": "Accueil",
        "actions.save": "Enregistrer",
        "actions.cancel": "Annuler",
    },
    "es": {
        "dashboard.title": "Panel",
        "dashboard.overview": "Resumen",
        "settings.title": "Configuración",
        "settings.language": "Idioma",
        "compliance_score.title": "Puntuación de cumplimiento",
        "violations.title": "Violaciones",
        "incidents.title": "Incidentes",
        "reports.title": "Informes",
        "nav.home": "Inicio",
        "actions.save": "Guardar",
    },
    "pt": {
        "dashboard.title": "Painel",
        "settings.title": "Configurações",
        "compliance_score.title": "Pontuação de conformidade",
        "violations.title": "Violações",
        "incidents.title": "Incidentes",
        "nav.home": "Início",
        "actions.save": "Salvar",
    },
    "ja": {
        "dashboard.title": "ダッシュボード",
        "settings.title": "設定",
        "compliance_score.title": "コンプライアンススコア",
        "violations.title": "違反",
        "incidents.title": "インシデント",
        "nav.home": "ホーム",
        "actions.save": "保存",
        "actions.cancel": "キャンセル",
    },
    "zh": {
        "dashboard.title": "仪表板",
        "settings.title": "设置",
        "compliance_score.title": "合规评分",
        "violations.title": "违规",
        "incidents.title": "事件",
        "nav.home": "首页",
        "actions.save": "保存",
    },
}


class LocalizationEngineService:
    """Service for managing translations and localization."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._translations: dict[str, dict[str, TranslationEntry]] = {}
        self._build_seed_translations()

    def _build_seed_translations(self) -> None:
        """Build seed translation entries for all supported languages."""
        now = datetime.now(UTC)

        # English — fully translated
        en_entries: dict[str, TranslationEntry] = {}
        for key, text in _SEED_KEYS.items():
            en_entries[key] = TranslationEntry(
                key=key,
                source_text=text,
                translated_text=text,
                language=Language.EN,
                status=TranslationStatus.TRANSLATED,
                context="common",
                last_updated=now,
            )
        self._translations["en"] = en_entries

        # Other languages — partial translations
        for lang_code, translations in _PARTIAL_TRANSLATIONS.items():
            lang_entries: dict[str, TranslationEntry] = {}
            language = Language(lang_code)
            for key, source_text in _SEED_KEYS.items():
                if key in translations:
                    lang_entries[key] = TranslationEntry(
                        key=key,
                        source_text=source_text,
                        translated_text=translations[key],
                        language=language,
                        status=TranslationStatus.TRANSLATED,
                        context="common",
                        last_updated=now,
                    )
                else:
                    lang_entries[key] = TranslationEntry(
                        key=key,
                        source_text=source_text,
                        translated_text="",
                        language=language,
                        status=TranslationStatus.PENDING,
                        context="common",
                        last_updated=now,
                    )
            self._translations[lang_code] = lang_entries

    async def get_translations(
        self, language: Language, namespace: str = "common"
    ) -> TranslationBundle:
        """Get all translations for a language and namespace."""
        log = logger.bind(language=language.value, namespace=namespace)
        log.info("translations.get")

        entries_map = self._translations.get(language.value, {})
        entries = [
            e for e in entries_map.values() if e.context == namespace
        ]
        translated = [
            e for e in entries if e.status == TranslationStatus.TRANSLATED
        ]

        return TranslationBundle(
            language=language,
            entries=entries,
            total_keys=len(entries),
            translated_keys=len(translated),
            coverage_pct=(
                len(translated) / len(entries) * 100 if entries else 0.0
            ),
            last_exported=None,
        )

    async def translate_key(
        self, key: str, language: Language
    ) -> TranslationEntry:
        """Get or create a translation for a specific key."""
        log = logger.bind(key=key, language=language.value)

        entries = self._translations.get(language.value, {})
        if key in entries:
            return entries[key]

        source_text = _SEED_KEYS.get(key, key)
        entry = TranslationEntry(
            key=key,
            source_text=source_text,
            translated_text="",
            language=language,
            status=TranslationStatus.PENDING,
            context="common",
            last_updated=datetime.now(UTC),
        )

        if language.value not in self._translations:
            self._translations[language.value] = {}
        self._translations[language.value][key] = entry

        log.info("translation.key.created")
        return entry

    async def list_languages(self) -> list[LocaleConfig]:
        """List all supported locale configurations."""
        return list(_LOCALE_CONFIGS)

    async def get_missing_translations(
        self, language: Language
    ) -> list[str]:
        """Get keys missing translations for a given language."""
        entries = self._translations.get(language.value, {})
        missing: list[str] = []
        for key in _SEED_KEYS:
            entry = entries.get(key)
            if not entry or entry.status == TranslationStatus.PENDING:
                missing.append(key)
        return missing

    async def export_bundle(
        self, language: Language, format: str = "json"
    ) -> dict:
        """Export a translation bundle in the specified format."""
        log = logger.bind(language=language.value, format=format)
        log.info("bundle.export")

        entries = self._translations.get(language.value, {})
        translations: dict[str, str] = {}
        for key, entry in entries.items():
            if entry.status == TranslationStatus.TRANSLATED:
                translations[key] = entry.translated_text

        return {
            "format": format,
            "language": language.value,
            "keys": len(translations),
            "translations": translations,
            "exported_at": datetime.now(UTC).isoformat(),
        }

    async def import_translations(
        self, language: Language, entries: list[dict]
    ) -> int:
        """Import translation entries for a language."""
        log = logger.bind(language=language.value, count=len(entries))
        log.info("translations.import.start")

        if language.value not in self._translations:
            self._translations[language.value] = {}

        imported = 0
        now = datetime.now(UTC)
        for item in entries:
            key = item.get("key", "")
            translated = item.get("translated_text", "")
            if key and translated:
                self._translations[language.value][key] = TranslationEntry(
                    key=key,
                    source_text=_SEED_KEYS.get(key, key),
                    translated_text=translated,
                    language=language,
                    status=TranslationStatus.TRANSLATED,
                    context=item.get("context", "common"),
                    last_updated=now,
                )
                imported += 1

        log.info("translations.imported", imported=imported)
        return imported

    async def get_stats(self) -> LocalizationStats:
        """Get aggregate localization statistics."""
        total_keys = len(_SEED_KEYS)
        languages = len(self._translations)

        by_language: dict[str, float] = {}
        machine_translated = 0
        needs_review = 0
        total_entries = 0

        for lang_code, entries in self._translations.items():
            translated = sum(
                1
                for e in entries.values()
                if e.status == TranslationStatus.TRANSLATED
            )
            by_language[lang_code] = (
                translated / len(entries) * 100 if entries else 0.0
            )
            for entry in entries.values():
                total_entries += 1
                if entry.status == TranslationStatus.MACHINE_TRANSLATED:
                    machine_translated += 1
                if entry.status == TranslationStatus.NEEDS_REVIEW:
                    needs_review += 1

        return LocalizationStats(
            total_keys=total_keys,
            languages_supported=languages,
            by_language=by_language,
            machine_translated_pct=(
                machine_translated / total_entries * 100
                if total_entries
                else 0.0
            ),
            needs_review=needs_review,
        )
