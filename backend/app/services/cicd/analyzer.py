"""CI/CD compliance analyzer for batch file analysis."""

import asyncio
import re
from pathlib import Path
from typing import Any

import structlog

from app.services.ide.analyzer import IDEComplianceAnalyzer
from app.services.ide.copilot_suggestions import CopilotComplianceSuggester


logger = structlog.get_logger()


class CICDComplianceAnalyzer:
    """Analyzer for CI/CD compliance checks on multiple files."""

    def __init__(
        self,
        regulations: list[str] | None = None,
        use_ai_analysis: bool = True,
        parallel_limit: int = 10,
    ):
        self.regulations = regulations or ["GDPR", "CCPA", "HIPAA", "EU AI Act", "SOX"]
        self.use_ai_analysis = use_ai_analysis
        self.parallel_limit = parallel_limit
        self._ide_analyzer = IDEComplianceAnalyzer(enabled_regulations=self.regulations)
        self._ai_suggester = CopilotComplianceSuggester() if use_ai_analysis else None

    def detect_language(self, filepath: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescriptreact",
            ".jsx": "javascriptreact",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
        }
        ext = Path(filepath).suffix.lower()
        return ext_map.get(ext, "unknown")

    async def analyze_file(
        self,
        filepath: str,
        content: str,
        include_ai_fixes: bool = False,
    ) -> list[dict[str, Any]]:
        """Analyze a single file for compliance issues.

        Args:
            filepath: Path to the file
            content: File content
            include_ai_fixes: Whether to generate AI-powered fix suggestions

        Returns:
            List of issues found
        """
        language = self.detect_language(filepath)
        issues = []

        # Run pattern-based analysis
        result = self._ide_analyzer.analyze_document(
            uri=filepath,
            content=content,
            language=language,
        )

        for diag in result.diagnostics:
            issue = {
                "file": filepath,
                "line": diag.range.start.line + 1,
                "column": diag.range.start.character + 1,
                "end_line": diag.range.end.line + 1,
                "end_column": diag.range.end.character + 1,
                "code": diag.code,
                "message": diag.message,
                "severity": diag.severity.value,
                "regulation": diag.regulation,
                "article_reference": diag.article_reference,
                "category": diag.category.value if diag.category else None,
            }

            # Get AI-powered fix if enabled
            if include_ai_fixes and self._ai_suggester:
                try:
                    # Extract the problematic code
                    lines = content.split("\n")
                    start_line = max(0, diag.range.start.line)
                    end_line = min(len(lines), diag.range.end.line + 1)
                    code_snippet = "\n".join(lines[start_line:end_line])

                    fix_result = await self._ai_suggester.generate_quick_fix(
                        code=code_snippet,
                        diagnostic=diag,
                        language=language,
                    )

                    if fix_result.fixed_code != fix_result.original_code:
                        issue["fix_code"] = fix_result.fixed_code
                        issue["fix_explanation"] = fix_result.explanation
                except Exception as e:
                    logger.warning(f"Failed to generate AI fix: {e}")

            issues.append(issue)

        # Run AI deep analysis if enabled
        if self.use_ai_analysis and self._ai_suggester:
            try:
                ai_suggestions = await self._ai_suggester.analyze_code_block(
                    code=content,
                    language=language,
                    regulations=self.regulations,
                )

                for suggestion in ai_suggestions:
                    # Check if this issue was already found by pattern matching
                    existing = any(
                        i["line"] == suggestion.diagnostic.range.start.line + 1 and
                        i["code"] == suggestion.diagnostic.code
                        for i in issues
                    )

                    if not existing:
                        issues.append({
                            "file": filepath,
                            "line": suggestion.diagnostic.range.start.line + 1,
                            "column": suggestion.diagnostic.range.start.character + 1,
                            "end_line": suggestion.diagnostic.range.end.line + 1,
                            "end_column": suggestion.diagnostic.range.end.character + 1,
                            "code": suggestion.diagnostic.code,
                            "message": suggestion.diagnostic.message,
                            "severity": suggestion.diagnostic.severity.value,
                            "regulation": suggestion.diagnostic.regulation,
                            "article_reference": suggestion.diagnostic.article_reference,
                            "category": suggestion.diagnostic.category.value if suggestion.diagnostic.category else None,
                            "fix_code": suggestion.fix_code,
                            "fix_explanation": suggestion.explanation,
                            "ai_generated": True,
                            "confidence": suggestion.confidence,
                        })

            except Exception as e:
                logger.warning(f"AI analysis failed for {filepath}: {e}")

        return issues

    async def analyze_files(
        self,
        files: list[dict[str, str]],
        include_ai_fixes: bool = False,
    ) -> dict[str, Any]:
        """Analyze multiple files for compliance issues.

        Args:
            files: List of dicts with 'path' and 'content' keys
            include_ai_fixes: Whether to generate AI fix suggestions

        Returns:
            Analysis results with issues, counts, etc.
        """
        all_issues = []
        semaphore = asyncio.Semaphore(self.parallel_limit)

        async def analyze_with_limit(file_info: dict) -> list[dict]:
            async with semaphore:
                return await self.analyze_file(
                    filepath=file_info["path"],
                    content=file_info["content"],
                    include_ai_fixes=include_ai_fixes,
                )

        # Analyze files in parallel with limit
        tasks = [analyze_with_limit(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"File analysis error: {result}")
            elif isinstance(result, list):
                all_issues.extend(result)

        # Count by severity
        counts = {
            "error": sum(1 for i in all_issues if i.get("severity") == "error"),
            "warning": sum(1 for i in all_issues if i.get("severity") == "warning"),
            "info": sum(1 for i in all_issues if i.get("severity") in ("info", "information", "hint")),
        }

        # Count by regulation
        by_regulation = {}
        for issue in all_issues:
            reg = issue.get("regulation", "Unknown")
            by_regulation[reg] = by_regulation.get(reg, 0) + 1

        return {
            "files_analyzed": len(files),
            "total_issues": len(all_issues),
            "critical_count": counts["error"],
            "warning_count": counts["warning"],
            "info_count": counts["info"],
            "by_regulation": by_regulation,
            "issues": all_issues,
        }

    def filter_changed_lines(
        self,
        issues: list[dict[str, Any]],
        changed_lines: dict[str, set[int]],
    ) -> list[dict[str, Any]]:
        """Filter issues to only those in changed lines.

        Args:
            issues: All issues found
            changed_lines: Dict mapping file paths to sets of changed line numbers

        Returns:
            Filtered list of issues
        """
        filtered = []
        for issue in issues:
            file_path = issue.get("file", "")
            line = issue.get("line", 0)

            if file_path in changed_lines:
                if line in changed_lines[file_path]:
                    filtered.append(issue)

        return filtered

    def parse_diff_for_lines(self, diff: str) -> dict[str, set[int]]:
        """Parse git diff to extract changed line numbers.

        Args:
            diff: Git diff output

        Returns:
            Dict mapping file paths to sets of changed line numbers
        """
        changed_lines: dict[str, set[int]] = {}
        current_file = None
        current_line = 0

        for line in diff.split("\n"):
            # New file
            if line.startswith("+++ b/"):
                current_file = line[6:]
                changed_lines[current_file] = set()
            # Hunk header
            elif line.startswith("@@"):
                match = re.search(r"\+(\d+)", line)
                if match:
                    current_line = int(match.group(1))
            # Added line
            elif line.startswith("+") and not line.startswith("+++"):
                if current_file:
                    changed_lines[current_file].add(current_line)
                current_line += 1
            # Context line
            elif not line.startswith("-"):
                current_line += 1

        return changed_lines
