"""Legal text parsing using AI."""

from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from app.models.regulation import Regulation
from app.models.requirement import (
    ObligationType,
    Requirement,
    RequirementCategory,
)


logger = structlog.get_logger()


LEGAL_PARSER_SYSTEM_PROMPT = """You are an expert regulatory compliance analyst specializing in extracting actionable requirements from legal text.

Your task is to parse regulatory documents and extract specific, implementable requirements that software systems must comply with.

For each requirement you identify, extract:

1. **Obligation Type**:
   - MUST: Mandatory requirement (shall, must, required)
   - MUST_NOT: Prohibition (shall not, must not, prohibited)
   - SHOULD: Recommended (should, recommended)
   - SHOULD_NOT: Not recommended (should not)
   - MAY: Optional/permitted (may, can, permitted)

2. **Category**: Classify into one of:
   - data_collection, data_storage, data_processing, data_transfer, data_deletion, data_access
   - consent, notification, documentation, security, audit
   - breach_response, risk_assessment, vendor_management
   - ai_transparency, ai_testing, ai_documentation, human_oversight

3. **Subject**: Who must comply (e.g., "data controllers", "processors", "AI system providers")

4. **Action**: What they must do (specific action required)

5. **Object**: What it applies to (e.g., "personal data", "high-risk AI systems")

6. **Timeframe**: Any deadlines mentioned (e.g., "within 72 hours", "30 days")

7. **Source Text**: The exact text from which this requirement was extracted

8. **Citations**: Article, section, paragraph references

Be precise and conservative. Only extract clear requirements, not general statements.
When uncertain about interpretation, note the uncertainty.

Output your findings as a JSON array of requirements."""


REQUIREMENT_EXTRACTION_PROMPT = """Extract compliance requirements from the following regulatory text.

**Regulation**: {regulation_name}
**Jurisdiction**: {jurisdiction}
**Framework**: {framework}

**Text to analyze**:
{text}

Extract all specific, actionable requirements. For each requirement, provide:
- reference_id: A unique identifier like "REQ-{framework}-001"
- title: Brief title for the requirement
- description: Clear description of what must be done
- obligation_type: MUST, MUST_NOT, SHOULD, SHOULD_NOT, or MAY
- category: The category of requirement
- subject: Who must comply
- action: What action is required
- object: What it applies to (optional)
- data_types: List of data types affected (if applicable)
- processes: List of processes affected (if applicable)
- timeframe: Any deadline or timeframe mentioned
- source_text: The exact source text
- citations: Array of {{article, section, paragraph}}
- confidence: Your confidence score 0.0 to 1.0

Return as JSON array. If no clear requirements found, return empty array."""


class LegalParserService:
    """Service for parsing legal text into structured requirements."""

    def __init__(self):
        self.http_client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(timeout=120.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()

    async def parse_regulation(
        self,
        regulation: Regulation,
        text: str,
    ) -> list[dict[str, Any]]:
        """Parse regulatory text and extract requirements."""
        logger.info(
            "Parsing regulation",
            regulation_id=str(regulation.id),
            regulation_name=regulation.name,
        )

        prompt = REQUIREMENT_EXTRACTION_PROMPT.format(
            regulation_name=regulation.name,
            jurisdiction=regulation.jurisdiction.value,
            framework=regulation.framework.value,
            text=text[:50000],  # Limit text length
        )

        # Call AI API (placeholder - would use Copilot SDK)
        requirements_data = await self._call_ai(prompt)

        logger.info(
            "Extraction complete",
            regulation_id=str(regulation.id),
            requirements_found=len(requirements_data),
        )

        return requirements_data

    async def _call_ai(self, prompt: str) -> list[dict[str, Any]]:
        """Call AI API for parsing. Placeholder for Copilot SDK integration."""
        # TODO: Replace with actual Copilot SDK call
        # For now, return empty list as placeholder
        logger.warning("AI parsing not yet implemented - returning empty requirements")
        return []

    def create_requirement_from_extraction(
        self,
        regulation: Regulation,
        extracted: dict[str, Any],
    ) -> Requirement:
        """Create a Requirement model from extracted data."""
        return Requirement(
            regulation_id=regulation.id,
            reference_id=extracted.get("reference_id", f"REQ-{regulation.framework.value}-{datetime.now(UTC).timestamp()}"),
            title=extracted.get("title", "Untitled Requirement"),
            description=extracted.get("description", ""),
            obligation_type=ObligationType(extracted.get("obligation_type", "must").lower()),
            category=RequirementCategory(extracted.get("category", "other").lower()),
            subject=extracted.get("subject", ""),
            action=extracted.get("action", ""),
            object=extracted.get("object"),
            data_types=extracted.get("data_types", []),
            processes=extracted.get("processes", []),
            systems=extracted.get("systems", []),
            roles=extracted.get("roles", []),
            timeframe=extracted.get("timeframe"),
            deadline_days=extracted.get("deadline_days"),
            source_text=extracted.get("source_text", ""),
            citations=extracted.get("citations", []),
            extraction_confidence=extracted.get("confidence", 0.0),
            extracted_at=datetime.now(UTC),
            metadata=extracted.get("metadata", {}),
        )


# Singleton instance
legal_parser_service = LegalParserService()
