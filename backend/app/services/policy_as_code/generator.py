"""Policy generator for converting compliance rules to Rego/OPA code."""

import json
import re
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.policy_as_code.models import (
    PolicyLanguage,
    PolicyFormat,
    PolicyRule,
    PolicyPackage,
    PolicyCategory,
    PolicySeverity,
    PolicyTestCase,
    CompliancePolicyTemplate,
    COMPLIANCE_TEMPLATES,
)

logger = structlog.get_logger()


class PolicyGenerator:
    """Generates policy code from compliance rules."""
    
    def __init__(self) -> None:
        self._packages: dict[UUID, PolicyPackage] = {}
        self._templates: dict[str, CompliancePolicyTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize pre-built compliance templates."""
        for regulation, rules_data in COMPLIANCE_TEMPLATES.items():
            rules = [
                PolicyRule(
                    name=r["name"],
                    description=r["description"],
                    regulation=r["regulation"],
                    article=r.get("article"),
                    category=r["category"],
                    severity=r["severity"],
                    condition=r["condition"],
                    remediation=r.get("remediation"),
                    tags=r.get("tags", []),
                )
                for r in rules_data
            ]
            
            template = CompliancePolicyTemplate(
                id=f"{regulation.lower().replace(' ', '_')}_template",
                name=f"{regulation} Compliance Policy",
                description=f"Pre-built policy rules for {regulation} compliance",
                regulation=regulation,
                version="1.0.0",
                rules=rules,
                use_cases=["Regulatory compliance", "Audit preparation", "CI/CD enforcement"],
                industries=self._get_industries_for_regulation(regulation),
            )
            self._templates[regulation] = template
    
    def _get_industries_for_regulation(self, regulation: str) -> list[str]:
        """Get relevant industries for a regulation."""
        industry_map = {
            "GDPR": ["Technology", "E-commerce", "Healthcare", "Finance", "All EU operations"],
            "HIPAA": ["Healthcare", "Health Tech", "Insurance"],
            "PCI-DSS": ["Finance", "E-commerce", "Retail", "Payment Processing"],
            "EU AI Act": ["AI/ML", "Technology", "All sectors using AI"],
        }
        return industry_map.get(regulation, ["General"])
    
    async def get_templates(self) -> list[CompliancePolicyTemplate]:
        """Get all available compliance policy templates."""
        return list(self._templates.values())
    
    async def get_template(self, regulation: str) -> CompliancePolicyTemplate | None:
        """Get a specific compliance policy template."""
        return self._templates.get(regulation)
    
    async def create_package_from_template(
        self,
        regulation: str,
        organization_id: UUID | None = None,
        custom_parameters: dict[str, Any] | None = None,
    ) -> PolicyPackage:
        """Create a policy package from a pre-built template."""
        template = self._templates.get(regulation)
        if not template:
            raise ValueError(f"No template found for regulation: {regulation}")
        
        namespace = f"compliance.{regulation.lower().replace(' ', '_').replace('-', '_')}"
        
        package = PolicyPackage(
            name=f"{regulation} Compliance Policies",
            namespace=namespace,
            description=template.description,
            regulations=[regulation],
            rules=template.rules,
            organization_id=organization_id,
        )
        
        # Generate Rego code
        package.rego_package = await self._generate_rego_package(package)
        
        self._packages[package.id] = package
        return package
    
    async def create_custom_package(
        self,
        name: str,
        namespace: str,
        description: str,
        rules: list[dict[str, Any]],
        organization_id: UUID | None = None,
    ) -> PolicyPackage:
        """Create a custom policy package."""
        policy_rules = [
            PolicyRule(
                name=r["name"],
                description=r["description"],
                regulation=r.get("regulation", "Custom"),
                article=r.get("article"),
                category=PolicyCategory(r.get("category", "data_protection")),
                severity=PolicySeverity(r.get("severity", "medium")),
                condition=r["condition"],
                remediation=r.get("remediation"),
                tags=r.get("tags", []),
            )
            for r in rules
        ]
        
        regulations = list(set(r.regulation for r in policy_rules))
        
        package = PolicyPackage(
            name=name,
            namespace=namespace,
            description=description,
            regulations=regulations,
            rules=policy_rules,
            organization_id=organization_id,
        )
        
        package.rego_package = await self._generate_rego_package(package)
        
        self._packages[package.id] = package
        return package
    
    async def get_package(self, package_id: UUID) -> PolicyPackage | None:
        """Get a policy package by ID."""
        return self._packages.get(package_id)
    
    async def list_packages(
        self,
        organization_id: UUID | None = None,
    ) -> list[PolicyPackage]:
        """List policy packages, optionally filtered by organization."""
        packages = list(self._packages.values())
        if organization_id:
            packages = [p for p in packages if p.organization_id == organization_id]
        return packages
    
    async def _generate_rego_package(self, package: PolicyPackage) -> str:
        """Generate Rego code for a policy package."""
        lines = [
            f"# {package.name}",
            f"# {package.description}",
            f"# Generated: {datetime.utcnow().isoformat()}",
            f"# Regulations: {', '.join(package.regulations)}",
            "",
            f"package {package.namespace}",
            "",
            "import future.keywords.if",
            "import future.keywords.in",
            "import future.keywords.contains",
            "",
            "# ============================================================================",
            "# Default deny - compliance must be proven",
            "# ============================================================================",
            "",
            "default allow := false",
            "",
            "# Allow if no violations exist",
            "allow if {",
            "    count(violations) == 0",
            "}",
            "",
            "# ============================================================================",
            "# Violation Aggregation",
            "# ============================================================================",
            "",
            "violations contains violation if {",
            "    some v in all_violations",
            "    violation := v",
            "}",
            "",
            "all_violations := union({",
        ]
        
        # Add rule set references
        rule_sets = [f"    {self._rule_name_to_rego(r.name)}_violations" for r in package.rules]
        lines.append(",\n".join(rule_sets))
        lines.append("})")
        lines.append("")
        
        # Generate each rule
        for rule in package.rules:
            lines.extend(await self._generate_rego_rule(rule))
            lines.append("")
        
        # Add helper functions
        lines.extend(self._generate_helper_functions())
        
        return "\n".join(lines)
    
    async def _generate_rego_rule(self, rule: PolicyRule) -> list[str]:
        """Generate Rego code for a single rule."""
        rule_name = self._rule_name_to_rego(rule.name)
        
        lines = [
            "# ============================================================================",
            f"# Rule: {rule.name}",
            f"# Regulation: {rule.regulation}",
            f"# Article: {rule.article or 'N/A'}",
            f"# Severity: {rule.severity.value}",
            f"# Category: {rule.category.value}",
            "# ============================================================================",
            "",
        ]
        
        # Generate condition-specific Rego code
        rego_condition = await self._condition_to_rego(rule)
        
        lines.extend([
            f"{rule_name}_violations contains violation if {{",
            f"    # Condition: {rule.condition}",
            rego_condition,
            f'    violation := {{',
            f'        "rule": "{rule.name}",',
            f'        "regulation": "{rule.regulation}",',
            f'        "article": "{rule.article or "N/A"}",',
            f'        "severity": "{rule.severity.value}",',
            f'        "category": "{rule.category.value}",',
            f'        "description": "{rule.description}",',
            f'        "remediation": "{rule.remediation or "Review and fix the violation"}",',
            f'        "resource": resource,',
            f'    }}',
            "}",
        ])
        
        return lines
    
    async def _condition_to_rego(self, rule: PolicyRule) -> str:
        """Convert a rule condition to Rego logic."""
        category = rule.category
        
        # Map categories to Rego patterns
        if category == PolicyCategory.ENCRYPTION:
            return self._generate_encryption_check()
        elif category == PolicyCategory.ACCESS_CONTROL:
            return self._generate_access_control_check()
        elif category == PolicyCategory.LOGGING:
            return self._generate_logging_check()
        elif category == PolicyCategory.DATA_RETENTION:
            return self._generate_retention_check()
        elif category == PolicyCategory.CONSENT:
            return self._generate_consent_check()
        elif category == PolicyCategory.BREACH_NOTIFICATION:
            return self._generate_breach_check()
        elif category == PolicyCategory.VULNERABILITY:
            return self._generate_vulnerability_check()
        elif category == PolicyCategory.AI_GOVERNANCE:
            return self._generate_ai_governance_check()
        else:
            return self._generate_generic_check()
    
    def _generate_encryption_check(self) -> str:
        return """    some resource in input.resources
    resource.type in ["database", "storage", "api"]
    not resource.encryption.enabled
    # or encryption algorithm is weak
    encryption_weak(resource)"""
    
    def _generate_access_control_check(self) -> str:
        return """    some resource in input.resources
    resource.type in ["api", "database", "service"]
    not has_rbac(resource)
    # Check for least privilege violations"""
    
    def _generate_logging_check(self) -> str:
        return """    some resource in input.resources
    resource.type in ["api", "database", "service"]
    not resource.logging.enabled
    # or missing required log fields"""
    
    def _generate_retention_check(self) -> str:
        return """    some resource in input.resources
    resource.type == "database"
    not resource.retention_policy
    # or retention exceeds allowed period"""
    
    def _generate_consent_check(self) -> str:
        return """    some resource in input.resources
    resource.type == "data_collection"
    not resource.consent.tracked
    # or consent is expired"""
    
    def _generate_breach_check(self) -> str:
        return """    some resource in input.resources
    resource.type == "incident_response"
    not resource.breach_notification.configured
    # or notification SLA exceeds 72 hours"""
    
    def _generate_vulnerability_check(self) -> str:
        return """    some resource in input.resources
    resource.type in ["dependency", "container", "infrastructure"]
    resource.vulnerability.severity in ["critical", "high"]
    not resource.vulnerability.patched
    patch_overdue(resource)"""
    
    def _generate_ai_governance_check(self) -> str:
        return """    some resource in input.resources
    resource.type == "ai_model"
    not resource.ai_governance.risk_classified
    # or missing human oversight for high-risk"""
    
    def _generate_generic_check(self) -> str:
        return """    some resource in input.resources
    not resource.compliant"""
    
    def _generate_helper_functions(self) -> list[str]:
        """Generate helper functions for Rego policies."""
        return [
            "# ============================================================================",
            "# Helper Functions",
            "# ============================================================================",
            "",
            "# Check if encryption is weak",
            "encryption_weak(resource) if {",
            '    resource.encryption.algorithm in ["DES", "3DES", "RC4", "MD5"]',
            "}",
            "",
            "encryption_weak(resource) if {",
            "    resource.encryption.key_size < 256",
            "}",
            "",
            "# Check if RBAC is properly configured",
            "has_rbac(resource) if {",
            "    resource.access_control.type == \"rbac\"",
            "    count(resource.access_control.roles) > 0",
            "}",
            "",
            "# Check if patch is overdue",
            "patch_overdue(resource) if {",
            '    resource.vulnerability.severity == "critical"',
            "    time.now_ns() > resource.vulnerability.discovered_at + (7 * 24 * 60 * 60 * 1000000000)",
            "}",
            "",
            "patch_overdue(resource) if {",
            '    resource.vulnerability.severity == "high"',
            "    time.now_ns() > resource.vulnerability.discovered_at + (30 * 24 * 60 * 60 * 1000000000)",
            "}",
            "",
            "# Calculate compliance score",
            "compliance_score := 100 - (count(violations) * 10)",
        ]
    
    def _rule_name_to_rego(self, name: str) -> str:
        """Convert rule name to valid Rego identifier."""
        return re.sub(r'[^a-z0-9_]', '_', name.lower())
    
    async def export_package(
        self,
        package_id: UUID,
        format: PolicyFormat = PolicyFormat.RAW,
    ) -> dict[str, Any]:
        """Export a policy package in the specified format."""
        package = self._packages.get(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        if format == PolicyFormat.RAW:
            return {
                "format": "raw",
                "filename": f"{package.namespace.replace('.', '/')}.rego",
                "content": package.rego_package,
            }
        
        elif format == PolicyFormat.OPA_BUNDLE:
            return await self._export_opa_bundle(package)
        
        elif format == PolicyFormat.CONFTEST:
            return await self._export_conftest(package)
        
        elif format == PolicyFormat.GATEKEEPER:
            return await self._export_gatekeeper(package)
        
        elif format == PolicyFormat.KYVERNO:
            return await self._export_kyverno(package)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _export_opa_bundle(self, package: PolicyPackage) -> dict[str, Any]:
        """Export as OPA bundle format."""
        return {
            "format": "opa-bundle",
            "files": {
                f"{package.namespace.replace('.', '/')}/policy.rego": package.rego_package,
                ".manifest": json.dumps({
                    "revision": package.version,
                    "roots": [package.namespace.split('.')[0]],
                }),
                "data.json": json.dumps({
                    "compliance": {
                        "regulations": package.regulations,
                        "version": package.version,
                    }
                }),
            },
            "bundle_command": f"opa build -b {package.namespace.replace('.', '/')} -o bundle.tar.gz",
        }
    
    async def _export_conftest(self, package: PolicyPackage) -> dict[str, Any]:
        """Export for Conftest CI/CD integration."""
        return {
            "format": "conftest",
            "files": {
                f"policy/{package.namespace.replace('.', '_')}.rego": package.rego_package,
            },
            "usage": {
                "test_command": "conftest test --policy policy/ input.json",
                "ci_example": """
# GitHub Actions example
- name: Run Conftest
  uses: instrumenta/conftest-action@master
  with:
    files: input.json
    policy: policy/
""",
            },
        }
    
    async def _export_gatekeeper(self, package: PolicyPackage) -> dict[str, Any]:
        """Export for Kubernetes Gatekeeper."""
        constraint_templates = []
        
        for rule in package.rules:
            template = {
                "apiVersion": "templates.gatekeeper.sh/v1",
                "kind": "ConstraintTemplate",
                "metadata": {
                    "name": self._rule_name_to_rego(rule.name),
                    "annotations": {
                        "description": rule.description,
                        "regulation": rule.regulation,
                        "severity": rule.severity.value,
                    },
                },
                "spec": {
                    "crd": {
                        "spec": {
                            "names": {
                                "kind": self._rule_name_to_rego(rule.name).title().replace('_', ''),
                            },
                        },
                    },
                    "targets": [
                        {
                            "target": "admission.k8s.gatekeeper.sh",
                            "rego": f"""
package {self._rule_name_to_rego(rule.name)}

violation[{{"msg": msg}}] {{
    # {rule.condition}
    input.review.object.kind == "Pod"
    not compliant
    msg := "{rule.description}"
}}

compliant {{
    # Add specific compliance check logic
    true
}}
""",
                        }
                    ],
                },
            }
            constraint_templates.append(template)
        
        return {
            "format": "gatekeeper",
            "files": {
                f"templates/{self._rule_name_to_rego(r.name)}.yaml": json.dumps(t, indent=2)
                for r, t in zip(package.rules, constraint_templates)
            },
            "usage": "kubectl apply -f templates/",
        }
    
    async def _export_kyverno(self, package: PolicyPackage) -> dict[str, Any]:
        """Export for Kyverno policy engine."""
        policies = []
        
        for rule in package.rules:
            policy = {
                "apiVersion": "kyverno.io/v1",
                "kind": "ClusterPolicy",
                "metadata": {
                    "name": self._rule_name_to_rego(rule.name),
                    "annotations": {
                        "policies.kyverno.io/title": rule.name,
                        "policies.kyverno.io/description": rule.description,
                        "policies.kyverno.io/severity": rule.severity.value,
                        "compliance/regulation": rule.regulation,
                    },
                },
                "spec": {
                    "validationFailureAction": "enforce" if rule.severity in [PolicySeverity.CRITICAL, PolicySeverity.HIGH] else "audit",
                    "rules": [
                        {
                            "name": rule.name,
                            "match": {
                                "any": [
                                    {"resources": {"kinds": ["Pod", "Deployment", "Service"]}},
                                ],
                            },
                            "validate": {
                                "message": rule.description,
                                "pattern": {
                                    "metadata": {
                                        "labels": {
                                            "compliance-checked": "true",
                                        },
                                    },
                                },
                            },
                        }
                    ],
                },
            }
            policies.append(policy)
        
        return {
            "format": "kyverno",
            "files": {
                f"policies/{self._rule_name_to_rego(r.name)}.yaml": json.dumps(p, indent=2)
                for r, p in zip(package.rules, policies)
            },
            "usage": "kubectl apply -f policies/",
        }


# Singleton instance
_generator_instance: PolicyGenerator | None = None


def get_policy_generator() -> PolicyGenerator:
    """Get or create the policy generator singleton."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = PolicyGenerator()
    return _generator_instance
