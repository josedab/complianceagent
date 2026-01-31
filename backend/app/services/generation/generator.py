"""Code generation service using AI."""

from datetime import UTC, datetime
from typing import Any

import structlog

from app.agents.copilot import CopilotClient
from app.models.codebase import CodebaseMapping, Repository
from app.models.requirement import Requirement


logger = structlog.get_logger()


CODE_GENERATION_SYSTEM_PROMPT = """You are an expert software engineer generating compliance code.

Your task is to generate production-quality code that implements regulatory requirements.

Requirements for generated code:
1. Follow existing codebase patterns and style
2. Include compliance comments with regulation citations
3. Generate comprehensive tests
4. Be minimally invasive to existing code
5. Document all changes clearly

Always include:
- Clear comments explaining the compliance requirement being addressed
- Citation to the specific regulation article/section
- Unit tests verifying the compliance behavior
- Integration test suggestions where applicable"""


CODE_GENERATION_PROMPT = """Generate compliant code to address these compliance gaps.

**Requirement**:
- ID: {requirement_id}
- Title: {requirement_title}
- Description: {requirement_description}
- Regulation: {regulation_name}
- Article: {citations}

**Gaps to Address**:
{gaps}

**Repository Context**:
- Repository: {repository_name}
- Languages: {languages}
- Primary Language: {primary_language}

**Existing Code Context**:
{existing_code}

**Style Guide** (if provided):
{style_guide}

Generate:

1. **files**: Code changes
   - path: file path
   - operation: "create" or "modify"
   - content: full file content (for create) or null
   - diff: unified diff (for modify) or null
   - language: programming language

2. **tests**: Test files
   - path: test file path
   - test_type: "unit", "integration", or "compliance"
   - content: test file content
   - description: what the test verifies

3. **documentation**: Documentation updates (markdown)

4. **compliance_comments**: Comments to add
   - file: file path
   - line: line number (approximate)
   - comment: compliance comment text

5. **pr_title**: Suggested PR title
6. **pr_body**: Suggested PR body (markdown)
7. **warnings**: Any warnings or concerns

Return as JSON."""


class CodeGenerationService:
    """Service for generating compliant code using CopilotClient."""

    def __init__(self, copilot_client: CopilotClient | None = None):
        """Initialize with optional CopilotClient for dependency injection."""
        self._copilot = copilot_client

    async def generate_code(
        self,
        mapping: CodebaseMapping,
        requirement: Requirement,
        repository: Repository,
        existing_code: dict[str, str] | None = None,
        style_guide: str | None = None,
        include_tests: bool = True,
        include_documentation: bool = True,
    ) -> dict[str, Any]:
        """Generate compliant code for a mapping."""
        logger.info(
            "Generating compliant code",
            mapping_id=str(mapping.id),
            requirement_id=str(requirement.id),
            repository=repository.full_name,
        )

        # Call AI for generation with structured data
        result = await self._call_ai(
            requirement=requirement,
            gaps=mapping.gaps or [],
            existing_code=existing_code or {},
            language=repository.primary_language or "python",
            style_guide=style_guide,
        )

        # Filter tests if not requested
        if not include_tests:
            result["tests"] = []

        # Filter documentation if not requested
        if not include_documentation:
            result["documentation"] = None

        # Add metadata
        result["mapping_id"] = str(mapping.id)
        result["requirement_id"] = str(requirement.id)
        result["generated_at"] = datetime.now(UTC).isoformat()

        logger.info(
            "Code generation complete",
            mapping_id=str(mapping.id),
            files_generated=len(result.get("files", [])),
            tests_generated=len(result.get("tests", [])),
        )

        return result

    async def _call_ai(
        self,
        requirement: Requirement,
        gaps: list[dict],
        existing_code: dict[str, str],
        language: str,
        style_guide: str | None = None,
    ) -> dict[str, Any]:
        """Call CopilotClient for code generation."""
        copilot = self._copilot or CopilotClient()

        async with copilot:
            result = await copilot.generate_compliant_code(
                requirement={
                    "reference_id": requirement.reference_id,
                    "title": requirement.title,
                    "description": requirement.description,
                    "regulation_name": requirement.regulation.name if requirement.regulation else "Unknown",
                },
                gaps=gaps,
                existing_code=existing_code,
                language=language,
                style_guide=style_guide,
            )

        logger.debug(
            "AI code generation completed",
            files_count=len(result.get("files", [])),
            confidence=result.get("confidence", 0.0),
        )

        return result

    def _format_gaps(self, gaps: list[dict]) -> str:
        """Format gaps for prompt."""
        lines = []
        for i, gap in enumerate(gaps, 1):
            lines.append(f"{i}. [{gap.get('severity', 'unknown').upper()}] {gap.get('description', 'No description')}")
            if gap.get("file_path"):
                lines.append(f"   Location: {gap['file_path']}")
            if gap.get("suggestion"):
                lines.append(f"   Suggestion: {gap['suggestion']}")
        return "\n".join(lines) or "No specific gaps identified"

    def _format_citations(self, citations: list[dict]) -> str:
        """Format regulation citations."""
        if not citations:
            return "No specific citations"
        parts = []
        for c in citations:
            parts.append(f"{c.get('article', '')} {c.get('section', '')} {c.get('paragraph', '')}".strip())
        return ", ".join(parts)

    def _format_existing_code(self, code: dict[str, str]) -> str:
        """Format existing code context."""
        lines = []
        for path, content in code.items():
            lines.append(f"### {path}\n```\n{content[:3000]}\n```\n")
        return "\n".join(lines) or "No existing code context provided"


# Factory function for dependency injection
def get_code_generation_service(
    copilot_client: CopilotClient | None = None,
) -> CodeGenerationService:
    """Get a CodeGenerationService instance with optional CopilotClient."""
    return CodeGenerationService(copilot_client=copilot_client)


# Default instance for backward compatibility
code_generation_service = CodeGenerationService()
