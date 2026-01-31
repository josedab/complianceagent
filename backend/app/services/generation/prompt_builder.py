"""Builder pattern for constructing AI prompts."""

from dataclasses import dataclass
from typing import Any


@dataclass
class PromptSection:
    """A section of a prompt with heading and content."""
    heading: str
    content: str
    priority: int = 0  # Higher priority sections appear first


class PromptBuilder:
    """Builder for constructing maintainable AI prompts.
    
    Example usage:
        prompt = (
            PromptBuilder()
            .with_system_context("code generation", "Python")
            .with_requirement(requirement_dict)
            .with_gaps(gaps_list)
            .with_code_context(existing_code)
            .with_output_format({"files": "list", "tests": "list"})
            .build()
        )
    """

    def __init__(self):
        self._sections: list[PromptSection] = []
        self._system_context: str | None = None
        self._output_format: dict[str, Any] | None = None

    def with_system_context(
        self,
        task: str,
        language: str | None = None,
        style_guide: str | None = None,
    ) -> "PromptBuilder":
        """Set the system context describing the AI's role."""
        parts = [f"You are an expert software engineer performing {task}."]

        if language:
            parts.append(f"Target language: {language}.")
        if style_guide:
            parts.append(f"Follow this style guide: {style_guide}")

        self._system_context = " ".join(parts)
        return self

    def with_requirement(
        self,
        requirement: dict[str, Any],
        include_regulation: bool = True,
    ) -> "PromptBuilder":
        """Add requirement context to the prompt."""
        lines = [
            f"**Title**: {requirement.get('title', 'Untitled')}",
            f"**Description**: {requirement.get('description', 'No description')}",
            f"**Reference ID**: {requirement.get('reference_id', 'N/A')}",
        ]

        if include_regulation and requirement.get("regulation_name"):
            lines.append(f"**Regulation**: {requirement['regulation_name']}")

        if requirement.get("category"):
            lines.append(f"**Category**: {requirement['category']}")

        if requirement.get("data_types"):
            lines.append(f"**Data Types**: {', '.join(requirement['data_types'])}")

        if requirement.get("obligation_type"):
            lines.append(f"**Obligation**: {requirement['obligation_type'].upper()}")

        self._sections.append(PromptSection(
            heading="Requirement",
            content="\n".join(lines),
            priority=100,
        ))
        return self

    def with_gaps(self, gaps: list[dict[str, Any]]) -> "PromptBuilder":
        """Add compliance gaps to address."""
        if not gaps:
            return self

        lines = []
        for i, gap in enumerate(gaps, 1):
            severity = gap.get("severity", "unknown").upper()
            description = gap.get("description", "No description")
            lines.append(f"{i}. [{severity}] {description}")

            if gap.get("location"):
                lines.append(f"   Location: {gap['location']}")
            if gap.get("recommendation"):
                lines.append(f"   Recommendation: {gap['recommendation']}")

        self._sections.append(PromptSection(
            heading="Compliance Gaps to Address",
            content="\n".join(lines),
            priority=90,
        ))
        return self

    def with_code_context(
        self,
        code_files: dict[str, str],
        max_files: int = 5,
        max_lines_per_file: int = 100,
    ) -> "PromptBuilder":
        """Add existing code context."""
        if not code_files:
            return self

        lines = []
        for path, content in list(code_files.items())[:max_files]:
            # Truncate long files
            content_lines = content.split("\n")
            if len(content_lines) > max_lines_per_file:
                content = "\n".join(content_lines[:max_lines_per_file])
                content += f"\n... ({len(content_lines) - max_lines_per_file} more lines)"

            # Detect language from extension
            ext = path.rsplit(".", 1)[-1] if "." in path else ""
            lang = self._extension_to_language(ext)

            lines.append(f"### {path}")
            lines.append(f"```{lang}")
            lines.append(content)
            lines.append("```")
            lines.append("")

        self._sections.append(PromptSection(
            heading="Existing Code Context",
            content="\n".join(lines),
            priority=70,
        ))
        return self

    def with_codebase_structure(self, structure: str) -> "PromptBuilder":
        """Add codebase structure information."""
        self._sections.append(PromptSection(
            heading="Codebase Structure",
            content=structure,
            priority=60,
        ))
        return self

    def with_constraints(self, constraints: list[str]) -> "PromptBuilder":
        """Add constraints or guidelines for the output."""
        if not constraints:
            return self

        lines = [f"- {c}" for c in constraints]
        self._sections.append(PromptSection(
            heading="Constraints",
            content="\n".join(lines),
            priority=50,
        ))
        return self

    def with_output_format(self, format_spec: dict[str, Any]) -> "PromptBuilder":
        """Specify the expected output format."""
        self._output_format = format_spec
        return self

    def with_custom_section(
        self,
        heading: str,
        content: str,
        priority: int = 40,
    ) -> "PromptBuilder":
        """Add a custom section to the prompt."""
        self._sections.append(PromptSection(
            heading=heading,
            content=content,
            priority=priority,
        ))
        return self

    def build(self) -> str:
        """Build the final prompt string."""
        parts = []

        # Add system context first
        if self._system_context:
            parts.append(self._system_context)
            parts.append("")

        # Sort sections by priority (descending) and add them
        sorted_sections = sorted(self._sections, key=lambda s: -s.priority)
        for section in sorted_sections:
            parts.append(f"## {section.heading}")
            parts.append(section.content)
            parts.append("")

        # Add output format specification
        if self._output_format:
            parts.append("## Expected Output Format")
            parts.append("Return a JSON object with the following structure:")
            parts.append("```json")
            parts.append(self._format_output_spec(self._output_format))
            parts.append("```")

        return "\n".join(parts).strip()

    @staticmethod
    def _extension_to_language(ext: str) -> str:
        """Map file extension to language for code blocks."""
        mapping = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "jsx": "javascript",
            "java": "java",
            "go": "go",
            "rs": "rust",
            "rb": "ruby",
            "cs": "csharp",
            "cpp": "cpp",
            "c": "c",
            "h": "c",
            "hpp": "cpp",
            "sql": "sql",
            "sh": "bash",
            "yml": "yaml",
            "yaml": "yaml",
            "json": "json",
            "md": "markdown",
            "html": "html",
            "css": "css",
        }
        return mapping.get(ext.lower(), ext)

    @staticmethod
    def _format_output_spec(spec: dict[str, Any], indent: int = 2) -> str:
        """Format output specification as JSON-like structure."""
        import json
        return json.dumps(spec, indent=indent)


# Pre-built prompt templates for common tasks
class CompliancePrompts:
    """Factory for common compliance-related prompts."""

    @staticmethod
    def code_generation(
        requirement: dict[str, Any],
        gaps: list[dict[str, Any]],
        existing_code: dict[str, str],
        language: str,
        style_guide: str | None = None,
    ) -> str:
        """Build prompt for code generation task."""
        return (
            PromptBuilder()
            .with_system_context("compliance code generation", language, style_guide)
            .with_requirement(requirement)
            .with_gaps(gaps)
            .with_code_context(existing_code)
            .with_constraints([
                "Follow existing codebase patterns and conventions",
                "Include compliance comments with regulation citations",
                "Include comprehensive tests for new code",
                "Make minimally invasive changes",
                "Document all changes thoroughly",
            ])
            .with_output_format({
                "files": [{"path": "string", "operation": "create|modify", "content": "string"}],
                "tests": [{"path": "string", "test_type": "unit|integration", "content": "string"}],
                "documentation": "markdown string",
                "compliance_comments": [{"file": "string", "line": "number", "comment": "string"}],
                "pr_title": "string",
                "pr_body": "markdown string",
                "confidence": "0.0 to 1.0",
                "warnings": ["string"],
            })
            .build()
        )

    @staticmethod
    def requirement_analysis(
        text: str,
        regulation_name: str,
        jurisdiction: str,
        framework: str,
    ) -> str:
        """Build prompt for requirement extraction task."""
        return (
            PromptBuilder()
            .with_system_context("regulatory requirement extraction")
            .with_custom_section("Regulatory Context", f"""
**Regulation**: {regulation_name}
**Jurisdiction**: {jurisdiction}
**Framework**: {framework}
""", priority=100)
            .with_custom_section("Legal Text to Analyze", text[:10000], priority=90)
            .with_constraints([
                "Extract all actionable requirements from the text",
                "Identify obligation type (must, should, may)",
                "Categorize by compliance domain",
                "Note applicable data types and processes",
                "Provide confidence scores for each extraction",
            ])
            .with_output_format({
                "requirements": [{
                    "reference_id": "string",
                    "title": "string",
                    "description": "string",
                    "obligation_type": "must|should|may",
                    "category": "string",
                    "data_types": ["string"],
                    "processes": ["string"],
                    "source_text": "string",
                    "confidence": "0.0 to 1.0",
                }]
            })
            .build()
        )

    @staticmethod
    def code_mapping(
        requirement: dict[str, Any],
        codebase_structure: str,
        sample_files: dict[str, str],
        languages: list[str],
    ) -> str:
        """Build prompt for requirement-to-code mapping task."""
        return (
            PromptBuilder()
            .with_system_context("compliance code analysis", ", ".join(languages))
            .with_requirement(requirement)
            .with_codebase_structure(codebase_structure)
            .with_code_context(sample_files)
            .with_constraints([
                "Identify all code locations relevant to the requirement",
                "Detect existing implementations that satisfy the requirement",
                "Identify gaps where compliance is missing",
                "Assess severity of each gap",
                "Provide effort estimates for remediation",
            ])
            .with_output_format({
                "affected_files": ["string"],
                "existing_implementations": [{"file": "string", "description": "string"}],
                "gaps": [{"severity": "critical|major|minor", "description": "string", "location": "string"}],
                "data_flows": [{"from": "string", "to": "string", "data_type": "string"}],
                "estimated_effort_hours": "number",
                "confidence": "0.0 to 1.0",
            })
            .build()
        )
