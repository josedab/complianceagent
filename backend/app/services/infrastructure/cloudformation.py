"""CloudFormation template analyzer for compliance."""

import json
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
class CFNResource:
    """Parsed CloudFormation resource."""
    
    logical_id: str
    resource_type: str
    properties: dict[str, Any]
    metadata: dict[str, Any]
    condition: str | None
    depends_on: list[str]
    file_path: str


class CloudFormationAnalyzer:
    """Analyzes CloudFormation templates for compliance violations."""
    
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
        file_path: str = "template.yaml",
        regulations: list[str] | None = None,
    ) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
        """Analyze CloudFormation template for compliance.
        
        Args:
            content: CloudFormation template content (JSON or YAML)
            file_path: Path to the file (for reporting)
            regulations: Filter rules by regulation
        
        Returns:
            Tuple of (resources, violations)
        """
        resources: list[InfrastructureResource] = []
        violations: list[ComplianceViolation] = []
        
        # Parse template
        template = self._parse_template(content)
        if not template:
            return resources, violations
        
        # Parse resources
        template_resources = template.get("Resources", {})
        parsed_resources = self._parse_resources(template_resources, file_path)
        
        for parsed in parsed_resources:
            # Create infrastructure resource
            resource = InfrastructureResource(
                name=parsed.logical_id,
                resource_type=parsed.resource_type,
                provider=CloudProvider.AWS,
                infrastructure_type=InfrastructureType.CLOUDFORMATION,
                file_path=parsed.file_path,
                properties=parsed.properties,
                depends_on=parsed.depends_on,
            )
            
            resources.append(resource)
            
            # Check rules
            for rule in self.policy_rules:
                if not rule.enabled:
                    continue
                
                # Filter by regulation
                if regulations and not any(r in rule.regulations for r in regulations):
                    continue
                
                # Map CFN resource type to rule resource types
                if rule.resource_types:
                    matches = any(
                        self._type_matches(parsed.resource_type, rt)
                        for rt in rule.resource_types
                    )
                    if not matches:
                        continue
                
                # Run checks
                violation = self._check_rule(rule, parsed, resource)
                if violation:
                    violations.append(violation)
        
        return resources, violations
    
    def _parse_template(self, content: str) -> dict | None:
        """Parse CloudFormation template (JSON or YAML)."""
        try:
            # Try JSON first
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        try:
            # Try YAML
            return yaml.safe_load(content)
        except yaml.YAMLError:
            pass
        
        return None
    
    def _parse_resources(
        self,
        resources: dict[str, Any],
        file_path: str,
    ) -> list[CFNResource]:
        """Parse CloudFormation resources section."""
        parsed: list[CFNResource] = []
        
        for logical_id, resource_def in resources.items():
            if not isinstance(resource_def, dict):
                continue
            
            resource_type = resource_def.get("Type", "")
            if not resource_type:
                continue
            
            properties = resource_def.get("Properties", {})
            metadata = resource_def.get("Metadata", {})
            condition = resource_def.get("Condition")
            depends_on = resource_def.get("DependsOn", [])
            
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            parsed.append(CFNResource(
                logical_id=logical_id,
                resource_type=resource_type,
                properties=properties,
                metadata=metadata,
                condition=condition,
                depends_on=depends_on,
                file_path=file_path,
            ))
        
        return parsed
    
    def _type_matches(self, cfn_type: str, rule_type: str) -> bool:
        """Check if CloudFormation type matches rule type."""
        # Direct match
        if cfn_type == rule_type:
            return True
        
        # Convert CFN type to Terraform-style for matching
        # AWS::S3::Bucket -> aws_s3_bucket
        if cfn_type.startswith("AWS::"):
            parts = cfn_type.split("::")
            if len(parts) == 3:
                tf_style = f"aws_{parts[1].lower()}_{parts[2].lower()}"
                if tf_style == rule_type:
                    return True
        
        return False
    
    def _check_rule(
        self,
        rule: PolicyRule,
        parsed: CFNResource,
        resource: InfrastructureResource,
    ) -> ComplianceViolation | None:
        """Check a rule against a resource."""
        
        # S3 Bucket Encryption
        if rule.id == "ENC001" and "S3::Bucket" in parsed.resource_type:
            bucket_encryption = parsed.properties.get("BucketEncryption", {})
            sse_config = bucket_encryption.get("ServerSideEncryptionConfiguration", [])
            
            if not sse_config:
                return self._create_violation(
                    rule, parsed, resource,
                    "S3 bucket does not have server-side encryption configured",
                    remediation=RemediationAction(
                        action_type="add_property",
                        description="Add BucketEncryption configuration",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="Properties.BucketEncryption",
                        suggested_code='''BucketEncryption:
  ServerSideEncryptionConfiguration:
    - ServerSideEncryptionByDefault:
        SSEAlgorithm: aws:kms
        KMSMasterKeyID: !Ref KMSKey''',
                        estimated_effort_minutes=10,
                    ),
                )
        
        # RDS Encryption
        if rule.id == "ENC002" and "RDS::DBInstance" in parsed.resource_type:
            storage_encrypted = parsed.properties.get("StorageEncrypted", False)
            if not storage_encrypted:
                return self._create_violation(
                    rule, parsed, resource,
                    "RDS instance does not have storage encryption enabled",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Enable storage encryption",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="Properties.StorageEncrypted",
                        current_value=False,
                        suggested_value=True,
                        suggested_code='StorageEncrypted: true\nKmsKeyId: !Ref RDSKMSKey',
                        estimated_effort_minutes=15,
                        breaking_change=True,
                    ),
                )
        
        # EBS Volume Encryption
        if rule.id == "ENC003" and "EC2::Volume" in parsed.resource_type:
            encrypted = parsed.properties.get("Encrypted", False)
            if not encrypted:
                return self._create_violation(
                    rule, parsed, resource,
                    "EBS volume is not encrypted",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Enable volume encryption",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="Properties.Encrypted",
                        current_value=False,
                        suggested_value=True,
                        suggested_code='Encrypted: true',
                        estimated_effort_minutes=5,
                    ),
                )
        
        # IAM Wildcard Actions
        if rule.id == "IAM001" and "IAM::Policy" in parsed.resource_type:
            policy_document = parsed.properties.get("PolicyDocument", {})
            statements = policy_document.get("Statement", [])
            
            for stmt in statements:
                if isinstance(stmt, dict):
                    actions = stmt.get("Action", [])
                    if isinstance(actions, str):
                        actions = [actions]
                    
                    if "*" in actions:
                        return self._create_violation(
                            rule, parsed, resource,
                            "IAM policy uses wildcard (*) for actions",
                            evidence={"statement": stmt},
                            remediation=RemediationAction(
                                action_type="modify_policy",
                                description="Replace wildcard with specific actions",
                                resource_name=parsed.logical_id,
                                resource_type=parsed.resource_type,
                                file_path=parsed.file_path,
                                requires_manual_review=True,
                                estimated_effort_minutes=30,
                            ),
                        )
        
        # Public S3 Buckets
        if rule.id == "IAM002" and "S3::Bucket" in parsed.resource_type:
            access_control = parsed.properties.get("AccessControl", "Private")
            public_access_config = parsed.properties.get("PublicAccessBlockConfiguration", {})
            
            # Check for public ACL
            if access_control in ["PublicRead", "PublicReadWrite"]:
                return self._create_violation(
                    rule, parsed, resource,
                    f"S3 bucket has public access control: {access_control}",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Remove public access",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="Properties.AccessControl",
                        current_value=access_control,
                        suggested_value="Private",
                        suggested_code='''AccessControl: Private
PublicAccessBlockConfiguration:
  BlockPublicAcls: true
  BlockPublicPolicy: true
  IgnorePublicAcls: true
  RestrictPublicBuckets: true''',
                        estimated_effort_minutes=10,
                    ),
                )
            
            # Check for missing public access block
            if not public_access_config:
                return self._create_violation(
                    rule, parsed, resource,
                    "S3 bucket does not have PublicAccessBlockConfiguration",
                    remediation=RemediationAction(
                        action_type="add_property",
                        description="Add public access block configuration",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="Properties.PublicAccessBlockConfiguration",
                        suggested_code='''PublicAccessBlockConfiguration:
  BlockPublicAcls: true
  BlockPublicPolicy: true
  IgnorePublicAcls: true
  RestrictPublicBuckets: true''',
                        estimated_effort_minutes=5,
                    ),
                )
        
        # Open Security Groups
        if rule.id == "NET001" and "EC2::SecurityGroup" in parsed.resource_type:
            ingress_rules = parsed.properties.get("SecurityGroupIngress", [])
            
            for ingress in ingress_rules:
                if not isinstance(ingress, dict):
                    continue
                
                cidr = ingress.get("CidrIp", "")
                cidr_v6 = ingress.get("CidrIpv6", "")
                
                if cidr == "0.0.0.0/0" or cidr_v6 == "::/0":
                    from_port = ingress.get("FromPort", 0)
                    to_port = ingress.get("ToPort", 65535)
                    
                    # Allow 443 from anywhere
                    if not (from_port == 443 and to_port == 443):
                        return self._create_violation(
                            rule, parsed, resource,
                            f"Security group allows unrestricted access on ports {from_port}-{to_port}",
                            evidence={"ingress_rule": ingress},
                            remediation=RemediationAction(
                                action_type="modify_property",
                                description="Restrict CIDR blocks",
                                resource_name=parsed.logical_id,
                                resource_type=parsed.resource_type,
                                file_path=parsed.file_path,
                                requires_manual_review=True,
                                estimated_effort_minutes=15,
                            ),
                        )
        
        # HTTPS Only on ALB Listeners
        if rule.id == "NET002" and "ElasticLoadBalancingV2::Listener" in parsed.resource_type:
            protocol = parsed.properties.get("Protocol", "HTTP")
            if protocol == "HTTP":
                port = parsed.properties.get("Port", 80)
                
                # Only flag if it's not a redirect action
                default_actions = parsed.properties.get("DefaultActions", [])
                is_redirect = any(
                    a.get("Type") == "redirect" and
                    a.get("RedirectConfig", {}).get("Protocol") == "HTTPS"
                    for a in default_actions if isinstance(a, dict)
                )
                
                if not is_redirect:
                    return self._create_violation(
                        rule, parsed, resource,
                        "Load balancer listener uses HTTP instead of HTTPS",
                        remediation=RemediationAction(
                            action_type="modify_property",
                            description="Switch to HTTPS or add redirect",
                            resource_name=parsed.logical_id,
                            resource_type=parsed.resource_type,
                            file_path=parsed.file_path,
                            property_path="Properties.Protocol",
                            current_value="HTTP",
                            suggested_value="HTTPS",
                            suggested_code='''Protocol: HTTPS
Port: 443
SslPolicy: ELBSecurityPolicy-TLS-1-2-2017-01
Certificates:
  - CertificateArn: !Ref Certificate''',
                            estimated_effort_minutes=20,
                        ),
                    )
        
        # CloudTrail
        if rule.id == "LOG001" and "CloudTrail::Trail" in parsed.resource_type:
            is_multi_region = parsed.properties.get("IsMultiRegionTrail", False)
            enable_log_validation = parsed.properties.get("EnableLogFileValidation", False)
            
            issues = []
            if not is_multi_region:
                issues.append("multi-region")
            if not enable_log_validation:
                issues.append("log file validation")
            
            if issues:
                return self._create_violation(
                    rule, parsed, resource,
                    f"CloudTrail is missing: {', '.join(issues)}",
                    remediation=RemediationAction(
                        action_type="modify_property",
                        description="Enable missing CloudTrail features",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        suggested_code='IsMultiRegionTrail: true\nEnableLogFileValidation: true',
                        estimated_effort_minutes=10,
                    ),
                )
        
        # S3 Access Logging
        if rule.id == "LOG002" and "S3::Bucket" in parsed.resource_type:
            logging_config = parsed.properties.get("LoggingConfiguration", {})
            if not logging_config:
                return self._create_violation(
                    rule, parsed, resource,
                    "S3 bucket does not have access logging enabled",
                    remediation=RemediationAction(
                        action_type="add_property",
                        description="Enable access logging",
                        resource_name=parsed.logical_id,
                        resource_type=parsed.resource_type,
                        file_path=parsed.file_path,
                        property_path="Properties.LoggingConfiguration",
                        suggested_code='''LoggingConfiguration:
  DestinationBucketName: !Ref LoggingBucket
  LogFilePrefix: access-logs/''',
                        estimated_effort_minutes=15,
                    ),
                )
        
        return None
    
    def _create_violation(
        self,
        rule: PolicyRule,
        parsed: CFNResource,
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
            resource_name=parsed.logical_id,
            resource_type=parsed.resource_type,
            resource_id=str(resource.id),
            provider=CloudProvider.AWS,
            file_path=parsed.file_path,
            regulations=rule.regulations,
            requirement_ids=rule.requirement_ids,
            evidence=evidence or {},
            remediation=remediation,
        )


def analyze_cloudformation_file(
    file_path: str | Path,
    regulations: list[str] | None = None,
) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
    """Convenience function to analyze a CloudFormation template."""
    path = Path(file_path)
    content = path.read_text()
    
    analyzer = CloudFormationAnalyzer()
    return analyzer.analyze(content, str(path), regulations)


def analyze_cloudformation_directory(
    directory: str | Path,
    regulations: list[str] | None = None,
) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
    """Analyze all CloudFormation templates in a directory."""
    dir_path = Path(directory)
    all_resources: list[InfrastructureResource] = []
    all_violations: list[ComplianceViolation] = []
    
    analyzer = CloudFormationAnalyzer()
    
    # Common CloudFormation file patterns
    patterns = ["*.yaml", "*.yml", "*.json", "*.template"]
    
    for pattern in patterns:
        for template_file in dir_path.rglob(pattern):
            try:
                content = template_file.read_text()
                
                # Check if it's a CloudFormation template
                if "AWSTemplateFormatVersion" in content or "Resources" in content:
                    resources, violations = analyzer.analyze(
                        content, str(template_file), regulations
                    )
                    all_resources.extend(resources)
                    all_violations.extend(violations)
            except Exception:
                pass  # Skip files that can't be parsed
    
    return all_resources, all_violations
