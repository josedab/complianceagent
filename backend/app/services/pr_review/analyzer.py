"""PR Analyzer - Phase 1: Analyzes PR diffs for compliance-relevant code changes."""

import re
import time
from typing import Any
from uuid import uuid4

import structlog

from app.services.github.client import GitHubClient
from app.services.pr_review.models import (
    ComplianceViolation,
    FileDiff,
    PRAnalysisResult,
    ViolationSeverity,
)


logger = structlog.get_logger()


# Compliance-relevant patterns to detect in code changes
COMPLIANCE_PATTERNS = {
    # GDPR / Privacy patterns
    "personal_data_collection": {
        "pattern": r"(email|phone|address|ssn|social_security|date_of_birth|dob|passport|driver.?license)",
        "message": "Code handles personal data that may require GDPR/CCPA compliance",
        "severity": ViolationSeverity.HIGH,
        "regulation": "GDPR",
        "article": "Article 5, 6",
        "category": "data_collection",
    },
    "consent_missing": {
        "pattern": r"(collect|store|process).*?(user|customer|client).*?(data|info|information)(?!.*consent)",
        "message": "Data processing without explicit consent verification",
        "severity": ViolationSeverity.HIGH,
        "regulation": "GDPR",
        "article": "Article 7",
        "category": "consent",
    },
    "data_retention": {
        "pattern": r"(delete|remove|purge|expire|retention|ttl).*?(user|customer|personal|pii)",
        "message": "Data retention/deletion logic - ensure compliance with retention policies",
        "severity": ViolationSeverity.MEDIUM,
        "regulation": "GDPR",
        "article": "Article 17",
        "category": "data_deletion",
    },
    "cross_border_transfer": {
        "pattern": r"(transfer|send|export|replicate).*?(data|user|customer).*?(region|country|international|overseas|eu|us|china)",
        "message": "Cross-border data transfer detected - may require SCCs or adequacy decisions",
        "severity": ViolationSeverity.HIGH,
        "regulation": "GDPR",
        "article": "Chapter V",
        "category": "data_transfer",
    },
    # HIPAA patterns
    "phi_handling": {
        "pattern": r"(patient|medical|health|diagnosis|treatment|prescription|insurance_id|mrn|medical_record)",
        "message": "Protected Health Information (PHI) handling detected - HIPAA compliance required",
        "severity": ViolationSeverity.CRITICAL,
        "regulation": "HIPAA",
        "article": "45 CFR 164",
        "category": "data_processing",
    },
    "healthcare_logging": {
        "pattern": r"(log|audit|track).*?(patient|medical|health|phi|hipaa)",
        "message": "Healthcare data logging - ensure audit trail meets HIPAA requirements",
        "severity": ViolationSeverity.MEDIUM,
        "regulation": "HIPAA",
        "article": "45 CFR 164.312(b)",
        "category": "audit",
    },
    # PCI-DSS patterns
    "card_data": {
        "pattern": r"(credit.?card|card.?number|cvv|cvc|pan|expir.*?(date|month|year)|cardholder)",
        "message": "Payment card data handling - PCI-DSS compliance required",
        "severity": ViolationSeverity.CRITICAL,
        "regulation": "PCI-DSS",
        "article": "Requirement 3, 4",
        "category": "data_processing",
    },
    "payment_logging": {
        "pattern": r"(log|print|console|debug).*?(card|payment|cvv|pan|credit)",
        "message": "Payment data in logs - PCI-DSS violation risk",
        "severity": ViolationSeverity.CRITICAL,
        "regulation": "PCI-DSS",
        "article": "Requirement 3.2",
        "category": "audit",
    },
    # EU AI Act patterns
    "ai_model_training": {
        "pattern": r"(train|fit|fine.?tune|learn).*?(model|neural|network|ai|ml|classifier|predictor)",
        "message": "AI model training detected - may require EU AI Act documentation",
        "severity": ViolationSeverity.MEDIUM,
        "regulation": "EU AI Act",
        "article": "Article 10",
        "category": "ai_documentation",
    },
    "ai_decision_making": {
        "pattern": r"(predict|classify|recommend|score|rank|decide).*?(user|customer|application|loan|credit|employment|hiring)",
        "message": "Automated decision-making affecting individuals - human oversight may be required",
        "severity": ViolationSeverity.HIGH,
        "regulation": "EU AI Act",
        "article": "Article 14",
        "category": "human_oversight",
    },
    "biometric_processing": {
        "pattern": r"(face|facial|fingerprint|voice|iris|retina|biometric|recognition)",
        "message": "Biometric data processing - strict compliance requirements apply",
        "severity": ViolationSeverity.CRITICAL,
        "regulation": "EU AI Act",
        "article": "Article 5",
        "category": "data_processing",
    },
    # Security patterns
    "hardcoded_secrets": {
        "pattern": r"(password|secret|api.?key|token|credential)\s*=\s*['\"][^'\"]{8,}['\"]",
        "message": "Potential hardcoded secret detected - use environment variables or vault",
        "severity": ViolationSeverity.CRITICAL,
        "regulation": None,
        "article": None,
        "category": "security",
    },
    "sql_injection": {
        "pattern": r"(execute|query|raw)\s*\([^)]*['\"].*?\+.*?['\"]|f['\"].*?(SELECT|INSERT|UPDATE|DELETE).*?\{",
        "message": "Potential SQL injection vulnerability - use parameterized queries",
        "severity": ViolationSeverity.CRITICAL,
        "regulation": None,
        "article": None,
        "category": "security",
    },
    "insecure_crypto": {
        "pattern": r"(md5|sha1|des|rc4|ecb)\s*\(|hashlib\.(md5|sha1)\(",
        "message": "Weak cryptographic algorithm detected - use stronger alternatives",
        "severity": ViolationSeverity.HIGH,
        "regulation": None,
        "article": None,
        "category": "security",
    },
    # SOX patterns
    "financial_calculation": {
        "pattern": r"(revenue|profit|loss|balance|ledger|journal|debit|credit|accrual|depreciation)",
        "message": "Financial calculation logic - SOX compliance requires audit trail",
        "severity": ViolationSeverity.MEDIUM,
        "regulation": "SOX",
        "article": "Section 404",
        "category": "audit",
    },
}


class PRAnalyzer:
    """Analyzes PR diffs for compliance violations."""

    def __init__(
        self,
        github_client: GitHubClient | None = None,
        enabled_regulations: list[str] | None = None,
        custom_patterns: dict[str, dict] | None = None,
    ):
        self.github_client = github_client
        self.enabled_regulations = enabled_regulations or [
            "GDPR", "CCPA", "HIPAA", "PCI-DSS", "EU AI Act", "SOX"
        ]
        self.custom_patterns = custom_patterns or {}
        self._compiled_patterns: dict[str, tuple[re.Pattern, dict]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        all_patterns = {**COMPLIANCE_PATTERNS, **self.custom_patterns}
        for name, config in all_patterns.items():
            regulation = config.get("regulation")
            if regulation is None or regulation in self.enabled_regulations:
                try:
                    compiled = re.compile(config["pattern"], re.IGNORECASE | re.MULTILINE)
                    self._compiled_patterns[name] = (compiled, config)
                except re.error as e:
                    logger.warning(f"Invalid pattern {name}: {e}")

    async def analyze_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        access_token: str | None = None,
    ) -> PRAnalysisResult:
        """Analyze a PR for compliance violations.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            access_token: GitHub access token
            
        Returns:
            PRAnalysisResult with all violations found
        """
        start_time = time.perf_counter()
        
        async with GitHubClient(access_token=access_token) as client:
            # Get PR details
            pr_data = await self._get_pr_details(client, owner, repo, pr_number)
            files = await self._get_pr_files(client, owner, repo, pr_number)
            
            violations: list[ComplianceViolation] = []
            file_diffs: list[FileDiff] = []
            total_additions = 0
            total_deletions = 0
            
            for file_data in files:
                file_diff = self._parse_file_diff(file_data)
                file_diffs.append(file_diff)
                total_additions += file_diff.additions
                total_deletions += file_diff.deletions
                
                # Analyze file if it has a patch (changes)
                if file_diff.patch:
                    file_violations = self._analyze_diff(file_diff)
                    violations.extend(file_violations)
            
            analysis_time = (time.perf_counter() - start_time) * 1000
            
            return PRAnalysisResult(
                id=uuid4(),
                pr_number=pr_number,
                repository=repo,
                owner=owner,
                base_sha=pr_data.get("base", {}).get("sha", ""),
                head_sha=pr_data.get("head", {}).get("sha", ""),
                files_analyzed=len(files),
                total_additions=total_additions,
                total_deletions=total_deletions,
                violations=violations,
                files=file_diffs,
                regulations_checked=self.enabled_regulations,
                analysis_time_ms=analysis_time,
            )

    async def analyze_diff_content(
        self,
        diff_content: str,
        file_path: str = "unknown",
    ) -> list[ComplianceViolation]:
        """Analyze raw diff content for compliance violations.
        
        Useful for webhook-based analysis without full GitHub API access.
        """
        file_diff = FileDiff(
            path=file_path,
            old_path=None,
            status="modified",
            additions=diff_content.count("\n+"),
            deletions=diff_content.count("\n-"),
            patch=diff_content,
            language=self._detect_language(file_path),
        )
        return self._analyze_diff(file_diff)

    async def _get_pr_details(
        self,
        client: GitHubClient,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> dict[str, Any]:
        """Get PR details from GitHub."""
        response = await client._client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        response.raise_for_status()
        return response.json()

    async def _get_pr_files(
        self,
        client: GitHubClient,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> list[dict[str, Any]]:
        """Get files changed in a PR."""
        response = await client._client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
            params={"per_page": 100},
        )
        response.raise_for_status()
        return response.json()

    def _parse_file_diff(self, file_data: dict[str, Any]) -> FileDiff:
        """Parse GitHub file data into FileDiff."""
        path = file_data.get("filename", "")
        return FileDiff(
            path=path,
            old_path=file_data.get("previous_filename"),
            status=file_data.get("status", "modified"),
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            patch=file_data.get("patch", ""),
            language=self._detect_language(path),
        )

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".sql": "sql",
            ".tf": "terraform",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
        }
        for ext, lang in ext_map.items():
            if file_path.lower().endswith(ext):
                return lang
        return "unknown"

    def _analyze_diff(self, file_diff: FileDiff) -> list[ComplianceViolation]:
        """Analyze a file diff for compliance violations."""
        violations: list[ComplianceViolation] = []
        
        if not file_diff.patch:
            return violations
            
        # Parse the patch to extract added/modified lines with their positions
        lines_info = self._parse_patch(file_diff.patch)
        
        for line_info in lines_info:
            line_content = line_info["content"]
            line_number = line_info["new_line"]
            
            # Only analyze added lines (marked with +)
            if not line_info["is_addition"]:
                continue
                
            # Check against all patterns
            for pattern_name, (compiled_pattern, config) in self._compiled_patterns.items():
                matches = list(compiled_pattern.finditer(line_content))
                for match in matches:
                    violation = ComplianceViolation(
                        file_path=file_diff.path,
                        line_start=line_number,
                        line_end=line_number,
                        column_start=match.start(),
                        column_end=match.end(),
                        code=f"{config.get('regulation', 'SEC')}-{pattern_name.upper()[:10]}",
                        message=config.get("message", f"Pattern {pattern_name} matched"),
                        severity=config.get("severity", ViolationSeverity.MEDIUM),
                        regulation=config.get("regulation"),
                        article_reference=config.get("article"),
                        category=config.get("category"),
                        evidence=match.group(),
                        confidence=0.85,  # Base confidence, can be refined with AI
                        metadata={
                            "pattern_name": pattern_name,
                            "language": file_diff.language,
                            "line_content": line_content[:200],
                        },
                    )
                    violations.append(violation)
        
        return violations

    def _parse_patch(self, patch: str) -> list[dict[str, Any]]:
        """Parse a unified diff patch into line information.
        
        Returns list of dicts with:
            - content: Line content (without +/- prefix)
            - old_line: Line number in old file (None for additions)
            - new_line: Line number in new file (None for deletions)
            - is_addition: True if line was added
            - is_deletion: True if line was removed
            - is_context: True if line is context (unchanged)
        """
        lines_info = []
        old_line = 0
        new_line = 0
        
        for line in patch.split("\n"):
            # Parse hunk header: @@ -start,count +start,count @@
            hunk_match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if hunk_match:
                old_line = int(hunk_match.group(1))
                new_line = int(hunk_match.group(2))
                continue
            
            if line.startswith("+") and not line.startswith("+++"):
                lines_info.append({
                    "content": line[1:],
                    "old_line": None,
                    "new_line": new_line,
                    "is_addition": True,
                    "is_deletion": False,
                    "is_context": False,
                })
                new_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                lines_info.append({
                    "content": line[1:],
                    "old_line": old_line,
                    "new_line": None,
                    "is_addition": False,
                    "is_deletion": True,
                    "is_context": False,
                })
                old_line += 1
            elif not line.startswith("\\"):  # Ignore "\ No newline at end of file"
                lines_info.append({
                    "content": line[1:] if line.startswith(" ") else line,
                    "old_line": old_line,
                    "new_line": new_line,
                    "is_addition": False,
                    "is_deletion": False,
                    "is_context": True,
                })
                old_line += 1
                new_line += 1
        
        return lines_info

    def add_custom_pattern(
        self,
        name: str,
        pattern: str,
        message: str,
        severity: ViolationSeverity = ViolationSeverity.MEDIUM,
        regulation: str | None = None,
        article: str | None = None,
        category: str | None = None,
    ) -> None:
        """Add a custom compliance pattern."""
        self.custom_patterns[name] = {
            "pattern": pattern,
            "message": message,
            "severity": severity,
            "regulation": regulation,
            "article": article,
            "category": category,
        }
        self._compile_patterns()
