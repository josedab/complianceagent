"""Compliance-as-Code Policy Language Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.policy_dsl.models import (
    CompiledPolicy,
    OutputFormat,
    PolicyDefinition,
    PolicyDSLStats,
    PolicySeverity,
    PolicyStatus,
    ValidationResult,
)


logger = structlog.get_logger()

_BUILTIN_POLICIES: list[PolicyDefinition] = [
    PolicyDefinition(
        name="GDPR Consent Required",
        slug="gdpr-consent-required",
        description="Require explicit consent mechanism for personal data processing",
        framework="GDPR",
        severity=PolicySeverity.HIGH,
        status=PolicyStatus.ACTIVE,
        dsl_source='policy "gdpr-consent" {\n  when: data_type == "personal"\n  then: require("consent_mechanism")\n  severity: high\n  article: "Art. 6"\n}',
        conditions=[{"field": "data_type", "operator": "==", "value": "personal"}],
        actions=[{"action": "require", "target": "consent_mechanism"}],
        author="complianceagent",
        created_at=datetime(2026, 1, 15, tzinfo=UTC),
    ),
    PolicyDefinition(
        name="HIPAA PHI Encryption",
        slug="hipaa-phi-encryption",
        description="Encrypt PHI at rest and in transit",
        framework="HIPAA",
        severity=PolicySeverity.CRITICAL,
        status=PolicyStatus.ACTIVE,
        dsl_source='policy "hipaa-encryption" {\n  when: data_type == "phi"\n  then: require("encryption_at_rest"), require("encryption_in_transit")\n  severity: critical\n  article: "§164.312"\n}',
        conditions=[{"field": "data_type", "operator": "==", "value": "phi"}],
        actions=[{"action": "require", "target": "encryption_at_rest"}, {"action": "require", "target": "encryption_in_transit"}],
        author="complianceagent",
        created_at=datetime(2026, 1, 15, tzinfo=UTC),
    ),
    PolicyDefinition(
        name="PCI Card Tokenization",
        slug="pci-card-tokenization",
        description="Card data must be tokenized before storage",
        framework="PCI-DSS",
        severity=PolicySeverity.CRITICAL,
        status=PolicyStatus.ACTIVE,
        dsl_source='policy "pci-tokenize" {\n  when: data_type == "card_number" OR data_type == "pan"\n  then: require("tokenization")\n  severity: critical\n  article: "Req 3"\n}',
        conditions=[{"field": "data_type", "operator": "in", "value": ["card_number", "pan"]}],
        actions=[{"action": "require", "target": "tokenization"}],
        author="complianceagent",
        created_at=datetime(2026, 1, 20, tzinfo=UTC),
    ),
]


class PolicyDSLService:
    """Compliance-as-Code policy language compiler."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._policies: dict[str, PolicyDefinition] = {p.slug: p for p in _BUILTIN_POLICIES}
        self._compilations: dict[str, int] = {}

    async def create_policy(
        self,
        name: str,
        slug: str,
        dsl_source: str,
        framework: str = "",
        severity: str = "medium",
        author: str = "",
    ) -> PolicyDefinition:
        validation = self.validate_dsl(dsl_source)
        if not validation.valid:
            raise ValueError(f"Invalid DSL: {'; '.join(validation.errors)}")

        policy = PolicyDefinition(
            name=name,
            slug=slug,
            description=f"Custom policy: {name}",
            framework=framework,
            severity=PolicySeverity(severity),
            status=PolicyStatus.DRAFT,
            dsl_source=dsl_source,
            conditions=self._parse_conditions(dsl_source),
            actions=self._parse_actions(dsl_source),
            author=author,
            created_at=datetime.now(UTC),
        )
        self._policies[slug] = policy
        logger.info("Policy created", slug=slug, framework=framework)
        return policy

    def validate_dsl(self, dsl_source: str) -> ValidationResult:
        errors = []
        warnings = []
        if not dsl_source.strip():
            errors.append("DSL source is empty")
            return ValidationResult(valid=False, errors=errors)
        if "policy" not in dsl_source.lower():
            errors.append("Missing 'policy' keyword")
        if "when:" not in dsl_source and "when " not in dsl_source:
            warnings.append("No 'when' condition found — policy will match all files")
        if "then:" not in dsl_source and "then " not in dsl_source:
            errors.append("Missing 'then' action block")

        conditions = self._parse_conditions(dsl_source)
        actions = self._parse_actions(dsl_source)
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            parsed_conditions=len(conditions),
            parsed_actions=len(actions),
        )

    def _parse_conditions(self, dsl_source: str) -> list[dict]:
        conditions = []
        for line in dsl_source.split("\n"):
            line = line.strip()
            if line.startswith("when:"):
                parts = line[5:].strip().split("==")
                if len(parts) == 2:
                    conditions.append({"field": parts[0].strip(), "operator": "==", "value": parts[1].strip().strip('"')})
        return conditions

    def _parse_actions(self, dsl_source: str) -> list[dict]:
        actions = []
        for line in dsl_source.split("\n"):
            line = line.strip()
            if line.startswith("then:"):
                import re
                requires = re.findall(r'require\("([^"]+)"\)', line)
                for r in requires:
                    actions.append({"action": "require", "target": r})
        return actions

    async def compile_policy(self, slug: str, output_format: str) -> CompiledPolicy:
        policy = self._policies.get(slug)
        if not policy:
            return CompiledPolicy(errors=[f"Policy '{slug}' not found"])

        fmt = OutputFormat(output_format)
        code = self._compile_to_format(policy, fmt)
        self._compilations[fmt.value] = self._compilations.get(fmt.value, 0) + 1

        return CompiledPolicy(
            policy_id=policy.id,
            output_format=fmt,
            compiled_code=code,
            compiled_at=datetime.now(UTC),
        )

    def _compile_to_format(self, policy: PolicyDefinition, fmt: OutputFormat) -> str:
        if fmt == OutputFormat.REGO:
            conditions = " ".join(f'input.{c["field"]} == "{c["value"]}"' for c in policy.conditions)
            return f'package compliance.{policy.slug.replace("-", "_")}\n\ndefault allow = false\n\nallow {{\n  {conditions}\n}}\n\nviolation[msg] {{\n  not allow\n  msg := "{policy.description}"\n}}'
        if fmt == OutputFormat.PYTHON:
            checks = " and ".join(f'context.get("{c["field"]}") == "{c["value"]}"' for c in policy.conditions)
            return f'def check_{policy.slug.replace("-", "_")}(context: dict) -> bool:\n    """Check: {policy.description}"""\n    return {checks or "True"}'
        if fmt == OutputFormat.YAML:
            return f"policy:\n  name: {policy.name}\n  framework: {policy.framework}\n  severity: {policy.severity.value}\n  conditions:\n" + "".join(f'    - field: {c["field"]}\n      operator: {c.get("operator", "==")}\n      value: "{c["value"]}"\n' for c in policy.conditions) + "  actions:\n" + "".join(f'    - {a["action"]}: {a["target"]}\n' for a in policy.actions)
        if fmt == OutputFormat.TYPESCRIPT:
            checks = " && ".join(f'context.{c["field"]} === "{c["value"]}"' for c in policy.conditions)
            return f'export function check{policy.slug.replace("-", "_").title().replace("_", "")}(context: Record<string, string>): boolean {{\n  // {policy.description}\n  return {checks or "true"};\n}}'
        return ""

    def get_policy(self, slug: str) -> PolicyDefinition | None:
        return self._policies.get(slug)

    def list_policies(self, framework: str | None = None, status: PolicyStatus | None = None) -> list[PolicyDefinition]:
        results = list(self._policies.values())
        if framework:
            results = [p for p in results if p.framework == framework]
        if status:
            results = [p for p in results if p.status == status]
        return results

    async def activate_policy(self, slug: str) -> PolicyDefinition | None:
        policy = self._policies.get(slug)
        if not policy:
            return None
        policy.status = PolicyStatus.ACTIVE
        policy.updated_at = datetime.now(UTC)
        return policy

    def get_stats(self) -> PolicyDSLStats:
        by_fw: dict[str, int] = {}
        by_sev: dict[str, int] = {}
        active = 0
        for p in self._policies.values():
            if p.framework:
                by_fw[p.framework] = by_fw.get(p.framework, 0) + 1
            by_sev[p.severity.value] = by_sev.get(p.severity.value, 0) + 1
            if p.status == PolicyStatus.ACTIVE:
                active += 1
        return PolicyDSLStats(
            total_policies=len(self._policies),
            active_policies=active,
            by_framework=by_fw,
            by_severity=by_sev,
            compilations=dict(self._compilations),
        )
