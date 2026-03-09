"""Codebase mapping service using AI via CopilotClient."""

from datetime import UTC, datetime
from typing import Any

import structlog

from app.agents.copilot import create_copilot_client
from app.core.exceptions import CopilotError
from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.requirement import Requirement


logger = structlog.get_logger()

_FALLBACK_RESPONSE: dict[str, Any] = {
    "affected_files": [],
    "existing_implementations": [],
    "gaps": [],
    "data_flows": [],
    "estimated_effort_hours": 8.0,
    "estimated_effort_description": "AI analysis unavailable — manual review required",
    "risk_level": "medium",
    "confidence": 0.0,
}


class CodebaseMappingService:
    """Service for mapping requirements to codebases using CopilotClient."""

    def __init__(self, copilot_factory=create_copilot_client):
        self._copilot_factory = copilot_factory

    async def map_requirement(
        self,
        requirement: Requirement,
        repository: Repository,
        codebase_structure: dict[str, Any],
        sample_files: dict[str, str] | None = None,
    ) -> CodebaseMapping:
        """Map a requirement to a repository's codebase."""
        logger.info(
            "Mapping requirement to codebase",
            requirement_id=str(requirement.id),
            repository=repository.full_name,
        )

        requirement_dict = {
            "reference_id": requirement.reference_id,
            "title": requirement.title,
            "description": requirement.description,
            "category": requirement.category.value,
            "data_types": requirement.data_types,
            "processes": requirement.processes,
        }
        structure_text = self._format_structure(codebase_structure)

        mapping_result = await self._call_ai(
            requirement_dict=requirement_dict,
            codebase_structure=structure_text,
            sample_files=sample_files or {},
            languages=repository.languages,
        )

        mapping = self._create_mapping(requirement, repository, mapping_result)

        logger.info(
            "Mapping complete",
            requirement_id=str(requirement.id),
            gaps_found=mapping.gap_count,
            confidence=mapping.mapping_confidence,
        )

        return mapping

    async def _call_ai(
        self,
        requirement_dict: dict[str, Any],
        codebase_structure: str,
        sample_files: dict[str, str],
        languages: list[str],
    ) -> dict[str, Any]:
        """Delegate to CopilotClient.map_requirement_to_code() with fallback."""
        try:
            client = self._copilot_factory()
            async with client:
                result = await client.map_requirement_to_code(
                    requirement=requirement_dict,
                    codebase_structure=codebase_structure,
                    sample_files=sample_files,
                    languages=languages,
                )
            if result.get("confidence", 0) > 0:
                return result
            logger.warning("Copilot returned zero-confidence mapping, using fallback")
            return _FALLBACK_RESPONSE
        except CopilotError as exc:
            logger.warning(
                "Copilot mapping failed, returning fallback",
                error=str(exc),
            )
            return _FALLBACK_RESPONSE
        except Exception as exc:
            logger.exception("Unexpected error during AI mapping", error=str(exc))
            return _FALLBACK_RESPONSE

    def _create_mapping(
        self,
        requirement: Requirement,
        repository: Repository,
        result: dict[str, Any],
    ) -> CodebaseMapping:
        """Create a CodebaseMapping from analysis result."""
        gaps = result.get("gaps", [])
        critical = sum(1 for g in gaps if g.get("severity") == "critical")
        major = sum(1 for g in gaps if g.get("severity") == "major")
        minor = sum(1 for g in gaps if g.get("severity") == "minor")

        # Determine compliance status
        if not gaps:
            if result.get("existing_implementations"):
                status = ComplianceStatus.COMPLIANT
            else:
                status = ComplianceStatus.PENDING_REVIEW
        elif critical > 0:
            status = ComplianceStatus.NON_COMPLIANT
        else:
            status = ComplianceStatus.PARTIAL

        return CodebaseMapping(
            repository_id=repository.id,
            requirement_id=requirement.id,
            compliance_status=status,
            affected_files=result.get("affected_files", []),
            affected_functions=self._extract_functions(result.get("affected_files", [])),
            affected_classes=self._extract_classes(result.get("affected_files", [])),
            data_flows=result.get("data_flows", []),
            existing_implementations=result.get("existing_implementations", []),
            gaps=gaps,
            gap_count=len(gaps),
            critical_gaps=critical,
            major_gaps=major,
            minor_gaps=minor,
            estimated_effort_hours=result.get("estimated_effort_hours"),
            estimated_effort_description=result.get("estimated_effort_description"),
            risk_level=result.get("risk_level"),
            mapping_confidence=result.get("confidence", 0.0),
            analyzed_at=datetime.now(UTC),
        )

    def _format_structure(self, structure: dict[str, Any]) -> str:
        """Format codebase structure for the AI prompt."""
        lines = [f"- {path}" for path in list(structure)[:100]]
        return "\n".join(lines)

    def _extract_functions(self, affected_files: list[dict]) -> list[dict]:
        """Extract function info from affected files."""
        functions = []
        for f in affected_files:
            for func in f.get("functions", []):
                functions.append(
                    {
                        "file": f.get("path"),
                        "name": func,
                    }
                )
        return functions

    def _extract_classes(self, affected_files: list[dict]) -> list[dict]:
        """Extract class info from affected files."""
        classes = []
        for f in affected_files:
            for cls in f.get("classes", []):
                classes.append(
                    {
                        "file": f.get("path"),
                        "name": cls,
                    }
                )
        return classes


# Singleton instance
codebase_mapping_service = CodebaseMappingService()
