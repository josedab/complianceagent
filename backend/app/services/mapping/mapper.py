"""Codebase mapping service using AI."""

from datetime import UTC, datetime
from typing import Any

import structlog

from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.requirement import Requirement


logger = structlog.get_logger()


MAPPING_SYSTEM_PROMPT = """You are an expert compliance engineer mapping regulatory requirements to code.

Your task is to analyze a codebase and identify:
1. Code that handles regulated data or processes
2. Existing compliance implementations
3. Gaps where requirements are not yet met

Be thorough but avoid false positives. When uncertain, flag for human review."""


MAPPING_PROMPT = """Map this regulatory requirement to the codebase.

**Requirement**:
- ID: {requirement_id}
- Title: {requirement_title}
- Description: {requirement_description}
- Category: {requirement_category}
- Data Types: {data_types}
- Processes: {processes}

**Repository**: {repository_name}
**Languages**: {languages}

**Codebase Structure**:
{codebase_structure}

**Sample Files** (relevant to the requirement):
{sample_files}

Analyze the codebase and provide:

1. **affected_files**: List of files that handle regulated data/processes
   - path: file path
   - relevance: 0.0 to 1.0 relevance score
   - functions: list of relevant functions
   - classes: list of relevant classes

2. **existing_implementations**: Existing compliance code found
   - path: file path
   - description: what it implements
   - coverage: partial or full

3. **gaps**: Compliance gaps identified
   - severity: critical, major, or minor
   - description: what's missing
   - file_path: where it should be implemented (optional)
   - suggestion: how to fix it

4. **data_flows**: Data flow paths affected
   - name: flow name
   - entry_point: where data enters
   - data_touched: what data is processed
   - compliance_status: compliant, partial, or non_compliant

5. **estimated_effort_hours**: Estimated implementation effort
6. **estimated_effort_description**: Human-readable effort description
7. **risk_level**: high, medium, or low
8. **confidence**: Your confidence in this mapping (0.0 to 1.0)

Return as JSON."""


class CodebaseMappingService:
    """Service for mapping requirements to codebases."""

    def __init__(self):
        pass

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

        # Build prompt
        prompt = MAPPING_PROMPT.format(
            requirement_id=requirement.reference_id,
            requirement_title=requirement.title,
            requirement_description=requirement.description,
            requirement_category=requirement.category.value,
            data_types=", ".join(requirement.data_types),
            processes=", ".join(requirement.processes),
            repository_name=repository.full_name,
            languages=", ".join(repository.languages),
            codebase_structure=self._format_structure(codebase_structure),
            sample_files=self._format_sample_files(sample_files or {}),
        )

        # Call AI for mapping (placeholder)
        mapping_result = await self._call_ai(prompt)

        # Create mapping record
        mapping = self._create_mapping(requirement, repository, mapping_result)

        logger.info(
            "Mapping complete",
            requirement_id=str(requirement.id),
            gaps_found=mapping.gap_count,
            confidence=mapping.mapping_confidence,
        )

        return mapping

    async def _call_ai(self, prompt: str) -> dict[str, Any]:
        """Call AI for mapping analysis. Placeholder for Copilot SDK."""
        # TODO: Implement actual Copilot SDK call
        logger.warning("AI mapping not yet implemented - returning placeholder")
        return {
            "affected_files": [],
            "existing_implementations": [],
            "gaps": [],
            "data_flows": [],
            "estimated_effort_hours": 8.0,
            "estimated_effort_description": "Requires manual analysis",
            "risk_level": "medium",
            "confidence": 0.0,
        }

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
        """Format codebase structure for prompt."""
        lines = []
        for path in structure:
            lines.append(f"- {path}")
        return "\n".join(lines[:100])  # Limit

    def _format_sample_files(self, files: dict[str, str]) -> str:
        """Format sample files for prompt."""
        lines = []
        for path, content in files.items():
            lines.append(f"### {path}\n```\n{content[:2000]}\n```\n")
        return "\n".join(lines)

    def _extract_functions(self, affected_files: list[dict]) -> list[dict]:
        """Extract function info from affected files."""
        functions = []
        for f in affected_files:
            for func in f.get("functions", []):
                functions.append({
                    "file": f.get("path"),
                    "name": func,
                })
        return functions

    def _extract_classes(self, affected_files: list[dict]) -> list[dict]:
        """Extract class info from affected files."""
        classes = []
        for f in affected_files:
            for cls in f.get("classes", []):
                classes.append({
                    "file": f.get("path"),
                    "name": cls,
                })
        return classes


# Singleton instance
codebase_mapping_service = CodebaseMappingService()
