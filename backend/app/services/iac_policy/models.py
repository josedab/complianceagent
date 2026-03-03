"""Multi-Cloud IaC Policy Engine models."""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"


class PolicySeverity(str, Enum):
    """Severity levels for policy violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IaCFormat(str, Enum):
    """Supported IaC configuration formats."""
    TERRAFORM_HCL = "terraform_hcl"
    CLOUDFORMATION = "cloudformation"
    KUBERNETES_YAML = "kubernetes_yaml"
    ARM_TEMPLATE = "arm_template"
    PULUMI = "pulumi"


@dataclass
class IaCViolation:
    """A violation found during IaC scanning."""

    id: UUID = field(default_factory=uuid4)
    rule_id: str = ""
    resource_type: str = ""
    resource_name: str = ""
    provider: CloudProvider = CloudProvider.AWS
    severity: PolicySeverity = PolicySeverity.MEDIUM
    framework: str = ""
    description: str = ""
    remediation: str = ""
    file_path: str = ""
    line_number: int = 0
    # Auto-remediation
    auto_fix_available: bool = False
    auto_fix_diff: str = ""
    # SARIF output fields
    sarif_level: str = "warning"
    fingerprint: str = ""


@dataclass
class PolicyRule:
    """A policy rule for IaC scanning."""

    id: str = ""
    name: str = ""
    provider: CloudProvider = CloudProvider.AWS
    framework: str = ""
    severity: PolicySeverity = PolicySeverity.MEDIUM
    description: str = ""
    pattern: str = ""
    # AST matching config
    resource_type: str = ""
    required_attributes: list[str] = field(default_factory=list)
    forbidden_values: dict[str, list[str]] = field(default_factory=dict)
    # OPA/Rego
    rego_rule: str = ""


@dataclass
class ParsedResource:
    """A resource parsed from IaC configuration."""
    resource_type: str = ""
    resource_name: str = ""
    provider: CloudProvider = CloudProvider.AWS
    file_path: str = ""
    line_number: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)
    raw_block: str = ""


@dataclass
class AutoRemediationPR:
    """Auto-generated remediation PR data."""
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    branch: str = ""
    title: str = ""
    body: str = ""
    files_changed: list[dict[str, str]] = field(default_factory=list)
    violations_fixed: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class IaCScanResult:
    """Result of an IaC scan."""

    id: UUID = field(default_factory=uuid4)
    provider: CloudProvider = CloudProvider.AWS
    iac_format: IaCFormat = IaCFormat.TERRAFORM_HCL
    files_scanned: int = 0
    resources_parsed: int = 0
    violations: list[IaCViolation] = field(default_factory=list)
    pass_count: int = 0
    fail_count: int = 0
    scan_duration_ms: int = 0
    auto_fixes_available: int = 0

    def to_sarif(self) -> dict:
        """Export scan results as SARIF v2.1.0 for GitHub Code Scanning."""
        rules = {}
        results = []

        for v in self.violations:
            if v.rule_id not in rules:
                rules[v.rule_id] = {
                    "id": v.rule_id,
                    "name": v.rule_id.replace("-", ""),
                    "shortDescription": {"text": v.description},
                    "defaultConfiguration": {
                        "level": _severity_to_sarif_level(v.severity),
                    },
                    "properties": {
                        "framework": v.framework,
                        "provider": v.provider.value,
                    },
                }

            results.append({
                "ruleId": v.rule_id,
                "level": _severity_to_sarif_level(v.severity),
                "message": {"text": v.description},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": v.file_path},
                        "region": {"startLine": max(1, v.line_number)},
                    },
                }],
                "fingerprints": {
                    "primaryLocationLineHash": v.fingerprint or str(v.id),
                },
                "fixes": [{
                    "description": {"text": v.remediation},
                }] if v.auto_fix_available else [],
            })

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "ComplianceAgent IaC Scanner",
                        "version": "1.0.0",
                        "informationUri": "https://complianceagent.ai/iac-scanner",
                        "rules": list(rules.values()),
                    },
                },
                "results": results,
            }],
        }

    def to_opa_rego(self) -> str:
        """Export policy rules as OPA/Rego policy."""
        lines = [
            "package complianceagent.iac",
            "",
            "import future.keywords.in",
            "",
        ]

        seen_rules = set()
        for v in self.violations:
            if v.rule_id in seen_rules:
                continue
            seen_rules.add(v.rule_id)

            rule_name = v.rule_id.lower().replace("-", "_")
            lines.extend([
                f"# {v.description}",
                f"deny[msg] {{",
                f'    resource := input.resources[_]',
                f'    resource.type == "{v.resource_type}"',
                f'    # Check for compliance violation: {v.rule_id}',
                f'    not resource.properties.compliant',
                f'    msg := sprintf("{v.rule_id}: %s - {v.description}", [resource.name])',
                f"}}",
                "",
            ])

        return "\n".join(lines)


def _severity_to_sarif_level(severity: PolicySeverity) -> str:
    """Map PolicySeverity to SARIF level."""
    return {
        PolicySeverity.CRITICAL: "error",
        PolicySeverity.HIGH: "error",
        PolicySeverity.MEDIUM: "warning",
        PolicySeverity.LOW: "note",
    }.get(severity, "warning")
