"""Regulation-to-Architecture Advisor Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.arch_advisor.models import (
    ArchAdvisorStats,
    ArchComponent,
    ArchConnection,
    ArchitectureDiagram,
    ComponentType,
    DiagramFormat,
)


logger = structlog.get_logger()

_FRAMEWORK_COMPONENTS: dict[str, list[dict]] = {
    "GDPR": [
        {"id": "consent-gate", "name": "Consent Manager", "type": "consent", "desc": "Manages user consent for data processing", "reqs": ["Art. 6 — Lawful basis", "Art. 7 — Consent conditions"]},
        {"id": "data-subject-api", "name": "Data Subject Rights API", "type": "service", "desc": "Handles DSAR (erasure, portability, access)", "reqs": ["Art. 15-22 — Data subject rights"]},
        {"id": "encryption-layer", "name": "Data Encryption Layer", "type": "encryption", "desc": "AES-256 encryption at rest and TLS in transit", "reqs": ["Art. 32 — Security of processing"]},
        {"id": "audit-trail", "name": "Processing Audit Log", "type": "audit", "desc": "Immutable record of all data processing activities", "reqs": ["Art. 30 — Records of processing"]},
    ],
    "HIPAA": [
        {"id": "phi-vault", "name": "PHI Vault", "type": "encryption", "desc": "Encrypted storage for Protected Health Information", "reqs": ["§164.312 — Technical safeguards"]},
        {"id": "access-control", "name": "RBAC Access Control", "type": "gateway", "desc": "Role-based access with MFA for PHI", "reqs": ["§164.312(a) — Access control"]},
        {"id": "audit-log", "name": "HIPAA Audit Trail", "type": "audit", "desc": "Logs all PHI access and modifications", "reqs": ["§164.312(b) — Audit controls"]},
    ],
    "PCI-DSS": [
        {"id": "tokenization", "name": "Card Tokenization Service", "type": "service", "desc": "Tokenizes card data before storage", "reqs": ["Req 3 — Protect stored account data"]},
        {"id": "network-seg", "name": "Network Segmentation", "type": "gateway", "desc": "Isolates cardholder data environment", "reqs": ["Req 1 — Network security controls"]},
        {"id": "key-mgmt", "name": "Key Management System", "type": "encryption", "desc": "Manages encryption keys with rotation", "reqs": ["Req 3.6 — Key management"]},
    ],
    "SOC2": [
        {"id": "monitoring", "name": "System Monitoring", "type": "service", "desc": "Continuous monitoring of system availability and security", "reqs": ["CC7.1 — System monitoring"]},
        {"id": "change-mgmt", "name": "Change Management", "type": "service", "desc": "Controlled change approval and deployment process", "reqs": ["CC8.1 — Change management"]},
        {"id": "incident-resp", "name": "Incident Response", "type": "service", "desc": "Automated incident detection and response", "reqs": ["CC7.3 — Incident response"]},
    ],
}


class ArchAdvisorService:
    """Generate compliance-aware architecture from regulatory requirements."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._diagrams: list[ArchitectureDiagram] = []

    async def generate_architecture(
        self,
        frameworks: list[str],
        diagram_format: str = "mermaid",
        app_name: str = "Application",
    ) -> ArchitectureDiagram:
        fmt = DiagramFormat(diagram_format)
        components: list[ArchComponent] = []
        connections: list[ArchConnection] = []
        recommendations: list[str] = []

        # Always add core components
        components.append(ArchComponent(id="api-gateway", name="API Gateway", component_type=ComponentType.GATEWAY, description="Entry point with rate limiting and auth"))
        components.append(ArchComponent(id="app-service", name=app_name, component_type=ComponentType.SERVICE, description="Main application service"))
        components.append(ArchComponent(id="database", name="Primary Database", component_type=ComponentType.DATABASE, description="Encrypted persistent storage"))

        connections.append(ArchConnection(source="api-gateway", target="app-service", label="HTTPS", encrypted=True))
        connections.append(ArchConnection(source="app-service", target="database", label="TLS", encrypted=True, audit_logged=True))

        # Add framework-specific components
        for fw in frameworks:
            fw_components = _FRAMEWORK_COMPONENTS.get(fw, [])
            for comp_def in fw_components:
                comp = ArchComponent(
                    id=comp_def["id"],
                    name=comp_def["name"],
                    component_type=ComponentType(comp_def["type"]),
                    frameworks=[fw],
                    description=comp_def["desc"],
                    requirements=comp_def["reqs"],
                )
                if not any(c.id == comp.id for c in components):
                    components.append(comp)
                    connections.append(ArchConnection(source="app-service", target=comp.id, label="internal", encrypted=True, audit_logged=True))

            recommendations.append(f"Ensure all {fw} requirements are addressed in deployment configuration")

        diagram_code = self._render_diagram(components, connections, fmt, app_name)

        diagram = ArchitectureDiagram(
            title=f"Compliance Architecture for {', '.join(frameworks)}",
            frameworks=frameworks,
            components=components,
            connections=connections,
            diagram_format=fmt,
            diagram_code=diagram_code,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )
        self._diagrams.append(diagram)
        logger.info("Architecture generated", frameworks=frameworks, components=len(components))
        return diagram

    def _render_diagram(self, components: list[ArchComponent], connections: list[ArchConnection], fmt: DiagramFormat, title: str) -> str:
        if fmt == DiagramFormat.MERMAID:
            lines = ["graph TD"]
            for c in components:
                shape = {"service": f"[{c.name}]", "database": f"[({c.name})]", "gateway": f"{{{c.name}}}", "encryption": f"[/{c.name}/]", "consent": f"({c.name})", "audit": f"[{c.name}]", "queue": f">{c.name}]", "cache": f"[{c.name}]"}
                lines.append(f"    {c.id}{shape.get(c.component_type.value, f'[{c.name}]')}")
            for conn in connections:
                label = f"|{conn.label}|" if conn.label else ""
                arrow = "-->" if conn.encrypted else "-..->"
                lines.append(f"    {conn.source} {arrow}{label} {conn.target}")
            return "\n".join(lines)
        if fmt == DiagramFormat.ASCII:
            lines = [f"=== {title} ===", ""]
            for c in components:
                lines.append(f"  [{c.component_type.value.upper()}] {c.name} ({c.id})")
            lines.append("")
            for conn in connections:
                enc = " [encrypted]" if conn.encrypted else ""
                lines.append(f"  {conn.source} --> {conn.target} ({conn.label}{enc})")
            return "\n".join(lines)
        return f"# {title}\n# Components: {len(components)}\n# Connections: {len(connections)}"

    def list_available_frameworks(self) -> list[str]:
        return list(_FRAMEWORK_COMPONENTS.keys())

    def get_stats(self) -> ArchAdvisorStats:
        by_fw: dict[str, int] = {}
        by_fmt: dict[str, int] = {}
        comp_counts: list[int] = []
        for d in self._diagrams:
            for fw in d.frameworks:
                by_fw[fw] = by_fw.get(fw, 0) + 1
            by_fmt[d.diagram_format.value] = by_fmt.get(d.diagram_format.value, 0) + 1
            comp_counts.append(len(d.components))
        return ArchAdvisorStats(
            total_diagrams=len(self._diagrams),
            by_framework=by_fw,
            by_format=by_fmt,
            avg_components=round(sum(comp_counts) / len(comp_counts), 1) if comp_counts else 0.0,
        )
