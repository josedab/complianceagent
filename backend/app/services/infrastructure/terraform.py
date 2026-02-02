"""Terraform configuration analyzer for compliance."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
class TerraformResource:
    """Parsed Terraform resource."""
    
    resource_type: str
    name: str
    properties: dict[str, Any]
    file_path: str
    line_start: int
    line_end: int


class TerraformAnalyzer:
    """Analyzes Terraform configurations for compliance violations."""
    
    def __init__(self, policy_rules: list[PolicyRule] | None = None):
        """Initialize with policy rules."""
        from .models import DEFAULT_POLICY_RULES
        
        self.policy_rules = policy_rules or [
            r for r in DEFAULT_POLICY_RULES
            if CloudProvider.AWS in r.providers or not r.providers
        ]
    
    def analyze(
        self,
        content: str,
        file_path: str = "main.tf",
        regulations: list[str] | None = None,
    ) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
        """Analyze Terraform content for compliance.
        
        Args:
            content: Terraform configuration content
            file_path: Path to the file (for reporting)
            regulations: Filter rules by regulation
        
        Returns:
            Tuple of (resources, violations)
        """
        resources: list[InfrastructureResource] = []
        violations: list[ComplianceViolation] = []
        
        # Parse resources from content
        parsed_resources = self._parse_terraform(content, file_path)
        
        for parsed in parsed_resources:
            # Create infrastructure resource
            resource = InfrastructureResource(
                name=parsed.name,
                resource_type=parsed.resource_type,
                provider=self._detect_provider(parsed.resource_type),
                infrastructure_type=InfrastructureType.TERRAFORM,
                file_path=parsed.file_path,
                line_start=parsed.line_start,
                line_end=parsed.line_end,
                properties=parsed.properties,
                tags=parsed.properties.get("tags", {}),
            )
            
            # Detect data sensitivity
            resource.contains_pii = self._contains_pii_data(parsed)
            resource.contains_phi = self._contains_phi_data(parsed)
            resource.contains_pci = self._contains_pci_data(parsed)
            
            resources.append(resource)
            
            # Check rules
            for rule in self.policy_rules:
                if not rule.enabled:
                    continue
                
                # Filter by regulation
                if regulations and not any(r in rule.regulations for r in regulations):
                    continue
                
                # Check if rule applies to this resource type
                if rule.resource_types and parsed.resource_type not in rule.resource_types:
                    continue
                
                # Run check
                violation = self._check_rule(rule, parsed, resource)
                if violation:
                    violations.append(violation)
        
        return resources, violations
    
    def _parse_terraform(self, content: str, file_path: str) -> list[TerraformResource]:
        """Parse Terraform HCL content."""
        resources: list[TerraformResource] = []
        
        # Resource block pattern: resource "type" "name" { ... }
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        for match in re.finditer(resource_pattern, content, re.DOTALL):
            resource_type = match.group(1)
            name = match.group(2)
            body = match.group(3)
            
            # Calculate line numbers
            start_pos = match.start()
            line_start = content[:start_pos].count("\n") + 1
            line_end = line_start + body.count("\n")
            
            # Parse properties from HCL body
            properties = self._parse_hcl_properties(body)
            
            resources.append(TerraformResource(
                resource_type=resource_type,
                name=name,
                properties=properties,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
            ))
        
        return resources
    
    def _parse_hcl_properties(self, body: str) -> dict[str, Any]:
        """Parse HCL properties from resource body."""
        props: dict[str, Any] = {}
        
        # Simple key = value patterns
        kv_pattern = r'(\w+)\s*=\s*("([^"]*)"|true|false|\d+|\[[^\]]*\]|\{[^}]*\})'
        
        for match in re.finditer(kv_pattern, body):
            key = match.group(1)
            value_raw = match.group(2)
            
            if value_raw.startswith('"'):
                props[key] = match.group(3)
            elif value_raw == "true":
                props[key] = True
            elif value_raw == "false":
                props[key] = False
            elif value_raw.startswith("["):
                props[key] = self._parse_hcl_list(value_raw)
            elif value_raw.startswith("{"):
                props[key] = self._parse_hcl_map(value_raw)
            else:
                try:
                    props[key] = int(value_raw)
                except ValueError:
                    props[key] = value_raw
        
        # Nested blocks
        block_pattern = r'(\w+)\s*\{([^}]*)\}'
        for match in re.finditer(block_pattern, body):
            block_name = match.group(1)
            block_body = match.group(2)
            
            if block_name not in props:
                props[block_name] = []
            
            block_props = self._parse_hcl_properties(block_body)
            if isinstance(props[block_name], list):
                props[block_name].append(block_props)
            else:
                props[block_name] = block_props
        
        return props
    
    def _parse_hcl_list(self, value: str) -> list:
        """Parse HCL list."""
        # Simplified: extract quoted strings
        items = re.findall(r'"([^"]*)"', value)
        return items
    
    def _parse_hcl_map(self, value: str) -> dict:
        """Parse HCL map."""
        result: dict[str, str] = {}
        kv_pattern = r'"?(\w+)"?\s*[=:]\s*"([^"]*)"'
        for match in re.finditer(kv_pattern, value):
            result[match.group(1)] = match.group(2)
        return result
    
    def _detect_provider(self, resource_type: str) -> CloudProvider:
        """Detect cloud provider from resource type."""
        if resource_type.startswith("aws_"):
            return CloudProvider.AWS
        elif resource_type.startswith("azurerm_"):
            return CloudProvider.AZURE
        elif resource_type.startswith("google_"):
            return CloudProvider.GCP
        elif resource_type.startswith("kubernetes_"):
            return CloudProvider.KUBERNETES
        return CloudProvider.AWS
    
    def _contains_pii_data(self, resource: TerraformResource) -> bool:
        """Check if resource likely contains PII."""
        pii_indicators = ["user", "customer", "personal", "email", "address", "name"]
        resource_str = json.dumps(resource.properties).lower()
        return any(ind in resource_str for ind in pii_indicators)
    
    def _contains_phi_data(self, resource: TerraformResource) -> bool:
        """Check if resource likely contains PHI."""
        phi_indicators = ["health", "medical", "patient", "clinical", "hipaa", "phi"]
        resource_str = json.dumps(resource.properties).lower()
        return any(ind in resource_str for ind in phi_indicators)
    
    def _contains_pci_data(self, resource: TerraformResource) -> bool:
        """Check if resource likely contains PCI data."""
        pci_indicators = ["payment", "card", "transaction", "checkout", "billing"]
        resource_str = json.dumps(resource.properties).lower()
        return any(ind in resource_str for ind in pci_indicators)
    
    def _check_rule(
        self,
        rule: PolicyRule,
        parsed: TerraformResource,
        resource: InfrastructureResource,
    ) -> ComplianceViolation | None:
        """Check a rule against a resource."""
        
        # S3 Bucket Encryption
        if rule.id == "ENC001" and parsed.resource_type == "aws_s3_bucket":
            sse_config = parsed.properties.get("server_side_encryption_configuration", [])
            if not sse_config:
                return self._create_violation(
                    rule, parsed, resource,
                    "S3 bucket does not have server-side encryption enabled",
                    remediation=self._generate_s3_encryption_remediation(parsed),
                )
        
        # RDS Encryption
        if rule.id == "ENC002" and parsed.resource_type == "aws_db_instance":
            if not parsed.properties.get("storage_encrypted", False):
                return self._create_violation(
                    rule, parsed, resource,
                    "RDS instance does not have storage encryption enabled",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Enable storage encryption",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="storage_encrypted",
                        current_value=False,
                        suggested_value=True,
                        suggested_code='storage_encrypted = true\nkms_key_id = aws_kms_key.rds.arn',
                        estimated_effort_minutes=15,
                        breaking_change=True,  # Requires recreation
                    ),
                )
        
        # EBS Volume Encryption
        if rule.id == "ENC003" and parsed.resource_type == "aws_ebs_volume":
            if not parsed.properties.get("encrypted", False):
                return self._create_violation(
                    rule, parsed, resource,
                    "EBS volume is not encrypted",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Enable EBS encryption",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="encrypted",
                        current_value=False,
                        suggested_value=True,
                        suggested_code='encrypted = true',
                        estimated_effort_minutes=5,
                    ),
                )
        
        # IAM Wildcard Actions
        if rule.id == "IAM001" and parsed.resource_type in ["aws_iam_policy", "aws_iam_role_policy"]:
            policy = parsed.properties.get("policy", "")
            if isinstance(policy, str) and '"Action": "*"' in policy or '"Action": ["*"]' in policy:
                return self._create_violation(
                    rule, parsed, resource,
                    "IAM policy uses wildcard (*) for actions",
                    remediation=RemediationAction(
                        action_type="modify_policy",
                        description="Replace wildcard actions with specific actions",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        requires_manual_review=True,
                        estimated_effort_minutes=30,
                    ),
                )
        
        # Public S3 Buckets
        if rule.id == "IAM002" and parsed.resource_type == "aws_s3_bucket":
            acl = parsed.properties.get("acl", "private")
            if acl in ["public-read", "public-read-write"]:
                return self._create_violation(
                    rule, parsed, resource,
                    f"S3 bucket has public ACL: {acl}",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Change ACL to private",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="acl",
                        current_value=acl,
                        suggested_value="private",
                        suggested_code='acl = "private"',
                        estimated_effort_minutes=5,
                    ),
                )
        
        # Open Security Groups
        if rule.id == "NET001" and parsed.resource_type == "aws_security_group":
            ingress_rules = parsed.properties.get("ingress", [])
            if isinstance(ingress_rules, list):
                for ingress in ingress_rules:
                    if isinstance(ingress, dict):
                        cidr_blocks = ingress.get("cidr_blocks", [])
                        if "0.0.0.0/0" in cidr_blocks:
                            from_port = ingress.get("from_port", 0)
                            to_port = ingress.get("to_port", 65535)
                            # Allow 443 from anywhere
                            if not (from_port == 443 and to_port == 443):
                                return self._create_violation(
                                    rule, parsed, resource,
                                    f"Security group allows unrestricted access (0.0.0.0/0) on ports {from_port}-{to_port}",
                                    evidence={"ingress_rule": ingress},
                                    remediation=RemediationAction(
                                        action_type="modify_property",
                                        description="Restrict CIDR blocks",
                                        resource_name=parsed.name,
                                        resource_type=parsed.resource_type,
                                        file_path=parsed.file_path,
                                        requires_manual_review=True,
                                        estimated_effort_minutes=15,
                                    ),
                                )
        
        # HTTPS Only
        if rule.id == "NET002" and parsed.resource_type == "aws_lb_listener":
            protocol = parsed.properties.get("protocol", "HTTP")
            if protocol == "HTTP":
                return self._create_violation(
                    rule, parsed, resource,
                    "Load balancer listener uses HTTP instead of HTTPS",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Switch to HTTPS",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="protocol",
                        current_value="HTTP",
                        suggested_value="HTTPS",
                        suggested_code='protocol = "HTTPS"\nssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"\ncertificate_arn = aws_acm_certificate.cert.arn',
                        estimated_effort_minutes=20,
                    ),
                )
        
        # CloudTrail
        if rule.id == "LOG001" and parsed.resource_type == "aws_cloudtrail":
            if not parsed.properties.get("is_multi_region_trail", False):
                return self._create_violation(
                    rule, parsed, resource,
                    "CloudTrail is not enabled for multi-region",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Enable multi-region CloudTrail",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="is_multi_region_trail",
                        current_value=False,
                        suggested_value=True,
                        suggested_code='is_multi_region_trail = true\nenable_log_file_validation = true',
                        estimated_effort_minutes=10,
                    ),
                )
        
        # S3 Access Logging
        if rule.id == "LOG002" and parsed.resource_type == "aws_s3_bucket":
            logging = parsed.properties.get("logging", [])
            if not logging:
                return self._create_violation(
                    rule, parsed, resource,
                    "S3 bucket does not have access logging enabled",
                    remediation=RemediationAction(
                        action_type="add_block",
                        description="Enable access logging",
                        resource_name=parsed.name,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        suggested_code='logging {\n  target_bucket = aws_s3_bucket.log_bucket.id\n  target_prefix = "log/${var.bucket_name}/"\n}',
                        estimated_effort_minutes=15,
                    ),
                )
        
        return None
    
    def _create_violation(
        self,
        rule: PolicyRule,
        parsed: TerraformResource,
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
            resource_type=parsed.resource_type,
            resource_id=str(resource.id),
            provider=resource.provider,
            file_path=parsed.file_path,
            line_number=parsed.line_start,
            regulations=rule.regulations,
            requirement_ids=rule.requirement_ids,
            evidence=evidence or {},
            remediation=remediation,
        )
    
    def _generate_s3_encryption_remediation(self, parsed: TerraformResource) -> RemediationAction:
        """Generate S3 encryption remediation."""
        return RemediationAction(
            action_type="add_block",
            description="Add server-side encryption configuration",
            resource_name=parsed.name,
            resource_type=parsed.resource_type,
            file_path=parsed.file_path,
            suggested_code='''server_side_encryption_configuration {
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
    bucket_key_enabled = true
  }
}''',
            estimated_effort_minutes=10,
        )


def analyze_terraform_file(file_path: str | Path, regulations: list[str] | None = None) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
    """Convenience function to analyze a Terraform file."""
    path = Path(file_path)
    content = path.read_text()
    
    analyzer = TerraformAnalyzer()
    return analyzer.analyze(content, str(path), regulations)


def analyze_terraform_directory(
    directory: str | Path,
    regulations: list[str] | None = None,
) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
    """Analyze all Terraform files in a directory."""
    dir_path = Path(directory)
    all_resources: list[InfrastructureResource] = []
    all_violations: list[ComplianceViolation] = []
    
    analyzer = TerraformAnalyzer()
    
    for tf_file in dir_path.rglob("*.tf"):
        try:
            content = tf_file.read_text()
            resources, violations = analyzer.analyze(content, str(tf_file), regulations)
            all_resources.extend(resources)
            all_violations.extend(violations)
        except Exception:
            pass  # Skip files that can't be parsed
    
    return all_resources, all_violations
