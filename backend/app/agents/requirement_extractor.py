"""Requirement extraction from regulatory text using AI."""

from typing import Any

import structlog
from opentelemetry import trace

from app.agents.copilot import CopilotClient
from app.models.regulation import Regulation


logger = structlog.get_logger()
tracer = trace.get_tracer("complianceagent.requirement_extractor")


class RequirementExtractor:
    """Extracts requirements from regulatory text using Copilot AI."""

    def __init__(self, copilot: CopilotClient):
        self._copilot = copilot

    async def extract(
        self,
        regulation: Regulation,
        content: str,
    ) -> list[dict[str, Any]]:
        """Extract requirements from regulatory text using AI."""
        with tracer.start_as_current_span(
            "copilot_analyze_legal_text",
            attributes={
                "regulation.name": regulation.name,
                "content.length": len(content),
            },
        ) as span:
            async with self._copilot:
                requirements = await self._copilot.analyze_legal_text(
                    text=content,
                    regulation_name=regulation.name,
                    jurisdiction=regulation.jurisdiction.value,
                    framework=regulation.framework.value,
                )

            span.set_attribute("requirements.extracted_count", len(requirements))
            logger.info(f"Extracted {len(requirements)} requirements")
            return requirements
