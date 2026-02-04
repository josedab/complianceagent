"""SBOM Generator - Creates Software Bill of Materials from dependency files."""

import hashlib
import json
import re
import time
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.services.sbom.models import (
    ComponentVulnerability,
    LicenseRisk,
    LICENSE_COMPLIANCE_INFO,
    SBOMComponent,
    SBOMDocument,
    SBOMFormat,
    VulnerabilitySeverity,
)


logger = structlog.get_logger()


# Known package licenses (sample data - in production, this would query registries)
KNOWN_LICENSES = {
    # Python packages
    "requests": "Apache-2.0",
    "flask": "BSD-3-Clause",
    "django": "BSD-3-Clause",
    "fastapi": "MIT",
    "pydantic": "MIT",
    "sqlalchemy": "MIT",
    "celery": "BSD-3-Clause",
    "redis": "MIT",
    "numpy": "BSD-3-Clause",
    "pandas": "BSD-3-Clause",
    "pytest": "MIT",
    # JavaScript packages
    "react": "MIT",
    "next": "MIT",
    "express": "MIT",
    "lodash": "MIT",
    "axios": "MIT",
    "typescript": "Apache-2.0",
    "eslint": "MIT",
    "webpack": "MIT",
    # Go modules
    "github.com/gin-gonic/gin": "MIT",
    "github.com/gorilla/mux": "BSD-3-Clause",
}

# Known vulnerabilities (sample data - in production, this would query NVD/OSV)
KNOWN_VULNERABILITIES = {
    "log4j-core": [
        {
            "id": "CVE-2021-44228",
            "severity": "critical",
            "cvss": 10.0,
            "description": "Log4Shell - Remote code execution via JNDI lookup",
            "fixed_in": "2.17.0",
        },
    ],
    "lodash": [
        {
            "id": "CVE-2021-23337",
            "severity": "high",
            "cvss": 7.2,
            "description": "Command injection via template function",
            "fixed_in": "4.17.21",
        },
    ],
    "cryptography": [
        {
            "id": "CVE-2023-49083",
            "severity": "high",
            "cvss": 7.5,
            "description": "NULL pointer dereference in PKCS7 parsing",
            "fixed_in": "41.0.6",
        },
    ],
}


class SBOMGenerator:
    """Generates SBOM documents from dependency files."""

    def __init__(self):
        self._sboms: dict[UUID, SBOMDocument] = {}

    async def generate_sbom(
        self,
        organization_id: UUID | None,
        repository_id: UUID | None,
        name: str,
        version: str,
        dependency_files: dict[str, str],
        format: SBOMFormat = SBOMFormat.CYCLONEDX_JSON,
        include_vulnerabilities: bool = True,
        include_licenses: bool = True,
    ) -> SBOMDocument:
        """Generate an SBOM from dependency files.
        
        Args:
            organization_id: Organization ID
            repository_id: Repository ID
            name: Project name
            version: Project version
            dependency_files: Dict of filename -> content
            format: Output format
            include_vulnerabilities: Check for known vulnerabilities
            include_licenses: Include license information
            
        Returns:
            SBOMDocument with all components and compliance metadata
        """
        start_time = time.perf_counter()
        
        sbom = SBOMDocument(
            organization_id=organization_id,
            repository_id=repository_id,
            name=name,
            version=version,
            format=format,
            source_files=list(dependency_files.keys()),
        )
        
        # Parse all dependency files
        for filename, content in dependency_files.items():
            components = await self._parse_dependency_file(filename, content)
            
            for component in components:
                # Enrich with license info
                if include_licenses:
                    self._enrich_license(component)
                
                # Check for vulnerabilities
                if include_vulnerabilities:
                    await self._check_vulnerabilities(component)
                
                sbom.components.append(component)
        
        # Calculate summaries
        self._calculate_summaries(sbom)
        
        # Generate signature
        sbom.signature = self._generate_signature(sbom)
        
        sbom.generation_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Store
        self._sboms[sbom.id] = sbom
        
        logger.info(
            "Generated SBOM",
            sbom_id=str(sbom.id),
            components=sbom.total_components,
            vulnerabilities=sbom.total_vulnerabilities,
            generation_time_ms=sbom.generation_time_ms,
        )
        
        return sbom

    async def _parse_dependency_file(
        self,
        filename: str,
        content: str,
    ) -> list[SBOMComponent]:
        """Parse a dependency file into components."""
        components = []
        
        try:
            if filename.endswith("package.json"):
                components = self._parse_npm(content)
            elif filename.endswith("package-lock.json"):
                components = self._parse_npm_lock(content)
            elif filename.endswith("requirements.txt"):
                components = self._parse_requirements(content)
            elif filename.endswith("Pipfile.lock"):
                components = self._parse_pipfile_lock(content)
            elif filename.endswith("pyproject.toml"):
                components = self._parse_pyproject(content)
            elif filename.endswith("go.mod"):
                components = self._parse_gomod(content)
            elif filename.endswith("go.sum"):
                components = self._parse_gosum(content)
            elif filename.endswith("Cargo.lock"):
                components = self._parse_cargo_lock(content)
            elif filename.endswith("pom.xml"):
                components = self._parse_pom(content)
            elif filename.endswith("Gemfile.lock"):
                components = self._parse_gemfile_lock(content)
        except Exception as e:
            logger.warning(f"Failed to parse {filename}: {e}")
        
        return components

    def _parse_npm(self, content: str) -> list[SBOMComponent]:
        """Parse npm package.json."""
        components = []
        
        try:
            data = json.loads(content)
            
            for name, version in data.get("dependencies", {}).items():
                components.append(SBOMComponent(
                    name=name,
                    version=self._clean_version(version),
                    purl=f"pkg:npm/{name}@{self._clean_version(version)}",
                    type="library",
                    is_direct=True,
                ))
            
            for name, version in data.get("devDependencies", {}).items():
                comp = SBOMComponent(
                    name=name,
                    version=self._clean_version(version),
                    purl=f"pkg:npm/{name}@{self._clean_version(version)}",
                    type="library",
                    scope="optional",
                    is_direct=True,
                )
                comp.metadata["dev_dependency"] = True
                components.append(comp)
        except json.JSONDecodeError:
            pass
        
        return components

    def _parse_npm_lock(self, content: str) -> list[SBOMComponent]:
        """Parse npm package-lock.json for complete dependency tree."""
        components = []
        
        try:
            data = json.loads(content)
            packages = data.get("packages", {})
            
            for path, info in packages.items():
                if not path or path == "":
                    continue  # Skip root
                
                name = path.split("node_modules/")[-1]
                version = info.get("version", "")
                
                if name and version:
                    components.append(SBOMComponent(
                        name=name,
                        version=version,
                        purl=f"pkg:npm/{name}@{version}",
                        type="library",
                        is_direct=not info.get("dev", False) and "node_modules" not in path.rsplit("node_modules/", 1)[0],
                        hash_sha256=info.get("integrity", "").replace("sha512-", "")[:64] if info.get("integrity") else None,
                    ))
        except json.JSONDecodeError:
            pass
        
        return components

    def _parse_requirements(self, content: str) -> list[SBOMComponent]:
        """Parse Python requirements.txt."""
        components = []
        
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*([<>=!~]+)?\s*(.+)?$', line)
            if match:
                name = match.group(1).lower()
                version = match.group(3) or ""
                
                components.append(SBOMComponent(
                    name=name,
                    version=version,
                    purl=f"pkg:pypi/{name}@{version}" if version else f"pkg:pypi/{name}",
                    type="library",
                    is_direct=True,
                ))
        
        return components

    def _parse_pipfile_lock(self, content: str) -> list[SBOMComponent]:
        """Parse Pipfile.lock."""
        components = []
        
        try:
            data = json.loads(content)
            
            for section in ["default", "develop"]:
                for name, info in data.get(section, {}).items():
                    version = info.get("version", "").lstrip("=")
                    hashes = info.get("hashes", [])
                    
                    comp = SBOMComponent(
                        name=name.lower(),
                        version=version,
                        purl=f"pkg:pypi/{name.lower()}@{version}",
                        type="library",
                        is_direct=section == "default",
                    )
                    
                    if hashes:
                        for h in hashes:
                            if h.startswith("sha256:"):
                                comp.hash_sha256 = h.replace("sha256:", "")
                                break
                    
                    components.append(comp)
        except json.JSONDecodeError:
            pass
        
        return components

    def _parse_pyproject(self, content: str) -> list[SBOMComponent]:
        """Parse pyproject.toml (simplified)."""
        components = []
        
        in_deps = False
        for line in content.split("\n"):
            if "[project.dependencies]" in line or "[tool.poetry.dependencies]" in line:
                in_deps = True
                continue
            elif line.startswith("["):
                in_deps = False
                continue
            
            if in_deps:
                match = re.match(r'^"?([a-zA-Z0-9_-]+)"?\s*[=<>]', line)
                if match:
                    name = match.group(1).lower()
                    components.append(SBOMComponent(
                        name=name,
                        version="",
                        purl=f"pkg:pypi/{name}",
                        type="library",
                        is_direct=True,
                    ))
        
        return components

    def _parse_gomod(self, content: str) -> list[SBOMComponent]:
        """Parse go.mod."""
        components = []
        
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("require ") or (line and not line.startswith("//") and not line.startswith("module")):
                match = re.match(r'(?:require\s+)?([^\s]+)\s+v?([^\s]+)', line)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    
                    components.append(SBOMComponent(
                        name=name,
                        version=version,
                        purl=f"pkg:golang/{name}@{version}",
                        type="library",
                        is_direct=True,
                    ))
        
        return components

    def _parse_gosum(self, content: str) -> list[SBOMComponent]:
        """Parse go.sum for hashes."""
        components = []
        seen = set()
        
        for line in content.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 3:
                name = parts[0]
                version = parts[1].split("/")[0].lstrip("v")
                hash_val = parts[2]
                
                key = f"{name}@{version}"
                if key not in seen:
                    seen.add(key)
                    components.append(SBOMComponent(
                        name=name,
                        version=version,
                        purl=f"pkg:golang/{name}@{version}",
                        type="library",
                        hash_sha256=hash_val.replace("h1:", "")[:64] if hash_val.startswith("h1:") else None,
                    ))
        
        return components

    def _parse_cargo_lock(self, content: str) -> list[SBOMComponent]:
        """Parse Cargo.lock."""
        components = []
        current = {}
        
        for line in content.split("\n"):
            line = line.strip()
            
            if line == "[[package]]":
                if current.get("name"):
                    components.append(SBOMComponent(
                        name=current["name"],
                        version=current.get("version", ""),
                        purl=f"pkg:cargo/{current['name']}@{current.get('version', '')}",
                        type="library",
                        hash_sha256=current.get("checksum"),
                    ))
                current = {}
            elif "=" in line:
                key, value = line.split("=", 1)
                current[key.strip()] = value.strip().strip('"')
        
        if current.get("name"):
            components.append(SBOMComponent(
                name=current["name"],
                version=current.get("version", ""),
                purl=f"pkg:cargo/{current['name']}@{current.get('version', '')}",
                type="library",
            ))
        
        return components

    def _parse_pom(self, content: str) -> list[SBOMComponent]:
        """Parse Maven pom.xml."""
        components = []
        
        # Simple regex extraction
        deps = re.findall(
            r'<dependency>.*?<groupId>([^<]+)</groupId>.*?<artifactId>([^<]+)</artifactId>.*?(?:<version>([^<]*)</version>)?.*?</dependency>',
            content,
            re.DOTALL
        )
        
        for group_id, artifact_id, version in deps:
            components.append(SBOMComponent(
                name=f"{group_id}:{artifact_id}",
                version=version or "",
                purl=f"pkg:maven/{group_id}/{artifact_id}@{version}" if version else f"pkg:maven/{group_id}/{artifact_id}",
                type="library",
                supplier=group_id,
            ))
        
        return components

    def _parse_gemfile_lock(self, content: str) -> list[SBOMComponent]:
        """Parse Gemfile.lock."""
        components = []
        in_specs = False
        
        for line in content.split("\n"):
            if line.strip() == "specs:":
                in_specs = True
                continue
            elif line and not line.startswith(" "):
                in_specs = False
            
            if in_specs:
                match = re.match(r'^\s{4}([a-zA-Z0-9_-]+)\s+\(([^)]+)\)', line)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    
                    components.append(SBOMComponent(
                        name=name,
                        version=version,
                        purl=f"pkg:gem/{name}@{version}",
                        type="library",
                    ))
        
        return components

    def _clean_version(self, version: str) -> str:
        """Clean version string."""
        return version.strip("^~>=<")

    def _enrich_license(self, component: SBOMComponent) -> None:
        """Add license information to component."""
        name_lower = component.name.lower()
        
        if name_lower in KNOWN_LICENSES:
            component.license = KNOWN_LICENSES[name_lower]
        
        if component.license and component.license in LICENSE_COMPLIANCE_INFO:
            info = LICENSE_COMPLIANCE_INFO[component.license]
            component.license_risk = info["risk"]
        else:
            component.license_risk = LicenseRisk.UNKNOWN

    async def _check_vulnerabilities(self, component: SBOMComponent) -> None:
        """Check component for known vulnerabilities."""
        name_lower = component.name.lower()
        
        if name_lower in KNOWN_VULNERABILITIES:
            for vuln_data in KNOWN_VULNERABILITIES[name_lower]:
                # Check if version is affected
                if self._version_affected(component.version, vuln_data.get("fixed_in")):
                    component.vulnerabilities.append(ComponentVulnerability(
                        id=vuln_data["id"],
                        severity=VulnerabilitySeverity(vuln_data["severity"]),
                        cvss_score=vuln_data.get("cvss"),
                        description=vuln_data["description"],
                        fixed_in_version=vuln_data.get("fixed_in"),
                    ))

    def _version_affected(self, current: str, fixed_in: str | None) -> bool:
        """Check if current version is affected (before fixed_in)."""
        if not fixed_in or not current:
            return True
        
        # Simple version comparison (in production, use packaging.version)
        try:
            current_parts = [int(x) for x in current.split(".")[:3]]
            fixed_parts = [int(x) for x in fixed_in.split(".")[:3]]
            
            # Pad to same length
            while len(current_parts) < 3:
                current_parts.append(0)
            while len(fixed_parts) < 3:
                fixed_parts.append(0)
            
            return current_parts < fixed_parts
        except (ValueError, AttributeError):
            return True  # Assume affected if can't parse

    def _calculate_summaries(self, sbom: SBOMDocument) -> None:
        """Calculate summary statistics for SBOM."""
        sbom.total_components = len(sbom.components)
        sbom.direct_dependencies = sum(1 for c in sbom.components if c.is_direct)
        sbom.transitive_dependencies = sbom.total_components - sbom.direct_dependencies
        
        # Vulnerabilities
        for component in sbom.components:
            for vuln in component.vulnerabilities:
                sbom.total_vulnerabilities += 1
                if vuln.severity == VulnerabilitySeverity.CRITICAL:
                    sbom.critical_vulnerabilities += 1
                elif vuln.severity == VulnerabilitySeverity.HIGH:
                    sbom.high_vulnerabilities += 1
                elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                    sbom.medium_vulnerabilities += 1
                elif vuln.severity == VulnerabilitySeverity.LOW:
                    sbom.low_vulnerabilities += 1
        
        # Licenses
        for component in sbom.components:
            license_name = component.license or "UNKNOWN"
            sbom.license_types[license_name] = sbom.license_types.get(license_name, 0) + 1
            
            if component.license_risk == LicenseRisk.HIGH:
                sbom.high_risk_licenses += 1
            elif component.license_risk == LicenseRisk.UNKNOWN:
                sbom.unknown_licenses += 1
        
        # Compliance score
        penalty = 0
        penalty += sbom.critical_vulnerabilities * 20
        penalty += sbom.high_vulnerabilities * 10
        penalty += sbom.medium_vulnerabilities * 5
        penalty += sbom.high_risk_licenses * 5
        penalty += sbom.unknown_licenses * 2
        
        sbom.compliance_score = max(0, 100 - penalty)

    def _generate_signature(self, sbom: SBOMDocument) -> str:
        """Generate digital signature for SBOM."""
        data = f"{sbom.id}:{sbom.name}:{sbom.version}:{sbom.total_components}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def get_sbom(self, sbom_id: UUID) -> SBOMDocument | None:
        """Retrieve an SBOM by ID."""
        return self._sboms.get(sbom_id)

    async def export_sbom(
        self,
        sbom_id: UUID,
        format: SBOMFormat,
    ) -> dict[str, Any]:
        """Export SBOM in specified format."""
        sbom = self._sboms.get(sbom_id)
        if not sbom:
            raise ValueError(f"SBOM {sbom_id} not found")
        
        if format in (SBOMFormat.SPDX_JSON, SBOMFormat.SPDX_XML):
            return sbom.to_spdx()
        else:
            return sbom.to_cyclonedx()


# Global instance
_generator: SBOMGenerator | None = None


def get_sbom_generator() -> SBOMGenerator:
    """Get or create SBOM generator."""
    global _generator
    if _generator is None:
        _generator = SBOMGenerator()
    return _generator
