"""Compliance-as-Code template services."""

from app.services.templates.registry import (
    ComplianceTemplate,
    TemplateCategory,
    TemplateRegistry,
    get_template_registry,
)


__all__ = [
    "ComplianceTemplate",
    "TemplateCategory",
    "TemplateRegistry",
    "get_template_registry",
]
