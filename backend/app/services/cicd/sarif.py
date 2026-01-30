"""SARIF report generator for CI/CD compliance results."""

from datetime import UTC, datetime
from typing import Any


class SARIFGenerator:
    """Generates SARIF (Static Analysis Results Interchange Format) reports."""

    SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
    SARIF_VERSION = "2.1.0"

    def __init__(
        self,
        tool_name: str = "ComplianceAgent",
        tool_version: str = "1.0.0",
        tool_uri: str = "https://complianceagent.ai",
    ):
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.tool_uri = tool_uri

    def generate(
        self,
        issues: list[dict[str, Any]],
        repository: str | None = None,
        commit_sha: str | None = None,
    ) -> dict[str, Any]:
        """Generate SARIF report from compliance issues.

        Args:
            issues: List of compliance issues with file, line, message, etc.
            repository: Repository identifier
            commit_sha: Git commit SHA

        Returns:
            SARIF report as dictionary
        """
        rules = {}
        results = []

        for issue in issues:
            rule_id = issue.get("code", "UNKNOWN")

            # Build rule if not exists
            if rule_id not in rules:
                rules[rule_id] = self._build_rule(issue)

            # Build result
            results.append(self._build_result(issue))

        sarif = {
            "$schema": self.SARIF_SCHEMA,
            "version": self.SARIF_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.tool_name,
                            "version": self.tool_version,
                            "informationUri": self.tool_uri,
                            "rules": list(rules.values()),
                        },
                    },
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": datetime.now(UTC).isoformat(),
                        }
                    ],
                    "versionControlProvenance": self._build_vcs_info(repository, commit_sha),
                }
            ],
        }

        return sarif

    def _build_rule(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Build SARIF rule definition from issue."""
        rule_id = issue.get("code", "UNKNOWN")
        regulation = issue.get("regulation", "")
        article = issue.get("article_reference", "")

        help_text = f"Compliance issue related to {regulation}"
        if article:
            help_text += f" ({article})"

        return {
            "id": rule_id,
            "name": rule_id.replace("-", " ").title(),
            "shortDescription": {"text": issue.get("message", "Compliance issue")[:100]},
            "fullDescription": {"text": issue.get("message", "Compliance issue")},
            "helpUri": f"{self.tool_uri}/rules/{rule_id}",
            "help": {
                "text": help_text,
                "markdown": f"**{regulation}** compliance rule.\n\n{help_text}",
            },
            "properties": {
                "regulation": regulation,
                "article": article,
                "category": issue.get("category", "compliance"),
                "tags": [regulation, issue.get("category", "compliance")],
            },
            "defaultConfiguration": {
                "level": self._severity_to_sarif_level(issue.get("severity", "warning")),
            },
        }

    def _build_result(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Build SARIF result from issue."""
        rule_id = issue.get("code", "UNKNOWN")
        file_path = issue.get("file", "unknown")
        line = issue.get("line", 1)
        column = issue.get("column", 1)
        end_line = issue.get("end_line", line)
        end_column = issue.get("end_column", column + 1)

        result = {
            "ruleId": rule_id,
            "level": self._severity_to_sarif_level(issue.get("severity", "warning")),
            "message": {"text": issue.get("message", "Compliance issue")},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": line,
                            "startColumn": column,
                            "endLine": end_line,
                            "endColumn": end_column,
                        },
                    },
                }
            ],
            "properties": {
                "regulation": issue.get("regulation"),
                "article": issue.get("article_reference"),
                "confidence": issue.get("confidence", 1.0),
            },
        }

        # Add fix suggestion if available
        if issue.get("fix_code"):
            result["fixes"] = [
                {
                    "description": {"text": "Apply suggested compliance fix"},
                    "artifactChanges": [
                        {
                            "artifactLocation": {"uri": file_path},
                            "replacements": [
                                {
                                    "deletedRegion": {
                                        "startLine": line,
                                        "startColumn": column,
                                        "endLine": end_line,
                                        "endColumn": end_column,
                                    },
                                    "insertedContent": {"text": issue["fix_code"]},
                                }
                            ],
                        }
                    ],
                }
            ]

        # Add related information if available
        if issue.get("related_files"):
            result["relatedLocations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": rf["file"]},
                        "region": {"startLine": rf.get("line", 1)},
                    },
                    "message": {"text": rf.get("message", "Related code")},
                }
                for rf in issue["related_files"]
            ]

        return result

    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            "error": "error",
            "critical": "error",
            "warning": "warning",
            "info": "note",
            "information": "note",
            "hint": "none",
        }
        return mapping.get(severity.lower(), "warning")

    def _build_vcs_info(
        self,
        repository: str | None,
        commit_sha: str | None,
    ) -> list[dict[str, Any]]:
        """Build version control provenance information."""
        if not repository:
            return []

        vcs = {
            "repositoryUri": repository,
        }

        if commit_sha:
            vcs["revisionId"] = commit_sha

        return [vcs]

    def to_github_annotations(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert issues to GitHub check run annotations format."""
        annotations = []

        for issue in issues[:50]:  # GitHub limits to 50 annotations per request
            level = "failure" if issue.get("severity") == "error" else "warning"
            if issue.get("severity") in ("info", "hint", "information"):
                level = "notice"

            annotations.append({
                "path": issue.get("file", "unknown"),
                "start_line": issue.get("line", 1),
                "end_line": issue.get("end_line", issue.get("line", 1)),
                "annotation_level": level,
                "message": issue.get("message", "Compliance issue"),
                "title": f"{issue.get('regulation', 'Compliance')}: {issue.get('code', 'UNKNOWN')}",
                "raw_details": issue.get("article_reference", ""),
            })

        return annotations
