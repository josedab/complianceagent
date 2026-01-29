#!/usr/bin/env python3
"""ComplianceAgent CI/CD compliance checker.

This script runs as part of the GitHub Action to scan code for compliance issues.
"""

import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml


# Severity levels
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2, "hint": 3}


class ComplianceChecker:
    """Compliance checker for CI/CD pipelines."""

    def __init__(self):
        self.api_url = os.environ.get("COMPLIANCEAGENT_API_URL", "https://api.complianceagent.ai")
        self.api_key = os.environ.get("COMPLIANCEAGENT_API_KEY", "")
        self.regulations = os.environ.get("REGULATIONS", "GDPR,CCPA,HIPAA").split(",")
        self.fail_on_severity = os.environ.get("FAIL_ON_SEVERITY", "error")
        self.scan_paths = os.environ.get("SCAN_PATHS", "**/*.py,**/*.ts,**/*.js").split(",")
        self.exclude_paths = os.environ.get("EXCLUDE_PATHS", "**/node_modules/**").split(",")
        self.output_format = os.environ.get("OUTPUT_FORMAT", "sarif")
        self.incremental = os.environ.get("INCREMENTAL", "true") == "true"
        self.changed_files = os.environ.get("CHANGED_FILES", "").split(",") if os.environ.get("CHANGED_FILES") else []
        self.config_file = os.environ.get("CONFIG_FILE", ".complianceagent.yml")

        self.issues: list[dict] = []
        self.files_scanned = 0
        self.load_config()

    def load_config(self):
        """Load configuration from .complianceagent.yml if present."""
        if Path(self.config_file).exists():
            with open(self.config_file) as f:
                config = yaml.safe_load(f)
                if config:
                    self.regulations = config.get("regulations", self.regulations)
                    self.fail_on_severity = config.get("fail_on_severity", self.fail_on_severity)
                    self.scan_paths = config.get("scan_paths", self.scan_paths)
                    self.exclude_paths = config.get("exclude_paths", self.exclude_paths)
                    print(f"✓ Loaded config from {self.config_file}")

    def get_files_to_scan(self) -> list[str]:
        """Get list of files to scan based on configuration."""
        files = set()

        # If incremental and we have changed files, only scan those
        if self.incremental and self.changed_files and self.changed_files[0]:
            for f in self.changed_files:
                if Path(f).exists():
                    files.add(f)
            print(f"Incremental scan: {len(files)} changed files")
        else:
            # Full scan based on patterns
            for pattern in self.scan_paths:
                pattern = pattern.strip()
                for f in glob.glob(pattern, recursive=True):
                    files.add(f)

        # Apply exclusions
        excluded = set()
        for pattern in self.exclude_paths:
            pattern = pattern.strip()
            for f in glob.glob(pattern, recursive=True):
                excluded.add(f)

        files = files - excluded
        return sorted(files)

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
        }
        ext = Path(filepath).suffix.lower()
        return ext_map.get(ext, "unknown")

    def analyze_file_local(self, filepath: str, content: str) -> list[dict]:
        """Perform local pattern-based analysis for offline mode or fallback."""
        issues = []
        lines = content.split("\n")
        language = self.detect_language(filepath)

        # Common compliance patterns
        patterns = [
            {
                "pattern": r"(log|print|console\.log|logger)\s*\([^)]*\b(email|password|ssn|credit_card|phone)\b",
                "code": "GDPR-LOG-001",
                "message": "Potential PII being logged",
                "severity": "error",
                "regulation": "GDPR",
                "article": "Article 32",
            },
            {
                "pattern": r"(store|save|write)\s*\([^)]*\b(password|ssn|credit_card)\b[^)]*\)(?!.*encrypt)",
                "code": "GDPR-ENC-001",
                "message": "PII may be stored without encryption",
                "severity": "warning",
                "regulation": "GDPR",
                "article": "Article 32",
            },
            {
                "pattern": r"\beval\s*\(",
                "code": "SEC-EVAL-001",
                "message": "eval() is a security risk",
                "severity": "error",
                "regulation": "Security",
                "article": "Best Practice",
            },
            {
                "pattern": r"(diagnosis|treatment|prescription|medical_record|health_info|patient)\b(?!.*encrypt|.*protected)",
                "code": "HIPAA-PHI-001",
                "message": "Protected Health Information (PHI) may be unprotected",
                "severity": "error",
                "regulation": "HIPAA",
                "article": "45 CFR 164.312",
            },
            {
                "pattern": r"(model\.predict|classifier|neural_network|deep_learning)\s*\(",
                "code": "EUAI-DOC-001",
                "message": "AI/ML model usage detected - ensure proper documentation",
                "severity": "warning",
                "regulation": "EU AI Act",
                "article": "Article 11",
            },
            {
                "pattern": r"(automated_decision|auto_reject|auto_approve)\s*\([^)]*\)(?!.*explain)",
                "code": "EUAI-TRA-001",
                "message": "Automated decision without explanation mechanism",
                "severity": "error",
                "regulation": "EU AI Act",
                "article": "Article 13",
            },
            {
                "pattern": r"(delete|update|modify)\s*\([^)]*\b(user|account|record)\b[^)]*\)(?!.*audit|.*log)",
                "code": "SOX-AUD-001",
                "message": "Data modification without audit logging",
                "severity": "warning",
                "regulation": "SOX",
                "article": "Section 802",
            },
            {
                "pattern": r"(sell|share|monetize)\s*\([^)]*\b(user|consumer|personal)\b[^)]*data",
                "code": "CCPA-OPT-001",
                "message": "Data sale/sharing without opt-out check",
                "severity": "error",
                "regulation": "CCPA",
                "article": "Section 1798.120",
            },
        ]

        # Filter patterns by enabled regulations
        active_patterns = [
            p for p in patterns
            if p["regulation"] in self.regulations or p["regulation"] == "Security"
        ]

        for i, line in enumerate(lines):
            for p in active_patterns:
                if re.search(p["pattern"], line, re.IGNORECASE):
                    issues.append({
                        "file": filepath,
                        "line": i + 1,
                        "column": 1,
                        "end_line": i + 1,
                        "end_column": len(line),
                        "code": p["code"],
                        "message": p["message"],
                        "severity": p["severity"],
                        "regulation": p["regulation"],
                        "article": p["article"],
                        "source_line": line.strip()[:100],
                    })

        return issues

    async def analyze_file_api(self, filepath: str, content: str) -> list[dict]:
        """Analyze file using ComplianceAgent API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/v1/ide/analyze",
                    json={
                        "uri": filepath,
                        "content": content,
                        "language": self.detect_language(filepath),
                        "regulations": self.regulations,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                issues = []
                for diag in data.get("diagnostics", []):
                    issues.append({
                        "file": filepath,
                        "line": diag["range"]["start"]["line"] + 1,
                        "column": diag["range"]["start"]["character"] + 1,
                        "end_line": diag["range"]["end"]["line"] + 1,
                        "end_column": diag["range"]["end"]["character"] + 1,
                        "code": diag["code"],
                        "message": diag["message"],
                        "severity": diag["severity"],
                        "regulation": diag.get("regulation"),
                        "article": diag.get("article_reference"),
                    })
                return issues

            except Exception as e:
                print(f"  ⚠ API error for {filepath}: {e}, using local analysis")
                return self.analyze_file_local(filepath, content)

    def analyze_file(self, filepath: str) -> list[dict]:
        """Analyze a file for compliance issues."""
        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"  ⚠ Could not read {filepath}: {e}")
            return []

        # Use local analysis (API call would be async)
        return self.analyze_file_local(filepath, content)

    def run_scan(self) -> dict:
        """Run compliance scan on all files."""
        print("\n🔍 ComplianceAgent Compliance Check")
        print("=" * 50)
        print(f"Regulations: {', '.join(self.regulations)}")
        print(f"Fail on severity: {self.fail_on_severity}")
        print(f"Incremental: {self.incremental}")
        print()

        files = self.get_files_to_scan()
        print(f"📁 Scanning {len(files)} files...")
        print()

        for filepath in files:
            self.files_scanned += 1
            file_issues = self.analyze_file(filepath)
            self.issues.extend(file_issues)
            if file_issues:
                print(f"  ⚠ {filepath}: {len(file_issues)} issue(s)")

        # Count by severity
        counts = {"error": 0, "warning": 0, "info": 0, "hint": 0}
        for issue in self.issues:
            sev = issue.get("severity", "info")
            counts[sev] = counts.get(sev, 0) + 1

        # Determine if check passed
        fail_threshold = SEVERITY_ORDER.get(self.fail_on_severity, 0)
        failed = any(
            SEVERITY_ORDER.get(issue.get("severity", "info"), 3) <= fail_threshold
            for issue in self.issues
        )

        return {
            "files_scanned": self.files_scanned,
            "total_issues": len(self.issues),
            "critical_issues": counts["error"],
            "warning_issues": counts["warning"],
            "info_issues": counts["info"] + counts["hint"],
            "issues": self.issues,
            "passed": not failed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate_sarif(self, results: dict) -> dict:
        """Generate SARIF report format."""
        rules = {}
        rule_results = []

        for issue in results["issues"]:
            rule_id = issue["code"]

            # Add rule if not already present
            if rule_id not in rules:
                rules[rule_id] = {
                    "id": rule_id,
                    "name": rule_id.replace("-", " ").title(),
                    "shortDescription": {"text": issue["message"]},
                    "fullDescription": {"text": issue["message"]},
                    "helpUri": f"https://complianceagent.ai/rules/{rule_id}",
                    "properties": {
                        "regulation": issue.get("regulation", "Unknown"),
                        "article": issue.get("article", "N/A"),
                    },
                    "defaultConfiguration": {
                        "level": "error" if issue["severity"] == "error" else "warning"
                    },
                }

            # Add result
            rule_results.append({
                "ruleId": rule_id,
                "level": "error" if issue["severity"] == "error" else "warning" if issue["severity"] == "warning" else "note",
                "message": {"text": issue["message"]},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": issue["file"]},
                        "region": {
                            "startLine": issue["line"],
                            "startColumn": issue["column"],
                            "endLine": issue.get("end_line", issue["line"]),
                            "endColumn": issue.get("end_column", issue["column"]),
                        },
                    },
                }],
                "properties": {
                    "regulation": issue.get("regulation"),
                    "article": issue.get("article"),
                },
            })

        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "ComplianceAgent",
                        "version": "1.0.0",
                        "informationUri": "https://complianceagent.ai",
                        "rules": list(rules.values()),
                    },
                },
                "results": rule_results,
                "invocations": [{
                    "executionSuccessful": True,
                    "endTimeUtc": results["timestamp"],
                }],
            }],
        }

        return sarif

    def generate_markdown(self, results: dict) -> str:
        """Generate markdown report for PR comment."""
        passed = results["passed"]
        status_emoji = "✅" if passed else "❌"
        status_text = "Passed" if passed else "Failed"

        md = f"""## 🛡️ ComplianceAgent Report

### Status: {status_emoji} {status_text}

| Metric | Count |
|--------|-------|
| Files Scanned | {results['files_scanned']} |
| Total Issues | {results['total_issues']} |
| 🔴 Critical | {results['critical_issues']} |
| 🟡 Warnings | {results['warning_issues']} |
| 🔵 Info | {results['info_issues']} |

**Regulations Checked:** {', '.join(self.regulations)}
"""

        if results["issues"]:
            md += "\n### Issues Found\n\n"

            # Group by severity
            errors = [i for i in results["issues"] if i["severity"] == "error"]
            warnings = [i for i in results["issues"] if i["severity"] == "warning"]
            infos = [i for i in results["issues"] if i["severity"] not in ["error", "warning"]]

            if errors:
                md += "<details open>\n<summary>🔴 Critical Issues</summary>\n\n"
                for issue in errors[:10]:  # Limit to 10
                    md += f"- **{issue['file']}:{issue['line']}** - {issue['message']}\n"
                    md += f"  - Code: `{issue['code']}` | {issue.get('regulation', 'N/A')} {issue.get('article', '')}\n"
                if len(errors) > 10:
                    md += f"\n... and {len(errors) - 10} more critical issues\n"
                md += "\n</details>\n\n"

            if warnings:
                md += "<details>\n<summary>🟡 Warnings</summary>\n\n"
                for issue in warnings[:10]:
                    md += f"- **{issue['file']}:{issue['line']}** - {issue['message']}\n"
                    md += f"  - Code: `{issue['code']}` | {issue.get('regulation', 'N/A')}\n"
                if len(warnings) > 10:
                    md += f"\n... and {len(warnings) - 10} more warnings\n"
                md += "\n</details>\n\n"

            if infos:
                md += "<details>\n<summary>🔵 Informational</summary>\n\n"
                for issue in infos[:5]:
                    md += f"- **{issue['file']}:{issue['line']}** - {issue['message']}\n"
                if len(infos) > 5:
                    md += f"\n... and {len(infos) - 5} more\n"
                md += "\n</details>\n\n"

        md += f"\n---\n*Scanned at {results['timestamp']}* | [View full report](https://complianceagent.ai)\n"

        return md

    def write_outputs(self, results: dict):
        """Write output files for GitHub Actions."""
        # Write SARIF
        sarif = self.generate_sarif(results)
        with open("compliance-results.sarif", "w") as f:
            json.dump(sarif, f, indent=2)
        print("✓ Generated compliance-results.sarif")

        # Write markdown report
        md = self.generate_markdown(results)
        with open("compliance-report.md", "w") as f:
            f.write(md)
        print("✓ Generated compliance-report.md")

        # Write JSON results
        with open("compliance-results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("✓ Generated compliance-results.json")

        # Write outputs for GitHub Actions
        with open("compliance-outputs.txt", "w") as f:
            f.write(f"total_issues={results['total_issues']}\n")
            f.write(f"critical_issues={results['critical_issues']}\n")
            f.write(f"warning_issues={results['warning_issues']}\n")
            f.write(f"info_issues={results['info_issues']}\n")
            f.write(f"sarif_file=compliance-results.sarif\n")
            f.write(f"passed={'true' if results['passed'] else 'false'}\n")

        # Write failure marker if failed
        if not results["passed"]:
            with open("compliance-failed.txt", "w") as f:
                f.write("Check failed")


def main():
    """Main entry point."""
    checker = ComplianceChecker()
    results = checker.run_scan()

    print()
    print("=" * 50)
    print(f"📊 Results: {results['total_issues']} issues in {results['files_scanned']} files")
    print(f"   🔴 Critical: {results['critical_issues']}")
    print(f"   🟡 Warnings: {results['warning_issues']}")
    print(f"   🔵 Info: {results['info_issues']}")
    print()

    checker.write_outputs(results)

    if results["passed"]:
        print("✅ Compliance check PASSED")
    else:
        print("❌ Compliance check FAILED")

    return 0 if results["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
