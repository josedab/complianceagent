"""Main infrastructure compliance analyzer service."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from .cloudformation import CloudFormationAnalyzer
from .kubernetes import KubernetesAnalyzer
from .models import (
    CloudProvider,
    ComplianceCategory,
    ComplianceViolation,
    InfrastructureAnalysisResult,
    InfrastructureResource,
    InfrastructureType,
    PolicyRule,
    ViolationSeverity,
)
from .terraform import TerraformAnalyzer

logger = structlog.get_logger(__name__)


class InfrastructureAnalyzer:
    """Unified infrastructure compliance analyzer.
    
    Analyzes Terraform, Kubernetes, and CloudFormation configurations
    for compliance violations across multiple regulations.
    
    Example:
        analyzer = InfrastructureAnalyzer()
        
        # Analyze a single file
        result = analyzer.analyze_file("infrastructure/main.tf")
        
        # Analyze a directory
        result = analyzer.analyze_directory("infrastructure/", regulations=["GDPR", "SOC2"])
        
        # Analyze content directly
        result = analyzer.analyze_content(
            content=terraform_code,
            infrastructure_type=InfrastructureType.TERRAFORM,
        )
    """
    
    def __init__(
        self,
        policy_rules: list[PolicyRule] | None = None,
        enabled_regulations: list[str] | None = None,
    ):
        """Initialize the analyzer.
        
        Args:
            policy_rules: Custom policy rules (uses defaults if not provided)
            enabled_regulations: Filter to only these regulations
        """
        self.policy_rules = policy_rules
        self.enabled_regulations = enabled_regulations
        
        # Initialize sub-analyzers
        self._terraform = TerraformAnalyzer(policy_rules)
        self._kubernetes = KubernetesAnalyzer(policy_rules)
        self._cloudformation = CloudFormationAnalyzer(policy_rules)
    
    def analyze_content(
        self,
        content: str,
        infrastructure_type: InfrastructureType,
        file_path: str = "inline",
        regulations: list[str] | None = None,
    ) -> InfrastructureAnalysisResult:
        """Analyze infrastructure configuration content.
        
        Args:
            content: Configuration content
            infrastructure_type: Type of infrastructure configuration
            file_path: Virtual file path for reporting
            regulations: Specific regulations to check
        
        Returns:
            InfrastructureAnalysisResult with resources and violations
        """
        start_time = time.time()
        
        active_regulations = regulations or self.enabled_regulations
        
        resources: list[InfrastructureResource] = []
        violations: list[ComplianceViolation] = []
        
        # Route to appropriate analyzer
        if infrastructure_type == InfrastructureType.TERRAFORM:
            resources, violations = self._terraform.analyze(
                content, file_path, active_regulations
            )
        elif infrastructure_type == InfrastructureType.KUBERNETES:
            resources, violations = self._kubernetes.analyze(
                content, file_path, active_regulations
            )
        elif infrastructure_type == InfrastructureType.CLOUDFORMATION:
            resources, violations = self._cloudformation.analyze(
                content, file_path, active_regulations
            )
        elif infrastructure_type == InfrastructureType.HELM:
            # Helm charts are Kubernetes manifests with templating
            resources, violations = self._kubernetes.analyze(
                content, file_path, active_regulations
            )
        else:
            logger.warning(
                "unsupported_infrastructure_type",
                type=infrastructure_type.value,
            )
        
        # Build result
        result = self._build_result(
            resources=resources,
            violations=violations,
            analyzed_files=[file_path],
            start_time=start_time,
        )
        
        logger.info(
            "infrastructure_analysis_complete",
            file=file_path,
            type=infrastructure_type.value,
            resources=result.total_resources,
            violations=len(result.violations),
            score=result.compliance_score,
        )
        
        return result
    
    def analyze_file(
        self,
        file_path: str | Path,
        regulations: list[str] | None = None,
    ) -> InfrastructureAnalysisResult:
        """Analyze a single infrastructure configuration file.
        
        Args:
            file_path: Path to the configuration file
            regulations: Specific regulations to check
        
        Returns:
            InfrastructureAnalysisResult with resources and violations
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error("file_not_found", path=str(path))
            return InfrastructureAnalysisResult(analyzed_files=[str(path)])
        
        # Detect infrastructure type from file extension/content
        infrastructure_type = self._detect_type(path)
        
        content = path.read_text()
        return self.analyze_content(
            content=content,
            infrastructure_type=infrastructure_type,
            file_path=str(path),
            regulations=regulations,
        )
    
    def analyze_directory(
        self,
        directory: str | Path,
        regulations: list[str] | None = None,
        recursive: bool = True,
    ) -> InfrastructureAnalysisResult:
        """Analyze all infrastructure files in a directory.
        
        Args:
            directory: Directory to scan
            regulations: Specific regulations to check
            recursive: Whether to scan subdirectories
        
        Returns:
            Combined InfrastructureAnalysisResult
        """
        start_time = time.time()
        dir_path = Path(directory)
        
        if not dir_path.is_dir():
            logger.error("directory_not_found", path=str(dir_path))
            return InfrastructureAnalysisResult()
        
        active_regulations = regulations or self.enabled_regulations
        
        all_resources: list[InfrastructureResource] = []
        all_violations: list[ComplianceViolation] = []
        analyzed_files: list[str] = []
        
        # Find and analyze files
        patterns = {
            "*.tf": InfrastructureType.TERRAFORM,
            "*.tfvars": InfrastructureType.TERRAFORM,
            "*.yaml": None,  # Detect based on content
            "*.yml": None,
            "*.json": None,
            "*.template": InfrastructureType.CLOUDFORMATION,
        }
        
        glob_method = dir_path.rglob if recursive else dir_path.glob
        
        for pattern, default_type in patterns.items():
            for file_path in glob_method(pattern):
                try:
                    content = file_path.read_text()
                    infra_type = default_type or self._detect_type_from_content(content, file_path)
                    
                    if infra_type is None:
                        continue
                    
                    # Get appropriate analyzer
                    resources, violations = self._analyze_with_type(
                        content, str(file_path), infra_type, active_regulations
                    )
                    
                    all_resources.extend(resources)
                    all_violations.extend(violations)
                    analyzed_files.append(str(file_path))
                    
                except Exception as e:
                    logger.warning(
                        "file_analysis_failed",
                        path=str(file_path),
                        error=str(e),
                    )
        
        result = self._build_result(
            resources=all_resources,
            violations=all_violations,
            analyzed_files=analyzed_files,
            start_time=start_time,
        )
        
        logger.info(
            "directory_analysis_complete",
            directory=str(dir_path),
            files=len(analyzed_files),
            resources=result.total_resources,
            violations=len(result.violations),
            score=result.compliance_score,
        )
        
        return result
    
    def _detect_type(self, file_path: Path) -> InfrastructureType:
        """Detect infrastructure type from file path."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        if suffix == ".tf" or suffix == ".tfvars":
            return InfrastructureType.TERRAFORM
        
        if "chart.yaml" in name or "values.yaml" in name:
            return InfrastructureType.HELM
        
        if suffix == ".template":
            return InfrastructureType.CLOUDFORMATION
        
        # Need to check content for YAML/JSON files
        try:
            content = file_path.read_text()
            detected = self._detect_type_from_content(content, file_path)
            if detected:
                return detected
        except Exception:
            pass
        
        # Default based on common patterns
        if any(x in str(file_path).lower() for x in ["terraform", "infra"]):
            return InfrastructureType.TERRAFORM
        if any(x in str(file_path).lower() for x in ["k8s", "kubernetes", "deploy"]):
            return InfrastructureType.KUBERNETES
        
        return InfrastructureType.KUBERNETES  # Default for YAML
    
    def _detect_type_from_content(
        self,
        content: str,
        file_path: Path,
    ) -> InfrastructureType | None:
        """Detect infrastructure type from content."""
        # CloudFormation markers
        if "AWSTemplateFormatVersion" in content:
            return InfrastructureType.CLOUDFORMATION
        if '"Resources"' in content and '"Type"' in content and "AWS::" in content:
            return InfrastructureType.CLOUDFORMATION
        
        # Kubernetes markers
        if "apiVersion:" in content and "kind:" in content:
            return InfrastructureType.KUBERNETES
        
        # Terraform markers
        if "resource " in content and "{" in content:
            return InfrastructureType.TERRAFORM
        if 'provider "' in content:
            return InfrastructureType.TERRAFORM
        
        # Helm markers
        if "{{" in content and "}}" in content:
            return InfrastructureType.HELM
        
        return None
    
    def _analyze_with_type(
        self,
        content: str,
        file_path: str,
        infra_type: InfrastructureType,
        regulations: list[str] | None,
    ) -> tuple[list[InfrastructureResource], list[ComplianceViolation]]:
        """Route to appropriate analyzer."""
        if infra_type == InfrastructureType.TERRAFORM:
            return self._terraform.analyze(content, file_path, regulations)
        elif infra_type in (InfrastructureType.KUBERNETES, InfrastructureType.HELM):
            return self._kubernetes.analyze(content, file_path, regulations)
        elif infra_type == InfrastructureType.CLOUDFORMATION:
            return self._cloudformation.analyze(content, file_path, regulations)
        return [], []
    
    def _build_result(
        self,
        resources: list[InfrastructureResource],
        violations: list[ComplianceViolation],
        analyzed_files: list[str],
        start_time: float,
    ) -> InfrastructureAnalysisResult:
        """Build analysis result from collected data."""
        # Count violations by severity
        severity_counts = {s: 0 for s in ViolationSeverity}
        for v in violations:
            severity_counts[v.severity] += 1
        
        # Find non-compliant resources
        violating_resource_ids = {v.resource_id for v in violations}
        non_compliant_count = len(violating_resource_ids)
        
        # Build provider breakdown
        provider_breakdown: dict[str, dict[str, int]] = {}
        for resource in resources:
            provider = resource.provider.value
            if provider not in provider_breakdown:
                provider_breakdown[provider] = {"resources": 0, "violations": 0}
            provider_breakdown[provider]["resources"] += 1
        
        for violation in violations:
            provider = violation.provider.value
            if provider in provider_breakdown:
                provider_breakdown[provider]["violations"] += 1
        
        # Build category breakdown
        category_breakdown: dict[str, dict[str, int]] = {}
        for violation in violations:
            category = violation.category.value
            if category not in category_breakdown:
                category_breakdown[category] = {"count": 0, "critical": 0, "high": 0}
            category_breakdown[category]["count"] += 1
            if violation.severity == ViolationSeverity.CRITICAL:
                category_breakdown[category]["critical"] += 1
            elif violation.severity == ViolationSeverity.HIGH:
                category_breakdown[category]["high"] += 1
        
        # Build regulation breakdown
        regulation_breakdown: dict[str, dict[str, int]] = {}
        for violation in violations:
            for reg in violation.regulations:
                if reg not in regulation_breakdown:
                    regulation_breakdown[reg] = {"count": 0}
                regulation_breakdown[reg]["count"] += 1
        
        result = InfrastructureAnalysisResult(
            total_resources=len(resources),
            compliant_resources=len(resources) - non_compliant_count,
            non_compliant_resources=non_compliant_count,
            critical_count=severity_counts[ViolationSeverity.CRITICAL],
            high_count=severity_counts[ViolationSeverity.HIGH],
            medium_count=severity_counts[ViolationSeverity.MEDIUM],
            low_count=severity_counts[ViolationSeverity.LOW],
            info_count=severity_counts[ViolationSeverity.INFO],
            resources=resources,
            violations=violations,
            provider_breakdown=provider_breakdown,
            category_breakdown=category_breakdown,
            regulation_breakdown=regulation_breakdown,
            analyzed_files=analyzed_files,
            analysis_duration_ms=int((time.time() - start_time) * 1000),
        )
        
        result.calculate_score()
        return result
    
    def get_policy_rules(self) -> list[PolicyRule]:
        """Get all policy rules."""
        from .models import DEFAULT_POLICY_RULES
        return self.policy_rules or DEFAULT_POLICY_RULES
    
    def add_policy_rule(self, rule: PolicyRule) -> None:
        """Add a custom policy rule."""
        from .models import DEFAULT_POLICY_RULES
        
        if self.policy_rules is None:
            self.policy_rules = list(DEFAULT_POLICY_RULES)
        
        self.policy_rules.append(rule)
        
        # Update sub-analyzers
        self._terraform = TerraformAnalyzer(self.policy_rules)
        self._kubernetes = KubernetesAnalyzer(self.policy_rules)
        self._cloudformation = CloudFormationAnalyzer(self.policy_rules)


# Global singleton
_infrastructure_analyzer: InfrastructureAnalyzer | None = None


def get_infrastructure_analyzer() -> InfrastructureAnalyzer:
    """Get the global infrastructure analyzer instance."""
    global _infrastructure_analyzer
    if _infrastructure_analyzer is None:
        _infrastructure_analyzer = InfrastructureAnalyzer()
    return _infrastructure_analyzer


def set_infrastructure_analyzer(analyzer: InfrastructureAnalyzer) -> None:
    """Set the global infrastructure analyzer instance."""
    global _infrastructure_analyzer
    _infrastructure_analyzer = analyzer
