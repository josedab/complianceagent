"""IDE compliance analyzer for real-time code analysis."""

import re
import time
from typing import Any

import structlog

from app.services.ide.diagnostic import (
    COMPLIANCE_PATTERNS,
    CodeAction,
    ComplianceDiagnostic,
    DiagnosticCategory,
    DiagnosticResult,
    DiagnosticSeverity,
    Position,
    Range,
)


logger = structlog.get_logger()


class IDEComplianceAnalyzer:
    """Analyzes code for compliance issues in real-time."""

    def __init__(
        self,
        enabled_regulations: list[str] | None = None,
        custom_patterns: dict[str, dict] | None = None,
        severity_threshold: DiagnosticSeverity = DiagnosticSeverity.HINT,
    ):
        self.enabled_regulations = enabled_regulations or [
            "GDPR", "CCPA", "HIPAA", "EU AI Act", "SOX"
        ]
        self.custom_patterns = custom_patterns or {}
        self.severity_threshold = severity_threshold
        self._compiled_patterns: dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        all_patterns = {**COMPLIANCE_PATTERNS, **self.custom_patterns}
        for name, config in all_patterns.items():
            if config.get("regulation") in self.enabled_regulations or not config.get("regulation"):
                try:
                    self._compiled_patterns[name] = re.compile(
                        config["pattern"],
                        re.IGNORECASE | re.MULTILINE
                    )
                except re.error as e:
                    logger.warning(f"Invalid pattern {name}: {e}")

    def analyze_document(
        self,
        uri: str,
        content: str,
        language: str | None = None,
        version: int | None = None,
    ) -> DiagnosticResult:
        """Analyze a document for compliance issues.

        Args:
            uri: Document URI
            content: Document content
            language: Programming language (auto-detected if not provided)
            version: Document version for incremental updates

        Returns:
            DiagnosticResult with all found compliance issues
        """
        start_time = time.perf_counter()
        diagnostics: list[ComplianceDiagnostic] = []
        lines = content.split("\n")

        # Detect language from URI if not provided
        if not language:
            language = self._detect_language(uri)

        # Run pattern-based analysis
        pattern_diagnostics = self._analyze_patterns(content, lines)
        diagnostics.extend(pattern_diagnostics)

        # Run language-specific analysis
        lang_diagnostics = self._analyze_language_specific(content, lines, language)
        diagnostics.extend(lang_diagnostics)

        # Filter by severity threshold
        severity_order = [
            DiagnosticSeverity.ERROR,
            DiagnosticSeverity.WARNING,
            DiagnosticSeverity.INFORMATION,
            DiagnosticSeverity.HINT,
        ]
        threshold_idx = severity_order.index(self.severity_threshold)
        diagnostics = [
            d for d in diagnostics
            if severity_order.index(d.severity) <= threshold_idx
        ]

        # Add code actions for fixable issues
        for diagnostic in diagnostics:
            diagnostic.code_actions = self._generate_code_actions(diagnostic, content, lines)

        analysis_time = (time.perf_counter() - start_time) * 1000

        return DiagnosticResult(
            uri=uri,
            version=version,
            diagnostics=diagnostics,
            analysis_time_ms=analysis_time,
            patterns_checked=len(self._compiled_patterns),
            requirements_evaluated=len(diagnostics),
        )

    def _detect_language(self, uri: str) -> str:
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
        for ext, lang in ext_map.items():
            if uri.endswith(ext):
                return lang
        return "unknown"

    def _analyze_patterns(
        self,
        content: str,
        lines: list[str],
    ) -> list[ComplianceDiagnostic]:
        """Analyze content using pre-compiled patterns."""
        diagnostics = []
        all_patterns = {**COMPLIANCE_PATTERNS, **self.custom_patterns}

        for name, pattern in self._compiled_patterns.items():
            config = all_patterns.get(name, {})

            for match in pattern.finditer(content):
                # Calculate line and column positions
                start_pos = match.start()
                end_pos = match.end()

                start_line = content[:start_pos].count("\n")
                start_col = start_pos - content[:start_pos].rfind("\n") - 1
                end_line = content[:end_pos].count("\n")
                end_col = end_pos - content[:end_pos].rfind("\n") - 1

                diagnostic = ComplianceDiagnostic(
                    range=Range(
                        start=Position(line=start_line, character=start_col),
                        end=Position(line=end_line, character=end_col),
                    ),
                    message=config.get("message", f"Compliance pattern '{name}' matched"),
                    severity=config.get("severity", DiagnosticSeverity.WARNING),
                    code=config.get("code", f"COMP-{name.upper()}"),
                    category=config.get("category"),
                    regulation=config.get("regulation"),
                    article_reference=config.get("article_reference"),
                    data={"pattern_name": name, "matched_text": match.group()},
                )
                diagnostics.append(diagnostic)

        return diagnostics

    def _analyze_language_specific(
        self,
        content: str,
        lines: list[str],
        language: str,
    ) -> list[ComplianceDiagnostic]:
        """Run language-specific compliance analysis."""
        diagnostics = []

        if language == "python":
            diagnostics.extend(self._analyze_python(content, lines))
        elif language in ("javascript", "typescript", "javascriptreact", "typescriptreact"):
            diagnostics.extend(self._analyze_javascript(content, lines))
        elif language == "java":
            diagnostics.extend(self._analyze_java(content, lines))

        return diagnostics

    def _analyze_python(self, content: str, lines: list[str]) -> list[ComplianceDiagnostic]:
        """Python-specific compliance analysis."""
        diagnostics = []

        # Check for pickle usage (security risk)
        pickle_pattern = re.compile(r"import\s+pickle|pickle\.(load|loads)\s*\(")
        for i, line in enumerate(lines):
            if pickle_pattern.search(line):
                diagnostics.append(ComplianceDiagnostic(
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line)),
                    ),
                    message="Pickle deserialization can execute arbitrary code. Consider using safer alternatives like JSON.",
                    severity=DiagnosticSeverity.WARNING,
                    code="SEC-PICKLE-001",
                    category=DiagnosticCategory.SECURITY,
                ))

        # Check for SQL injection vulnerabilities
        sql_pattern = re.compile(r'(execute|cursor\.execute)\s*\(\s*[f"\'].*%s.*["\'].*%|format\s*\(')
        for i, line in enumerate(lines):
            if sql_pattern.search(line) and "parameterized" not in line.lower():
                diagnostics.append(ComplianceDiagnostic(
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line)),
                    ),
                    message="Potential SQL injection vulnerability. Use parameterized queries.",
                    severity=DiagnosticSeverity.ERROR,
                    code="SEC-SQL-001",
                    category=DiagnosticCategory.SECURITY,
                ))

        return diagnostics

    def _analyze_javascript(self, content: str, lines: list[str]) -> list[ComplianceDiagnostic]:
        """JavaScript/TypeScript-specific compliance analysis."""
        diagnostics = []

        # Check for eval usage
        eval_pattern = re.compile(r"\beval\s*\(")
        for i, line in enumerate(lines):
            if eval_pattern.search(line):
                diagnostics.append(ComplianceDiagnostic(
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line)),
                    ),
                    message="eval() is a security risk. Consider safer alternatives.",
                    severity=DiagnosticSeverity.ERROR,
                    code="SEC-EVAL-001",
                    category=DiagnosticCategory.SECURITY,
                ))

        # Check for localStorage with sensitive data
        storage_pattern = re.compile(r"localStorage\.(setItem|getItem)\s*\([^)]*\b(token|password|secret|key)\b")
        for i, line in enumerate(lines):
            if storage_pattern.search(line):
                diagnostics.append(ComplianceDiagnostic(
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line)),
                    ),
                    message="Storing sensitive data in localStorage is insecure. Consider httpOnly cookies or secure storage.",
                    severity=DiagnosticSeverity.WARNING,
                    code="SEC-STORAGE-001",
                    category=DiagnosticCategory.SECURITY,
                ))

        return diagnostics

    def _analyze_java(self, content: str, lines: list[str]) -> list[ComplianceDiagnostic]:
        """Java-specific compliance analysis."""
        diagnostics = []

        # Check for hardcoded credentials
        cred_pattern = re.compile(r'(password|secret|apiKey|api_key)\s*=\s*"[^"]+"|\.setPassword\s*\("[^"]+"\)')
        for i, line in enumerate(lines):
            if cred_pattern.search(line):
                diagnostics.append(ComplianceDiagnostic(
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line)),
                    ),
                    message="Hardcoded credentials detected. Use environment variables or secure vault.",
                    severity=DiagnosticSeverity.ERROR,
                    code="SEC-CRED-001",
                    category=DiagnosticCategory.SECURITY,
                ))

        return diagnostics

    def _generate_code_actions(
        self,
        diagnostic: ComplianceDiagnostic,
        content: str,
        lines: list[str],
    ) -> list[CodeAction]:
        """Generate code actions (quick fixes) for a diagnostic."""
        actions = []

        # Generate fix based on diagnostic code
        if diagnostic.code == "GDPR-LOG-001":
            actions.append(CodeAction(
                title="Mask PII in log statement",
                kind="quickfix",
                is_preferred=True,
            ))
            actions.append(CodeAction(
                title="Remove sensitive data from log",
                kind="quickfix",
            ))

        elif diagnostic.code == "SEC-SQL-001":
            actions.append(CodeAction(
                title="Convert to parameterized query",
                kind="quickfix",
                is_preferred=True,
            ))

        elif diagnostic.code == "GDPR-CON-001":
            actions.append(CodeAction(
                title="Add consent verification check",
                kind="quickfix",
                is_preferred=True,
            ))

        elif diagnostic.code == "EUAI-DOC-001":
            actions.append(CodeAction(
                title="Generate AI model documentation template",
                kind="source",
            ))

        # Always add "Learn more" action
        if diagnostic.regulation:
            actions.append(CodeAction(
                title=f"Learn more about {diagnostic.regulation} compliance",
                kind="source",
                command={
                    "command": "complianceAgent.openDocumentation",
                    "arguments": [diagnostic.regulation, diagnostic.article_reference],
                },
            ))

        return actions

    def get_hover_info(
        self,
        uri: str,
        content: str,
        line: int,
        character: int,
    ) -> dict[str, Any] | None:
        """Get compliance hover information for a position.

        Returns detailed compliance information when hovering over flagged code.
        """
        # Analyze the document first
        result = self.analyze_document(uri, content)

        # Find diagnostics that contain this position
        for diagnostic in result.diagnostics:
            if (diagnostic.range.start.line <= line <= diagnostic.range.end.line and
                (line != diagnostic.range.start.line or character >= diagnostic.range.start.character) and
                (line != diagnostic.range.end.line or character <= diagnostic.range.end.character)):

                hover_content = f"**{diagnostic.regulation or 'Compliance'} Issue: {diagnostic.code}**\n\n"
                hover_content += f"{diagnostic.message}\n\n"

                if diagnostic.article_reference:
                    hover_content += f"📖 Reference: {diagnostic.article_reference}\n\n"

                if diagnostic.category:
                    hover_content += f"🏷️ Category: {diagnostic.category.value.replace('_', ' ').title()}\n\n"

                hover_content += f"⚠️ Severity: {diagnostic.severity.value.upper()}"

                return {
                    "contents": {
                        "kind": "markdown",
                        "value": hover_content,
                    }
                }

        return None

    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        message: str,
        severity: DiagnosticSeverity = DiagnosticSeverity.WARNING,
        category: DiagnosticCategory | None = None,
        regulation: str | None = None,
        code: str | None = None,
    ) -> None:
        """Add a custom compliance pattern."""
        self.custom_patterns[name] = {
            "pattern": pattern,
            "message": message,
            "severity": severity,
            "category": category,
            "regulation": regulation,
            "code": code or f"CUSTOM-{name.upper()}",
        }
        # Recompile patterns
        self._compile_patterns()

    def remove_custom_pattern(self, name: str) -> bool:
        """Remove a custom compliance pattern."""
        if name in self.custom_patterns:
            del self.custom_patterns[name]
            self._compile_patterns()
            return True
        return False
