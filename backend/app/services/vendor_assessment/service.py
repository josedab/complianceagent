"""Vendor and dependency compliance assessment service."""

import re
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.vendor_assessment.models import (
    CERTIFICATION_COMPLIANCE_MAP,
    LICENSE_RISKS,
    Dependency,
    DependencyRisk,
    DependencyRiskLevel,
    DependencyScanResult,
    Vendor,
    VendorAssessment,
    VendorRiskLevel,
    VendorStatus,
)


logger = structlog.get_logger()


class VendorAssessmentService:
    """Service for vendor and dependency compliance assessment."""
    
    def __init__(self, db: AsyncSession, copilot: Any = None):
        self.db = db
        self.copilot = copilot
        self._vendors: dict[UUID, Vendor] = {}
        self._assessments: dict[UUID, VendorAssessment] = {}
    
    # --- Vendor Management ---
    
    async def create_vendor(
        self,
        organization_id: UUID,
        name: str,
        vendor_type: str,
        created_by: UUID,
        description: str = "",
        website: str = "",
        category: str = "",
        certifications: list[str] | None = None,
        data_types_processed: list[str] | None = None,
        data_processing_locations: list[str] | None = None,
    ) -> Vendor:
        """Create a new vendor record."""
        vendor = Vendor(
            organization_id=organization_id,
            name=name,
            description=description,
            website=website,
            vendor_type=vendor_type,
            category=category,
            certifications=certifications or [],
            data_types_processed=data_types_processed or [],
            data_processing_locations=data_processing_locations or [],
            created_by=created_by,
        )
        
        # Calculate initial risk level based on data handling
        vendor.risk_level = self._calculate_vendor_risk_level(vendor)
        
        self._vendors[vendor.id] = vendor
        
        logger.info(
            "vendor_created",
            vendor_id=str(vendor.id),
            name=name,
            risk_level=vendor.risk_level.value,
        )
        
        return vendor
    
    async def get_vendor(self, vendor_id: UUID) -> Vendor | None:
        """Get vendor by ID."""
        return self._vendors.get(vendor_id)
    
    async def list_vendors(
        self,
        organization_id: UUID,
        status: VendorStatus | None = None,
        risk_level: VendorRiskLevel | None = None,
    ) -> list[Vendor]:
        """List vendors for an organization."""
        vendors = [
            v for v in self._vendors.values()
            if v.organization_id == organization_id
        ]
        
        if status:
            vendors = [v for v in vendors if v.status == status]
        
        if risk_level:
            vendors = [v for v in vendors if v.risk_level == risk_level]
        
        return vendors
    
    async def update_vendor(
        self,
        vendor_id: UUID,
        **updates,
    ) -> Vendor | None:
        """Update vendor details."""
        vendor = self._vendors.get(vendor_id)
        if not vendor:
            return None
        
        for key, value in updates.items():
            if hasattr(vendor, key) and value is not None:
                setattr(vendor, key, value)
        
        vendor.updated_at = datetime.utcnow()
        vendor.risk_level = self._calculate_vendor_risk_level(vendor)
        
        return vendor
    
    # --- Vendor Assessment ---
    
    async def assess_vendor(
        self,
        vendor_id: UUID,
        organization_id: UUID,
        assessor: str,
        assessment_type: str = "initial",
        target_frameworks: list[str] | None = None,
    ) -> VendorAssessment:
        """Perform compliance assessment on a vendor."""
        vendor = self._vendors.get(vendor_id)
        if not vendor:
            raise ValueError(f"Vendor not found: {vendor_id}")
        
        frameworks = target_frameworks or ["SOC2", "GDPR"]
        
        assessment = VendorAssessment(
            vendor_id=vendor_id,
            organization_id=organization_id,
            assessment_type=assessment_type,
            assessor=assessor,
        )
        
        # Calculate scores
        assessment.security_score = self._calculate_security_score(vendor)
        assessment.privacy_score = self._calculate_privacy_score(vendor)
        assessment.operational_score = self._calculate_operational_score(vendor)
        assessment.financial_score = self._calculate_financial_score(vendor)
        
        assessment.overall_score = (
            assessment.security_score * 0.35 +
            assessment.privacy_score * 0.30 +
            assessment.operational_score * 0.20 +
            assessment.financial_score * 0.15
        )
        
        # Identify risk factors
        assessment.risk_factors = self._identify_risk_factors(vendor)
        
        # Framework-specific assessments
        for framework in frameworks:
            assessment.framework_assessments[framework] = (
                self._assess_framework_compliance(vendor, framework)
            )
        
        # Identify compliance gaps
        assessment.compliance_gaps = self._identify_compliance_gaps(
            vendor, assessment.framework_assessments
        )
        
        # Generate recommendations
        assessment.required_actions = self._generate_required_actions(
            vendor, assessment.compliance_gaps
        )
        
        # Determine risk level and recommendation
        assessment.risk_level = self._determine_assessment_risk(assessment)
        assessment.recommendation = self._generate_recommendation(assessment)
        
        # Set status based on assessment
        if assessment.overall_score >= 80 and not assessment.compliance_gaps:
            assessment.status = VendorStatus.APPROVED
            assessment.valid_until = datetime.utcnow() + timedelta(days=365)
        elif assessment.overall_score >= 60:
            assessment.status = VendorStatus.CONDITIONALLY_APPROVED
            assessment.conditions = [
                gap["description"] for gap in assessment.compliance_gaps[:3]
            ]
            assessment.valid_until = datetime.utcnow() + timedelta(days=90)
        else:
            assessment.status = VendorStatus.REJECTED
        
        self._assessments[assessment.id] = assessment
        
        # Update vendor status
        vendor.status = assessment.status
        vendor.last_assessment_date = datetime.utcnow()
        vendor.next_review_date = assessment.valid_until
        
        logger.info(
            "vendor_assessed",
            vendor_id=str(vendor_id),
            assessment_id=str(assessment.id),
            score=assessment.overall_score,
            status=assessment.status.value,
        )
        
        return assessment
    
    async def get_assessment(self, assessment_id: UUID) -> VendorAssessment | None:
        """Get assessment by ID."""
        return self._assessments.get(assessment_id)
    
    async def list_assessments(
        self,
        organization_id: UUID,
        vendor_id: UUID | None = None,
    ) -> list[VendorAssessment]:
        """List assessments."""
        assessments = [
            a for a in self._assessments.values()
            if a.organization_id == organization_id
        ]
        
        if vendor_id:
            assessments = [a for a in assessments if a.vendor_id == vendor_id]
        
        return sorted(assessments, key=lambda a: a.assessment_date, reverse=True)
    
    # --- Dependency Scanning ---
    
    async def scan_dependencies(
        self,
        repository_id: UUID,
        organization_id: UUID,
        manifest_content: str,
        package_manager: str = "npm",
        target_frameworks: list[str] | None = None,
    ) -> DependencyScanResult:
        """Scan dependencies for compliance risks."""
        result = DependencyScanResult(
            repository_id=repository_id,
            organization_id=organization_id,
        )
        
        # Parse dependencies based on package manager
        dependencies = self._parse_dependencies(manifest_content, package_manager)
        
        result.total_dependencies = len(dependencies)
        result.direct_dependencies = len([d for d in dependencies if not d.get("transitive")])
        result.transitive_dependencies = result.total_dependencies - result.direct_dependencies
        
        # Assess each dependency
        for dep_info in dependencies:
            dep = Dependency(
                name=dep_info.get("name", ""),
                version=dep_info.get("version", ""),
                package_manager=package_manager,
                license=dep_info.get("license", "Unknown"),
            )
            
            # Simulate additional metadata
            dep.license_risk = LICENSE_RISKS.get(dep.license, "medium")
            dep.has_known_vulnerabilities = self._check_vulnerabilities(dep)
            dep.is_outdated = self._check_outdated(dep)
            
            # Assess risk
            risk = self._assess_dependency_risk(dep, target_frameworks or ["SOC2", "GDPR"])
            result.dependency_risks.append(risk)
            
            # Update counters
            if risk.risk_level == DependencyRiskLevel.CRITICAL:
                result.critical_count += 1
            elif risk.risk_level == DependencyRiskLevel.HIGH:
                result.high_count += 1
            elif risk.risk_level == DependencyRiskLevel.MEDIUM:
                result.medium_count += 1
            else:
                result.low_count += 1
            
            if dep.has_known_vulnerabilities:
                result.total_vulnerabilities += dep.vulnerability_count
                if risk.risk_level == DependencyRiskLevel.CRITICAL:
                    result.critical_vulnerabilities += 1
                elif risk.risk_level == DependencyRiskLevel.HIGH:
                    result.high_vulnerabilities += 1
            
            if dep.license_risk in ["high", "critical"]:
                result.license_violations += 1
            elif dep.license == "Unknown":
                result.unknown_licenses += 1
        
        # Calculate health score
        total = result.total_dependencies or 1
        penalty = (
            result.critical_count * 10 +
            result.high_count * 5 +
            result.medium_count * 2 +
            result.license_violations * 5
        )
        result.health_score = max(0, 100 - (penalty / total * 10))
        
        # Determine compliance impact
        result.frameworks_affected = self._determine_affected_frameworks(result)
        result.compliance_impact = self._calculate_compliance_impact(result)
        
        logger.info(
            "dependency_scan_complete",
            repository_id=str(repository_id),
            total=result.total_dependencies,
            critical=result.critical_count,
            health_score=result.health_score,
        )
        
        return result
    
    def _parse_dependencies(
        self,
        manifest_content: str,
        package_manager: str,
    ) -> list[dict]:
        """Parse dependencies from manifest file."""
        dependencies = []
        
        if package_manager == "npm":
            # Simple parsing for package.json format
            import json
            try:
                data = json.loads(manifest_content)
                for name, version in data.get("dependencies", {}).items():
                    dependencies.append({
                        "name": name,
                        "version": version.lstrip("^~>=<"),
                        "license": self._lookup_license(name, package_manager),
                    })
                for name, version in data.get("devDependencies", {}).items():
                    dependencies.append({
                        "name": name,
                        "version": version.lstrip("^~>=<"),
                        "license": self._lookup_license(name, package_manager),
                        "dev": True,
                    })
            except json.JSONDecodeError:
                pass
        
        elif package_manager == "pip":
            # Parse requirements.txt format
            for line in manifest_content.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    match = re.match(r'^([a-zA-Z0-9_-]+)([=<>!~].*)?', line)
                    if match:
                        name = match.group(1)
                        version = match.group(2) or ""
                        version = re.sub(r'[=<>!~]', '', version)
                        dependencies.append({
                            "name": name,
                            "version": version,
                            "license": self._lookup_license(name, package_manager),
                        })
        
        elif package_manager == "maven":
            # Simple XML parsing for pom.xml
            for match in re.finditer(
                r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]+)</version>',
                manifest_content,
                re.DOTALL
            ):
                dependencies.append({
                    "name": f"{match.group(1)}:{match.group(2)}",
                    "version": match.group(3),
                    "license": self._lookup_license(match.group(2), package_manager),
                })
        
        return dependencies
    
    def _lookup_license(self, package_name: str, package_manager: str) -> str:
        """Look up license for a package (simulated)."""
        # Known popular packages
        known_licenses = {
            "react": "MIT",
            "lodash": "MIT",
            "express": "MIT",
            "axios": "MIT",
            "typescript": "Apache-2.0",
            "requests": "Apache-2.0",
            "django": "BSD-3-Clause",
            "flask": "BSD-3-Clause",
            "numpy": "BSD-3-Clause",
            "pandas": "BSD-3-Clause",
            "spring-boot": "Apache-2.0",
            "hibernate": "LGPL-2.1",
        }
        return known_licenses.get(package_name.lower(), "MIT")
    
    def _check_vulnerabilities(self, dep: Dependency) -> bool:
        """Check if dependency has known vulnerabilities (simulated)."""
        # Simulate vulnerability check
        known_vulnerable = {"lodash": True, "moment": True}
        if dep.name.lower() in known_vulnerable:
            dep.vulnerability_count = 2
            return True
        return False
    
    def _check_outdated(self, dep: Dependency) -> bool:
        """Check if dependency is outdated (simulated)."""
        # Simulate outdated check
        return False
    
    def _assess_dependency_risk(
        self,
        dep: Dependency,
        frameworks: list[str],
    ) -> DependencyRisk:
        """Assess risk for a single dependency."""
        risk = DependencyRisk(dependency=dep)
        
        score = 0
        
        # Vulnerability risk
        if dep.has_known_vulnerabilities:
            score += 40
            risk.vulnerabilities.append({
                "severity": "high",
                "count": dep.vulnerability_count,
                "description": "Known security vulnerabilities",
            })
            risk.recommendations.append(f"Update {dep.name} to latest version")
        
        # License risk
        if dep.license_risk == "critical":
            score += 30
            risk.license_issues.append(f"AGPL/SSPL license requires source disclosure")
            risk.compliance_issues.append("May conflict with proprietary licensing")
        elif dep.license_risk == "high":
            score += 20
            risk.license_issues.append("GPL license has copyleft requirements")
        elif dep.license == "Unknown":
            score += 15
            risk.license_issues.append("Unknown license - legal review required")
        
        # Maintenance risk
        if dep.is_deprecated:
            score += 20
            risk.maintenance_issues.append("Package is deprecated")
            risk.recommendations.append(f"Find alternative for {dep.name}")
        
        if dep.is_outdated:
            score += 10
            risk.maintenance_issues.append("Package is outdated")
        
        # Determine risk level
        risk.risk_score = min(100, score)
        if score >= 50:
            risk.risk_level = DependencyRiskLevel.CRITICAL
            risk.remediation_priority = 1
        elif score >= 30:
            risk.risk_level = DependencyRiskLevel.HIGH
            risk.remediation_priority = 2
        elif score >= 15:
            risk.risk_level = DependencyRiskLevel.MEDIUM
            risk.remediation_priority = 3
        else:
            risk.risk_level = DependencyRiskLevel.LOW
            risk.remediation_priority = 4
        
        return risk
    
    # --- Scoring Helpers ---
    
    def _calculate_vendor_risk_level(self, vendor: Vendor) -> VendorRiskLevel:
        """Calculate vendor risk level based on data handling."""
        score = 0
        
        # Data types risk
        sensitive_data = {"PII", "PHI", "PCI", "financial", "health"}
        if any(d in sensitive_data for d in vendor.data_types_processed):
            score += 30
        
        # Data access level
        if vendor.data_access_level in ["full", "admin"]:
            score += 20
        elif vendor.data_access_level in ["read_write", "modify"]:
            score += 10
        
        # Location risk
        high_risk_locations = {"China", "Russia"}
        if any(loc in high_risk_locations for loc in vendor.data_processing_locations):
            score += 20
        
        # Certification bonus (reduces risk)
        if vendor.certifications:
            score -= len(vendor.certifications) * 5
        
        score = max(0, score)
        
        if score >= 40:
            return VendorRiskLevel.CRITICAL
        elif score >= 30:
            return VendorRiskLevel.HIGH
        elif score >= 20:
            return VendorRiskLevel.MEDIUM
        elif score >= 10:
            return VendorRiskLevel.LOW
        return VendorRiskLevel.MINIMAL
    
    def _calculate_security_score(self, vendor: Vendor) -> float:
        """Calculate security score for vendor."""
        score = 50.0
        
        security_certs = {"SOC2_TYPE_2", "SOC2_TYPE_1", "ISO_27001", "ISO_27017"}
        for cert in vendor.certifications:
            if cert in security_certs:
                score += 15
        
        return min(100, score)
    
    def _calculate_privacy_score(self, vendor: Vendor) -> float:
        """Calculate privacy score for vendor."""
        score = 50.0
        
        privacy_certs = {"ISO_27018", "GDPR_COMPLIANT", "PRIVACY_SHIELD"}
        for cert in vendor.certifications:
            if cert in privacy_certs:
                score += 20
        
        # Penalize risky locations
        if any(loc in ["China", "Russia"] for loc in vendor.data_processing_locations):
            score -= 20
        
        return max(0, min(100, score))
    
    def _calculate_operational_score(self, vendor: Vendor) -> float:
        """Calculate operational score for vendor."""
        score = 70.0
        
        # Subprocessors complexity
        if len(vendor.subprocessors) > 5:
            score -= 10
        
        return min(100, score)
    
    def _calculate_financial_score(self, vendor: Vendor) -> float:
        """Calculate financial stability score (simulated)."""
        return 75.0
    
    def _identify_risk_factors(self, vendor: Vendor) -> list[dict]:
        """Identify risk factors for vendor."""
        factors = []
        
        if not vendor.certifications:
            factors.append({
                "category": "security",
                "severity": "high",
                "description": "No security certifications",
            })
        
        sensitive_data = {"PII", "PHI", "PCI"}
        if any(d in sensitive_data for d in vendor.data_types_processed):
            factors.append({
                "category": "data",
                "severity": "medium",
                "description": "Processes sensitive data types",
            })
        
        return factors
    
    def _assess_framework_compliance(
        self,
        vendor: Vendor,
        framework: str,
    ) -> dict:
        """Assess vendor compliance with specific framework."""
        assessment = {
            "framework": framework,
            "compliant": False,
            "coverage": 0.0,
            "gaps": [],
        }
        
        required_certs = [
            cert for cert, frameworks in CERTIFICATION_COMPLIANCE_MAP.items()
            if framework in frameworks
        ]
        
        matched = [c for c in vendor.certifications if c in required_certs]
        
        if matched:
            assessment["compliant"] = True
            assessment["coverage"] = len(matched) / max(1, len(required_certs)) * 100
        else:
            assessment["gaps"].append(f"Missing {framework}-related certifications")
        
        return assessment
    
    def _identify_compliance_gaps(
        self,
        vendor: Vendor,
        framework_assessments: dict,
    ) -> list[dict]:
        """Identify compliance gaps."""
        gaps = []
        
        for framework, assessment in framework_assessments.items():
            if not assessment.get("compliant"):
                for gap in assessment.get("gaps", []):
                    gaps.append({
                        "framework": framework,
                        "description": gap,
                        "severity": "high",
                    })
        
        return gaps
    
    def _generate_required_actions(
        self,
        vendor: Vendor,
        gaps: list[dict],
    ) -> list[str]:
        """Generate required actions for vendor."""
        actions = []
        
        for gap in gaps:
            if "certification" in gap["description"].lower():
                actions.append(f"Request {gap['framework']} compliance documentation")
        
        if not vendor.certifications:
            actions.append("Request SOC2 Type 2 report")
        
        return actions
    
    def _determine_assessment_risk(self, assessment: VendorAssessment) -> VendorRiskLevel:
        """Determine overall assessment risk level."""
        if assessment.overall_score >= 80:
            return VendorRiskLevel.LOW
        elif assessment.overall_score >= 60:
            return VendorRiskLevel.MEDIUM
        elif assessment.overall_score >= 40:
            return VendorRiskLevel.HIGH
        return VendorRiskLevel.CRITICAL
    
    def _generate_recommendation(self, assessment: VendorAssessment) -> str:
        """Generate assessment recommendation."""
        if assessment.overall_score >= 80:
            return "Approve vendor for use with standard monitoring"
        elif assessment.overall_score >= 60:
            return "Approve with conditions - address compliance gaps within 90 days"
        elif assessment.overall_score >= 40:
            return "Defer approval pending security improvements"
        return "Do not approve - significant compliance concerns"
    
    def _determine_affected_frameworks(self, result: DependencyScanResult) -> list[str]:
        """Determine which frameworks are affected by dependency issues."""
        frameworks = []
        
        if result.license_violations > 0:
            frameworks.extend(["SOC2", "GDPR"])
        
        if result.critical_vulnerabilities > 0:
            frameworks.extend(["SOC2", "HIPAA", "PCI_DSS"])
        
        return list(set(frameworks))
    
    def _calculate_compliance_impact(
        self,
        result: DependencyScanResult,
    ) -> dict[str, str]:
        """Calculate compliance impact of dependency issues."""
        impact = {}
        
        if result.critical_count > 0:
            impact["SOC2"] = "Critical vulnerabilities violate CC7.1 (Vulnerability Management)"
        
        if result.license_violations > 0:
            impact["legal"] = "License violations may have legal implications"
        
        return impact
