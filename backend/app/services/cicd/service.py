"""CI/CD compliance service for GitHub/GitLab integration."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog

from app.services.cicd.analyzer import CICDComplianceAnalyzer
from app.services.cicd.sarif import SARIFGenerator


logger = structlog.get_logger()


@dataclass
class CICDScanRequest:
    """Request for CI/CD compliance scan."""

    files: list[dict[str, str]]  # List of {path, content}
    regulations: list[str] | None = None
    fail_on_severity: str = "error"  # error, warning, info
    include_ai_fixes: bool = True
    incremental: bool = False
    diff: str | None = None  # Git diff for incremental scans
    repository: str | None = None
    commit_sha: str | None = None
    branch: str | None = None
    pr_number: int | None = None


@dataclass
class CICDScanResult:
    """Result of CI/CD compliance scan."""

    scan_id: str
    passed: bool
    files_analyzed: int
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    by_regulation: dict[str, int]
    issues: list[dict[str, Any]]
    sarif: dict[str, Any] | None
    github_annotations: list[dict[str, Any]] | None
    markdown_summary: str
    scanned_at: datetime


class CICDComplianceService:
    """Service for CI/CD compliance checks."""

    SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}

    def __init__(self):
        self.sarif_generator = SARIFGenerator()

    def _generate_scan_id(self, request: CICDScanRequest) -> str:
        """Generate unique scan ID."""
        content = f"{request.repository}:{request.commit_sha}:{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def run_scan(self, request: CICDScanRequest) -> CICDScanResult:
        """Run compliance scan on provided files.

        Args:
            request: Scan request with files and configuration

        Returns:
            Scan result with issues and reports
        """
        scan_id = self._generate_scan_id(request)
        logger.info(
            "Starting CI/CD compliance scan",
            scan_id=scan_id,
            files_count=len(request.files),
            regulations=request.regulations,
        )

        analyzer = CICDComplianceAnalyzer(
            regulations=request.regulations,
            use_ai_analysis=request.include_ai_fixes,
        )

        # Run analysis
        results = await analyzer.analyze_files(
            files=request.files,
            include_ai_fixes=request.include_ai_fixes,
        )

        issues = results["issues"]

        # Filter to changed lines if incremental
        if request.incremental and request.diff:
            changed_lines = analyzer.parse_diff_for_lines(request.diff)
            issues = analyzer.filter_changed_lines(issues, changed_lines)
            results["total_issues"] = len(issues)
            results["critical_count"] = sum(1 for i in issues if i.get("severity") == "error")
            results["warning_count"] = sum(1 for i in issues if i.get("severity") == "warning")
            results["info_count"] = sum(1 for i in issues if i.get("severity") not in ("error", "warning"))

        # Determine pass/fail
        fail_threshold = self.SEVERITY_ORDER.get(request.fail_on_severity, 0)
        passed = not any(
            self.SEVERITY_ORDER.get(issue.get("severity", "info"), 2) <= fail_threshold
            for issue in issues
        )

        # Generate SARIF
        sarif = self.sarif_generator.generate(
            issues=issues,
            repository=request.repository,
            commit_sha=request.commit_sha,
        )

        # Generate GitHub annotations
        annotations = self.sarif_generator.to_github_annotations(issues)

        # Generate markdown summary
        markdown = self._generate_markdown_summary(
            results=results,
            request=request,
            passed=passed,
            issues=issues,
        )

        return CICDScanResult(
            scan_id=scan_id,
            passed=passed,
            files_analyzed=results["files_analyzed"],
            total_issues=len(issues),
            critical_count=results["critical_count"],
            warning_count=results["warning_count"],
            info_count=results["info_count"],
            by_regulation=results["by_regulation"],
            issues=issues,
            sarif=sarif,
            github_annotations=annotations,
            markdown_summary=markdown,
            scanned_at=datetime.now(UTC),
        )

    def _generate_markdown_summary(
        self,
        results: dict[str, Any],
        request: CICDScanRequest,
        passed: bool,
        issues: list[dict[str, Any]],
    ) -> str:
        """Generate markdown summary for PR comment."""
        status_emoji = "✅" if passed else "❌"
        status_text = "Passed" if passed else "Failed"

        regulations_str = ", ".join(request.regulations or ["All"])

        md = f"""## 🛡️ ComplianceAgent Report

### Status: {status_emoji} {status_text}

| Metric | Count |
|--------|-------|
| Files Analyzed | {results['files_analyzed']} |
| Total Issues | {len(issues)} |
| 🔴 Critical | {results['critical_count']} |
| 🟡 Warnings | {results['warning_count']} |
| 🔵 Info | {results['info_count']} |

**Regulations Checked:** {regulations_str}
"""

        if request.commit_sha:
            md += f"\n**Commit:** `{request.commit_sha[:7]}`"
        if request.branch:
            md += f" on `{request.branch}`"
        md += "\n"

        if issues:
            md += "\n### Issues Found\n\n"

            # Group by severity
            errors = [i for i in issues if i.get("severity") == "error"]
            warnings = [i for i in issues if i.get("severity") == "warning"]
            infos = [i for i in issues if i.get("severity") not in ("error", "warning")]

            if errors:
                md += "<details open>\n<summary>🔴 Critical Issues</summary>\n\n"
                md += "| File | Line | Issue | Regulation |\n"
                md += "|------|------|-------|------------|\n"
                for issue in errors[:15]:
                    file_name = issue["file"].split("/")[-1]
                    msg = issue["message"][:60] + "..." if len(issue["message"]) > 60 else issue["message"]
                    reg = issue.get("regulation", "N/A")
                    md += f"| `{file_name}` | {issue['line']} | {msg} | {reg} |\n"
                if len(errors) > 15:
                    md += f"\n*... and {len(errors) - 15} more critical issues*\n"
                md += "\n</details>\n\n"

            if warnings:
                md += "<details>\n<summary>🟡 Warnings</summary>\n\n"
                md += "| File | Line | Issue | Regulation |\n"
                md += "|------|------|-------|------------|\n"
                for issue in warnings[:10]:
                    file_name = issue["file"].split("/")[-1]
                    msg = issue["message"][:60] + "..." if len(issue["message"]) > 60 else issue["message"]
                    reg = issue.get("regulation", "N/A")
                    md += f"| `{file_name}` | {issue['line']} | {msg} | {reg} |\n"
                if len(warnings) > 10:
                    md += f"\n*... and {len(warnings) - 10} more warnings*\n"
                md += "\n</details>\n\n"

            if infos:
                md += "<details>\n<summary>🔵 Informational</summary>\n\n"
                for issue in infos[:5]:
                    md += f"- `{issue['file']}:{issue['line']}` - {issue['message']}\n"
                if len(infos) > 5:
                    md += f"\n*... and {len(infos) - 5} more*\n"
                md += "\n</details>\n\n"

        # Add by-regulation breakdown
        if results.get("by_regulation"):
            md += "\n### Issues by Regulation\n\n"
            md += "| Regulation | Count |\n"
            md += "|------------|-------|\n"
            for reg, count in sorted(results["by_regulation"].items(), key=lambda x: -x[1]):
                md += f"| {reg} | {count} |\n"

        md += f"\n---\n*Scanned at {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n"

        return md

    async def create_github_check_run(
        self,
        result: CICDScanResult,
        github_token: str,
        owner: str,
        repo: str,
        head_sha: str,
    ) -> dict[str, Any]:
        """Create GitHub Check Run with compliance results.

        This method would integrate with GitHub API to create check runs.
        Currently returns the payload that would be sent.
        """
        conclusion = "success" if result.passed else "failure"

        check_run = {
            "name": "ComplianceAgent",
            "head_sha": head_sha,
            "status": "completed",
            "conclusion": conclusion,
            "completed_at": result.scanned_at.isoformat(),
            "output": {
                "title": f"Compliance Check: {'Passed' if result.passed else 'Failed'}",
                "summary": f"Found {result.total_issues} issues ({result.critical_count} critical, {result.warning_count} warnings)",
                "text": result.markdown_summary,
                "annotations": result.github_annotations,
            },
        }

        return check_run

    def generate_gitlab_report(self, result: CICDScanResult) -> dict[str, Any]:
        """Generate GitLab Code Quality report format."""
        issues = []

        severity_map = {
            "error": "blocker",
            "warning": "major",
            "info": "minor",
            "hint": "info",
        }

        for issue in result.issues:
            issues.append({
                "description": issue.get("message", "Compliance issue"),
                "check_name": issue.get("code", "COMPLIANCE"),
                "fingerprint": hashlib.md5(
                    f"{issue.get('file')}:{issue.get('line')}:{issue.get('code')}".encode()
                ).hexdigest(),
                "severity": severity_map.get(issue.get("severity", "info"), "minor"),
                "location": {
                    "path": issue.get("file", "unknown"),
                    "lines": {
                        "begin": issue.get("line", 1),
                        "end": issue.get("end_line", issue.get("line", 1)),
                    },
                },
                "categories": [issue.get("regulation", "Compliance")],
            })

        return issues
