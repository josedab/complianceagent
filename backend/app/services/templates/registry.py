"""Compliance-as-Code template registry and library.

This module provides a registry for managing compliance code templates.
Templates are organized by category and loaded from separate module files.
"""

from typing import Any

import structlog

from app.services.templates.base import (
    ComplianceTemplate,
    TemplateCategory,
    TemplateParameter,
)
from app.services.templates.audit_templates import AUDIT_TEMPLATES
from app.services.templates.consent_templates import CONSENT_TEMPLATES
from app.services.templates.data_access_templates import DATA_ACCESS_TEMPLATES
from app.services.templates.hipaa_templates import HIPAA_TEMPLATES
from app.services.templates.pci_templates import PCI_TEMPLATES


logger = structlog.get_logger()

# Re-export base types for backwards compatibility
__all__ = [
    "ComplianceTemplate",
    "TemplateCategory",
    "TemplateParameter",
    "TemplateRegistry",
    "get_template_registry",
]


def _get_all_builtin_templates() -> list[ComplianceTemplate]:
    """Aggregate all builtin templates from category modules."""
    return (
        CONSENT_TEMPLATES
        + HIPAA_TEMPLATES
        + DATA_ACCESS_TEMPLATES
        + AUDIT_TEMPLATES
        + PCI_TEMPLATES
    )


class TemplateRegistry:
    """Registry for compliance code templates."""

    def __init__(self):
        self._templates: dict[str, ComplianceTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates from category modules."""
        for template in _get_all_builtin_templates():
            self._templates[str(template.id)] = template
        logger.info(
            "Loaded builtin templates",
            count=len(self._templates),
        )

    def get_template(self, template_id: str) -> ComplianceTemplate | None:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def list_templates(
        self,
        category: TemplateCategory | None = None,
        regulation: str | None = None,
        language: str | None = None,
        search: str | None = None,
    ) -> list[ComplianceTemplate]:
        """List templates with optional filters."""
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if regulation:
            templates = [t for t in templates if regulation in t.regulations]

        if language:
            templates = [t for t in templates if language in t.languages]

        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower()
                or search_lower in t.description.lower()
                or any(search_lower in tag for tag in t.tags)
            ]

        return templates

    def add_template(self, template: ComplianceTemplate) -> None:
        """Add a custom template."""
        self._templates[str(template.id)] = template

    def get_template_code(
        self,
        template_id: str,
        language: str,
        parameters: dict[str, Any] | None = None,
    ) -> str | None:
        """Get template code with parameter substitution."""
        template = self.get_template(template_id)
        if not template or language not in template.code:
            return None

        code = template.code[language]

        # Simple parameter substitution
        if parameters:
            for key, value in parameters.items():
                code = code.replace(f"{{{{ {key} }}}}", str(value))

        return code

    def get_categories(self) -> list[dict[str, Any]]:
        """Get all template categories with counts."""
        counts: dict[TemplateCategory, int] = {}
        for template in self._templates.values():
            counts[template.category] = counts.get(template.category, 0) + 1

        return [
            {
                "category": cat.value,
                "name": cat.value.replace("_", " ").title(),
                "count": counts.get(cat, 0),
            }
            for cat in TemplateCategory
        ]


# Global registry instance
_registry: TemplateRegistry | None = None


def get_template_registry() -> TemplateRegistry:
    """Get or create the global template registry."""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
