"""Kubernetes manifest analyzer for compliance."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import (
    CloudProvider,
    ComplianceCategory,
    ComplianceViolation,
    InfrastructureResource,
    InfrastructureType,
    PolicyRule,
    RemediationAction,
    ViolationSeverity,
)


@dataclass
class K8sResource:
    """Parsed Kubernetes resource."""
    
    api_version: str
    kind: str
    name: str
    namespace: str
    spec: dict[str, Any]
    metadata: dict[str, Any]
    file_path: str
    document_index: int


class KubernetesAnalyzer:
    """Analyzes Kubernetes manifests for compliance violations."""
    
    def __init__(self, policy_rules: list[PolicyRule] | None = None):
        """Initialize with policy rules."""
        from .models import DEFAULT_POLICY_RULES
        
        self.policy_rules = policy_rules or [
            r for r in DEFAULT_POLICY_RULES
            if CloudProvider.KUBERNETES in r.providers
        ]
    
    def analyze(
        self,
        content: str,
        file_path: str = "manifest.yaml",
        regulations: list[str] | None = None,
    ) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
        """Analyze Kubernetes manifest for compliance.
        
        Args:
            content: YAML manifest content
            file_path: Path to the file (for reporting)
            regulations: Filter rules by regulation
        
        Returns:
            Tuple of (resources, violations)
        """
        resources: list[InfrastructureResource] = []
        violations: list[ComplianceViolation] = []
        
        # Parse YAML documents
        parsed_resources = self._parse_manifests(content, file_path)
        
        for parsed in parsed_resources:
            # Create infrastructure resource
            resource = InfrastructureResource(
                name=parsed.name,
                resource_type=parsed.kind,
                provider=CloudProvider.KUBERNETES,
                infrastructure_type=InfrastructureType.KUBERNETES,
                file_path=parsed.file_path,
                properties={
                    "apiVersion": parsed.api_version,
                    "kind": parsed.kind,
                    "spec": parsed.spec,
                    "metadata": parsed.metadata,
                },
                tags=parsed.metadata.get("labels", {}),
            )
            
            resources.append(resource)
            
            # Check rules
            for rule in self.policy_rules:
                if not rule.enabled:
                    continue
                
                # Filter by regulation
                if regulations and not any(r in rule.regulations for r in regulations):
                    continue
                
                # Check if rule applies to this resource kind
                if rule.resource_types and parsed.kind not in rule.resource_types:
                    continue
                
                # Run checks
                rule_violations = self._check_rule(rule, parsed, resource)
                violations.extend(rule_violations)
        
        return resources, violations
    
    def _parse_manifests(self, content: str, file_path: str) -> list[K8sResource]:
        """Parse YAML manifests."""
        resources: list[K8sResource] = []
        
        try:
            docs = list(yaml.safe_load_all(content))
        except yaml.YAMLError:
            return resources
        
        for i, doc in enumerate(docs):
            if doc is None:
                continue
            
            if not isinstance(doc, dict):
                continue
            
            kind = doc.get("kind", "")
            if not kind:
                continue
            
            metadata = doc.get("metadata", {})
            
            resources.append(K8sResource(
                api_version=doc.get("apiVersion", ""),
                kind=kind,
                name=metadata.get("name", "unnamed"),
                namespace=metadata.get("namespace", "default"),
                spec=doc.get("spec", {}),
                metadata=metadata,
                file_path=file_path,
                document_index=i,
            ))
        
        return resources
    
    def _check_rule(
        self,
        rule: PolicyRule,
        parsed: K8sResource,
        resource: InfrastructureResource,
    ) -> list[ComplianceViolation]:
        """Check a rule against a resource."""
        violations: list[ComplianceViolation] = []
        
        # Get all containers (including init containers)
        containers = self._get_containers(parsed)
        
        # K8S001: No Privileged Containers
        if rule.id == "K8S001":
            for container in containers:
                security_context = container.get("securityContext", {})
                if security_context.get("privileged", False):
                    violations.append(self._create_violation(
                        rule, parsed, resource,
                        f"Container '{container.get('name', 'unknown')}' runs in privileged mode",
                        evidence={"container": container.get("name"), "privileged": True},
                        remediation=RemediationAction(
                            action_type="modify_property",
                            description="Disable privileged mode",
                            resource_name=parsed.name,
                            resource_type=parsed.kind,
                            file_path=parsed.file_path,
                            property_path=f"spec.containers[].securityContext.privileged",
                            current_value=True,
                            suggested_value=False,
                            suggested_code='securityContext:\n  privileged: false',
                            estimated_effort_minutes=5,
                        ),
                    ))
        
        # K8S002: Run as Non-Root
        if rule.id == "K8S002":
            for container in containers:
                security_context = container.get("securityContext", {})
                pod_security = parsed.spec.get("securityContext", {})
                
                # Check both container and pod level
                run_as_non_root = (
                    security_context.get("runAsNonRoot") or
                    pod_security.get("runAsNonRoot")
                )
                
                if not run_as_non_root:
                    violations.append(self._create_violation(
                        rule, parsed, resource,
                        f"Container '{container.get('name', 'unknown')}' may run as root",
                        evidence={"container": container.get("name")},
                        remediation=RemediationAction(
                            action_type="modify_property",
                            description="Configure to run as non-root",
                            resource_name=parsed.name,
                            resource_type=parsed.kind,
                            file_path=parsed.file_path,
                            property_path=f"spec.containers[].securityContext.runAsNonRoot",
                            current_value=None,
                            suggested_value=True,
                            suggested_code='securityContext:\n  runAsNonRoot: true\n  runAsUser: 1000',
                            estimated_effort_minutes=10,
                        ),
                    ))
        
        # K8S003: Resource Limits Required
        if rule.id == "K8S003":
            for container in containers:
                resources_spec = container.get("resources", {})
                limits = resources_spec.get("limits", {})
                
                missing = []
                if "cpu" not in limits:
                    missing.append("cpu")
                if "memory" not in limits:
                    missing.append("memory")
                
                if missing:
                    violations.append(self._create_violation(
                        rule, parsed, resource,
                        f"Container '{container.get('name', 'unknown')}' missing resource limits: {', '.join(missing)}",
                        evidence={"container": container.get("name"), "missing_limits": missing},
                        remediation=RemediationAction(
                            action_type="add_property",
                            description="Add resource limits",
                            resource_name=parsed.name,
                            resource_type=parsed.kind,
                            file_path=parsed.file_path,
                            property_path=f"spec.containers[].resources.limits",
                            suggested_code='resources:\n  limits:\n    cpu: "500m"\n    memory: "512Mi"\n  requests:\n    cpu: "100m"\n    memory: "128Mi"',
                            estimated_effort_minutes=10,
                        ),
                    ))
        
        # K8S004: No Latest Tag
        if rule.id == "K8S004":
            for container in containers:
                image = container.get("image", "")
                
                # Check for latest tag or no tag
                if ":latest" in image or ":" not in image:
                    violations.append(self._create_violation(
                        rule, parsed, resource,
                        f"Container '{container.get('name', 'unknown')}' uses 'latest' or untagged image: {image}",
                        evidence={"container": container.get("name"), "image": image},
                        remediation=RemediationAction(
                            action_type="modify_property",
                            description="Use specific image tag",
                            resource_name=parsed.name,
                            resource_type=parsed.kind,
                            file_path=parsed.file_path,
                            property_path=f"spec.containers[].image",
                            current_value=image,
                            suggested_value=f"{image.split(':')[0]}:v1.0.0",
                            requires_manual_review=True,
                            estimated_effort_minutes=5,
                        ),
                    ))
        
        # K8S005: Secrets should reference external secret managers
        if rule.id == "K8S005" and parsed.kind == "Secret":
            secret_type = parsed.spec.get("type", "Opaque")
            # Check if data is plain (not from external source)
            data = parsed.spec.get("data", {})
            string_data = parsed.spec.get("stringData", {})
            
            if data or string_data:
                violations.append(self._create_violation(
                    rule, parsed, resource,
                    f"Secret '{parsed.name}' contains embedded secret data",
                    evidence={"secret_type": secret_type, "has_data": bool(data or string_data)},
                    remediation=RemediationAction(
                        action_type="refactor",
                        description="Use external secret manager (Vault, AWS Secrets Manager, etc.)",
                        resource_name=parsed.name,
                        resource_type=parsed.kind,
                        file_path=parsed.file_path,
                        requires_manual_review=True,
                        estimated_effort_minutes=60,
                    ),
                ))
        
        # Additional checks for workloads
        if parsed.kind in ["Deployment", "StatefulSet", "DaemonSet", "Pod"]:
            violations.extend(self._check_workload_security(rule, parsed, resource, containers))
        
        return violations
    
    def _check_workload_security(
        self,
        rule: PolicyRule,
        parsed: K8sResource,
        resource: InfrastructureResource,
        containers: list[dict],
    ) -> list[ComplianceViolation]:
        """Additional security checks for workloads."""
        violations: list[ComplianceViolation] = []
        
        for container in containers:
            security_context = container.get("securityContext", {})
            
            # Check for capabilities
            capabilities = security_context.get("capabilities", {})
            add_caps = capabilities.get("add", [])
            
            dangerous_caps = ["SYS_ADMIN", "NET_ADMIN", "ALL"]
            for cap in dangerous_caps:
                if cap in add_caps:
                    violations.append(ComplianceViolation(
                        rule_id="K8S006",
                        rule_name="Dangerous Capabilities",
                        severity=ViolationSeverity.HIGH,
                        category=ComplianceCategory.ACCESS_CONTROL,
                        description=f"Container '{container.get('name')}' has dangerous capability: {cap}",
                        resource_name=parsed.name,
                        resource_type=parsed.kind,
                        file_path=parsed.file_path,
                        regulations=["SOC2", "PCI-DSS"],
                        evidence={"capability": cap},
                        remediation=RemediationAction(
                            action_type="remove_property",
                            description=f"Remove {cap} capability",
                            resource_name=parsed.name,
                            resource_type=parsed.kind,
                            file_path=parsed.file_path,
                            requires_manual_review=True,
                            estimated_effort_minutes=15,
                        ),
                    ))
            
            # Check for host network/PID/IPC
            pod_spec = parsed.spec.get("template", {}).get("spec", {}) if "template" in parsed.spec else parsed.spec
            
            if pod_spec.get("hostNetwork", False):
                violations.append(ComplianceViolation(
                    rule_id="K8S007",
                    rule_name="Host Network",
                    severity=ViolationSeverity.HIGH,
                    category=ComplianceCategory.NETWORK_SECURITY,
                    description=f"Pod '{parsed.name}' uses host network",
                    resource_name=parsed.name,
                    resource_type=parsed.kind,
                    file_path=parsed.file_path,
                    regulations=["SOC2", "PCI-DSS"],
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Disable host network",
                        resource_name=parsed.name,
                        resource_type=parsed.kind,
                        file_path=parsed.file_path,
                        property_path="spec.hostNetwork",
                        current_value=True,
                        suggested_value=False,
                        estimated_effort_minutes=10,
                    ),
                ))
        
        return violations
    
    def _get_containers(self, parsed: K8sResource) -> list[dict]:
        """Get all containers from a resource."""
        containers: list[dict] = []
        
        if parsed.kind == "Pod":
            containers.extend(parsed.spec.get("containers", []))
            containers.extend(parsed.spec.get("initContainers", []))
        elif parsed.kind in ["Deployment", "StatefulSet", "DaemonSet", "Job"]:
            template = parsed.spec.get("template", {})
            spec = template.get("spec", {})
            containers.extend(spec.get("containers", []))
            containers.extend(spec.get("initContainers", []))
        elif parsed.kind == "CronJob":
            job_template = parsed.spec.get("jobTemplate", {})
            template = job_template.get("spec", {}).get("template", {})
            spec = template.get("spec", {})
            containers.extend(spec.get("containers", []))
            containers.extend(spec.get("initContainers", []))
        
        return containers
    
    def _create_violation(
        self,
        rule: PolicyRule,
        parsed: K8sResource,
        resource: InfrastructureResource,
        description: str,
        evidence: dict[str, Any] | None = None,
        remediation: RemediationAction | None = None,
    ) -> ComplianceViolation:
        """Create a compliance violation."""
        return ComplianceViolation(
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            category=rule.category,
            description=description,
            resource_name=parsed.name,
            resource_type=parsed.kind,
            resource_id=str(resource.id),
            provider=CloudProvider.KUBERNETES,
            file_path=parsed.file_path,
            regulations=rule.regulations,
            requirement_ids=rule.requirement_ids,
            evidence=evidence or {},
            remediation=remediation,
        )


def analyze_kubernetes_file(
    file_path: str | Path,
    regulations: list[str] | None = None,
) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
    """Convenience function to analyze a Kubernetes manifest file."""
    path = Path(file_path)
    content = path.read_text()
    
    analyzer = KubernetesAnalyzer()
    return analyzer.analyze(content, str(path), regulations)


def analyze_kubernetes_directory(
    directory: str | Path,
    regulations: list[str] | None = None,
) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
    """Analyze all Kubernetes manifest files in a directory."""
    dir_path = Path(directory)
    all_resources: list[InfrastructureResource] = []
    all_violations: list[ComplianceViolation] = []
    
    analyzer = KubernetesAnalyzer()
    
    for pattern in ["*.yaml", "*.yml"]:
        for manifest_file in dir_path.rglob(pattern):
            try:
                content = manifest_file.read_text()
                resources, violations = analyzer.analyze(
                    content, str(manifest_file), regulations
                )
                all_resources.extend(resources)
                all_violations.extend(violations)
            except Exception:
                pass  # Skip files that can't be parsed
    
    return all_resources, all_violations
