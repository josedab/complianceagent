"""Dependency Scanner - Scans for package dependencies and builds graph."""

import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog

from app.services.vendor_risk.models import (
    ComplianceTier,
    DependencyEdge,
    KNOWN_VENDORS,
    RiskLevel,
    Vendor,
    VendorGraph,
    VendorType,
)


logger = structlog.get_logger()


# Package registries
REGISTRIES = {
    "npm": "npmjs.com",
    "pypi": "pypi.org",
    "maven": "maven.org",
    "nuget": "nuget.org",
    "rubygems": "rubygems.org",
    "cargo": "crates.io",
}


class DependencyScanner:
    """Scans repositories for dependencies and builds vendor graph."""

    def __init__(self):
        self._graphs: dict[UUID, VendorGraph] = {}

    async def scan_repository(
        self,
        organization_id: UUID,
        repository_id: UUID | None = None,
        files: dict[str, str] | None = None,
    ) -> VendorGraph:
        """Scan repository for dependencies.
        
        Args:
            organization_id: Organization ID
            repository_id: Repository ID
            files: Dict of filename -> content for dependency files
            
        Returns:
            VendorGraph with all discovered dependencies
        """
        graph = VendorGraph(
            organization_id=organization_id,
            repository_id=repository_id,
        )
        
        if not files:
            files = {}
        
        # Parse each manifest file
        for filename, content in files.items():
            deps = await self._parse_manifest(filename, content)
            for dep in deps:
                if dep.name not in graph.vendors:
                    graph.vendors[dep.name] = dep
                    graph.edges.append(DependencyEdge(
                        source="root",
                        target=dep.name,
                        is_direct=True,
                    ))
        
        # Enrich with known vendor data
        await self._enrich_vendors(graph)
        
        # Calculate statistics
        graph.total_vendors = len(graph.vendors)
        graph.total_dependencies = len(graph.edges)
        graph.source = ", ".join(files.keys()) if files else "unknown"
        
        # Summarize risks
        self._summarize_risks(graph)
        
        # Store
        self._graphs[graph.id] = graph
        
        logger.info(
            "Scanned repository for dependencies",
            organization_id=str(organization_id),
            vendors=graph.total_vendors,
            critical_risks=graph.critical_risks,
        )
        
        return graph

    async def _parse_manifest(
        self,
        filename: str,
        content: str,
    ) -> list[Vendor]:
        """Parse a dependency manifest file."""
        vendors = []
        
        try:
            if filename.endswith("package.json"):
                vendors = self._parse_package_json(content)
            elif filename.endswith("requirements.txt"):
                vendors = self._parse_requirements_txt(content)
            elif filename.endswith("Pipfile") or filename.endswith("Pipfile.lock"):
                vendors = self._parse_pipfile(content)
            elif filename.endswith("pyproject.toml"):
                vendors = self._parse_pyproject_toml(content)
            elif filename.endswith("go.mod"):
                vendors = self._parse_go_mod(content)
            elif filename.endswith("Gemfile"):
                vendors = self._parse_gemfile(content)
            elif filename.endswith("pom.xml"):
                vendors = self._parse_pom_xml(content)
            elif filename.endswith("Cargo.toml"):
                vendors = self._parse_cargo_toml(content)
        except Exception as e:
            logger.warning(f"Failed to parse {filename}: {e}")
        
        return vendors

    def _parse_package_json(self, content: str) -> list[Vendor]:
        """Parse npm package.json."""
        vendors = []
        
        try:
            data = json.loads(content)
            
            # Regular dependencies
            for name, version in data.get("dependencies", {}).items():
                vendors.append(Vendor(
                    name=name,
                    vendor_type=VendorType.PACKAGE,
                    version=self._clean_version(version),
                    registry="npm",
                ))
            
            # Dev dependencies (optional)
            for name, version in data.get("devDependencies", {}).items():
                v = Vendor(
                    name=name,
                    vendor_type=VendorType.PACKAGE,
                    version=self._clean_version(version),
                    registry="npm",
                )
                v.metadata["dev_dependency"] = True
                vendors.append(v)
        except json.JSONDecodeError:
            pass
        
        return vendors

    def _parse_requirements_txt(self, content: str) -> list[Vendor]:
        """Parse Python requirements.txt."""
        vendors = []
        
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            
            # Parse package==version or package>=version etc.
            match = re.match(r'^([a-zA-Z0-9_-]+)([<>=!]+)?(.+)?$', line)
            if match:
                name = match.group(1)
                version = match.group(3) or ""
                vendors.append(Vendor(
                    name=name,
                    vendor_type=VendorType.PACKAGE,
                    version=version,
                    registry="pypi",
                ))
        
        return vendors

    def _parse_pipfile(self, content: str) -> list[Vendor]:
        """Parse Pipfile (simplified)."""
        vendors = []
        in_packages = False
        
        for line in content.split("\n"):
            line = line.strip()
            if line == "[packages]":
                in_packages = True
                continue
            elif line.startswith("["):
                in_packages = False
                continue
            
            if in_packages and "=" in line:
                name = line.split("=")[0].strip().strip('"')
                vendors.append(Vendor(
                    name=name,
                    vendor_type=VendorType.PACKAGE,
                    registry="pypi",
                ))
        
        return vendors

    def _parse_pyproject_toml(self, content: str) -> list[Vendor]:
        """Parse pyproject.toml dependencies (simplified)."""
        vendors = []
        in_deps = False
        
        for line in content.split("\n"):
            if "dependencies" in line and "=" in line:
                in_deps = True
                continue
            elif line.startswith("[") and in_deps:
                in_deps = False
                continue
            
            if in_deps:
                # Try to extract package name
                match = re.search(r'"([a-zA-Z0-9_-]+)', line)
                if match:
                    vendors.append(Vendor(
                        name=match.group(1),
                        vendor_type=VendorType.PACKAGE,
                        registry="pypi",
                    ))
        
        return vendors

    def _parse_go_mod(self, content: str) -> list[Vendor]:
        """Parse Go go.mod."""
        vendors = []
        
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("require ") or (line and not line.startswith("//") and "/" in line):
                match = re.match(r'(?:require\s+)?([^\s]+)\s+([^\s]+)', line)
                if match:
                    vendors.append(Vendor(
                        name=match.group(1),
                        vendor_type=VendorType.PACKAGE,
                        version=match.group(2),
                        registry="go",
                    ))
        
        return vendors

    def _parse_gemfile(self, content: str) -> list[Vendor]:
        """Parse Ruby Gemfile."""
        vendors = []
        
        for line in content.split("\n"):
            match = re.match(r"^\s*gem\s+['\"]([^'\"]+)['\"]", line)
            if match:
                vendors.append(Vendor(
                    name=match.group(1),
                    vendor_type=VendorType.PACKAGE,
                    registry="rubygems",
                ))
        
        return vendors

    def _parse_pom_xml(self, content: str) -> list[Vendor]:
        """Parse Maven pom.xml (simplified)."""
        vendors = []
        
        # Simple regex for artifactId extraction
        matches = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
        for name in matches:
            if name and not name.startswith("$"):
                vendors.append(Vendor(
                    name=name,
                    vendor_type=VendorType.PACKAGE,
                    registry="maven",
                ))
        
        return vendors

    def _parse_cargo_toml(self, content: str) -> list[Vendor]:
        """Parse Rust Cargo.toml."""
        vendors = []
        in_deps = False
        
        for line in content.split("\n"):
            if "[dependencies]" in line:
                in_deps = True
                continue
            elif line.startswith("["):
                in_deps = False
                continue
            
            if in_deps and "=" in line:
                name = line.split("=")[0].strip()
                if name:
                    vendors.append(Vendor(
                        name=name,
                        vendor_type=VendorType.PACKAGE,
                        registry="cargo",
                    ))
        
        return vendors

    def _clean_version(self, version: str) -> str:
        """Clean version string."""
        return version.strip("^~>=<")

    async def _enrich_vendors(self, graph: VendorGraph) -> None:
        """Enrich vendors with known data."""
        for name, vendor in graph.vendors.items():
            name_lower = name.lower()
            
            # Check known vendors
            if name_lower in KNOWN_VENDORS:
                known = KNOWN_VENDORS[name_lower]
                vendor.name = known.get("name", vendor.name)
                vendor.vendor_type = known.get("type", vendor.vendor_type)
                vendor.risk_level = known.get("risk_level", RiskLevel.UNKNOWN)
                vendor.data_processing = known.get("data_processing", [])
                
                certs = known.get("certifications", [])
                if certs:
                    vendor.compliance_tier = ComplianceTier.FULLY_CERTIFIED
                    graph.certified_vendors += 1
                else:
                    graph.uncertified_vendors += 1
            else:
                # Default to unknown
                vendor.compliance_tier = ComplianceTier.UNKNOWN
                graph.uncertified_vendors += 1
                
                # Infer some info from name
                if any(kw in name_lower for kw in ["auth", "oauth", "jwt"]):
                    vendor.data_processing.append("credentials")
                if any(kw in name_lower for kw in ["analytics", "tracking"]):
                    vendor.data_processing.append("personal_data")

    def _summarize_risks(self, graph: VendorGraph) -> None:
        """Summarize risk levels in graph."""
        for vendor in graph.vendors.values():
            if vendor.risk_level == RiskLevel.CRITICAL:
                graph.critical_risks += 1
            elif vendor.risk_level == RiskLevel.HIGH:
                graph.high_risks += 1
            elif vendor.risk_level == RiskLevel.MEDIUM:
                graph.medium_risks += 1
        
        # Overall risk
        if graph.critical_risks > 0:
            graph.overall_risk = RiskLevel.CRITICAL
        elif graph.high_risks > 0:
            graph.overall_risk = RiskLevel.HIGH
        elif graph.medium_risks > 0:
            graph.overall_risk = RiskLevel.MEDIUM
        elif graph.total_vendors > 0:
            graph.overall_risk = RiskLevel.LOW
        else:
            graph.overall_risk = RiskLevel.MINIMAL

    async def get_graph(self, graph_id: UUID) -> VendorGraph | None:
        """Get a vendor graph by ID."""
        return self._graphs.get(graph_id)


# Global instance
_scanner: DependencyScanner | None = None


def get_dependency_scanner() -> DependencyScanner:
    """Get or create dependency scanner."""
    global _scanner
    if _scanner is None:
        _scanner = DependencyScanner()
    return _scanner
