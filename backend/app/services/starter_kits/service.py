"""Regulation-specific starter kits service."""

import json
import zipfile
from datetime import UTC, datetime
from io import BytesIO
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.starter_kits.gdpr_kit import create_gdpr_kit
from app.services.starter_kits.hipaa_kit import create_hipaa_kit
from app.services.starter_kits.models import (
    CodeTemplate,
    ConfigTemplate,
    DocumentTemplate,
    StarterKit,
    TemplateLanguage,
)
from app.services.starter_kits.pci_kit import create_pci_kit
from app.services.starter_kits.soc2_kit import create_soc2_kit


logger = structlog.get_logger()


class StarterKitsService:
    """Service for managing regulation-specific starter kits."""

    def __init__(self, db: AsyncSession, copilot: Any = None):
        self.db = db
        self.copilot = copilot
        self._kits = self._initialize_kits()

    def _initialize_kits(self) -> dict[str, StarterKit]:
        """Initialize built-in starter kits."""
        return {
            "GDPR": create_gdpr_kit(),
            "HIPAA": create_hipaa_kit(),
            "PCI_DSS": create_pci_kit(),
            "SOC2": create_soc2_kit(),
        }

    async def list_kits(
        self,
        framework: str | None = None,
        language: TemplateLanguage | None = None,
    ) -> list[StarterKit]:
        """List available starter kits."""
        kits = list(self._kits.values())

        if framework:
            kits = [k for k in kits if k.framework == framework]

        if language:
            kits = [k for k in kits if language in k.supported_languages]

        return kits

    async def get_kit(self, framework: str) -> StarterKit | None:
        """Get a starter kit by framework."""
        return self._kits.get(framework)

    async def get_template(
        self,
        framework: str,
        template_id: UUID,
    ) -> CodeTemplate | ConfigTemplate | DocumentTemplate | None:
        """Get a specific template from a kit."""
        kit = self._kits.get(framework)
        if not kit:
            return None

        for template in kit.code_templates:
            if template.id == template_id:
                return template

        for template in kit.config_templates:
            if template.id == template_id:
                return template

        for template in kit.document_templates:
            if template.id == template_id:
                return template

        return None

    async def generate_kit_archive(
        self,
        framework: str,
        language: TemplateLanguage = TemplateLanguage.PYTHON,
        customizations: dict | None = None,
    ) -> bytes:
        """Generate a downloadable ZIP archive of the starter kit."""
        kit = self._kits.get(framework)
        if not kit:
            raise ValueError(f"Starter kit not found: {framework}")

        buffer = BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add README
            readme = self._generate_readme(kit)
            zf.writestr(f"{framework.lower()}_starter_kit/README.md", readme)

            # Add code templates
            for template in kit.code_templates:
                if template.language == language:
                    content = self._apply_customizations(template.content, customizations or {})
                    path = f"{framework.lower()}_starter_kit/src/{template.file_name}"
                    zf.writestr(path, content)

            # Add config templates
            for template in kit.config_templates:
                content = self._apply_customizations(template.content, customizations or {})
                path = f"{framework.lower()}_starter_kit/config/{template.file_name}"
                zf.writestr(path, content)

            # Add document templates
            for template in kit.document_templates:
                content = self._apply_customizations(template.content, customizations or {})
                path = f"{framework.lower()}_starter_kit/docs/{template.file_name}"
                zf.writestr(path, content)

            # Add manifest
            manifest = {
                "framework": kit.framework,
                "version": kit.version,
                "generated_at": datetime.now(UTC).isoformat(),
                "language": language.value,
                "requirements_covered": kit.requirements_covered,
            }
            zf.writestr(
                f"{framework.lower()}_starter_kit/manifest.json", json.dumps(manifest, indent=2)
            )

        kit.download_count += 1

        buffer.seek(0)
        return buffer.getvalue()

    def _apply_customizations(self, content: str, customizations: dict) -> str:
        """Apply customizations to template content."""
        for key, value in customizations.items():
            placeholder = f"{{{{ {key} }}}}"
            content = content.replace(placeholder, str(value))
        return content

    def _generate_readme(self, kit: StarterKit) -> str:
        """Generate README for the kit."""
        return f"""# {kit.name}

{kit.description}

## Quick Start

{kit.quick_start}

## Prerequisites

{chr(10).join(f"- {p}" for p in kit.prerequisites)}

## What's Included

### Code Templates
{chr(10).join(f"- `{t.file_name}`: {t.description}" for t in kit.code_templates)}

### Configuration Files
{chr(10).join(f"- `{t.file_name}`: {t.description}" for t in kit.config_templates)}

### Documentation
{chr(10).join(f"- `{t.name}`: {t.description}" for t in kit.document_templates)}

## Requirements Covered

This starter kit addresses the following compliance requirements:

{chr(10).join(f"- {r}" for r in kit.requirements_covered)}

## Version

{kit.version}

---
Generated by ComplianceAgent
"""

