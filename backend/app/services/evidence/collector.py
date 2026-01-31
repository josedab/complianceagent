"""Evidence Collector - Automated evidence collection from various sources."""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from app.services.evidence.models import (
    CollectionConfig,
    Control,
    EvidenceCollection,
    EvidenceItem,
    EvidenceStatus,
    EvidenceType,
    Framework,
)


logger = structlog.get_logger()


# Common controls by framework (subset for demonstration)
FRAMEWORK_CONTROLS: dict[Framework, list[Control]] = {
    Framework.SOC2: [
        Control(
            control_id="CC1.1",
            framework=Framework.SOC2,
            title="COSO Principle 1",
            description="The entity demonstrates a commitment to integrity and ethical values",
            category="Control Environment",
            evidence_requirements=["code_of_conduct", "ethics_policy", "training_records"],
        ),
        Control(
            control_id="CC6.1",
            framework=Framework.SOC2,
            title="Logical Access Security",
            description="The entity implements logical access security measures",
            category="Logical and Physical Access Controls",
            evidence_requirements=["access_policy", "mfa_config", "access_logs"],
        ),
        Control(
            control_id="CC7.1",
            framework=Framework.SOC2,
            title="System Operations",
            description="The entity detects and monitors security events",
            category="System Operations",
            evidence_requirements=["monitoring_config", "alert_rules", "incident_logs"],
        ),
        Control(
            control_id="CC8.1",
            framework=Framework.SOC2,
            title="Change Management",
            description="The entity authorizes, designs, and implements changes",
            category="Change Management",
            evidence_requirements=["change_policy", "pr_reviews", "deployment_logs"],
        ),
    ],
    Framework.ISO27001: [
        Control(
            control_id="A.5.1",
            framework=Framework.ISO27001,
            title="Information Security Policies",
            description="Management direction for information security",
            category="Security Policies",
            evidence_requirements=["security_policy", "policy_review_records"],
        ),
        Control(
            control_id="A.8.1",
            framework=Framework.ISO27001,
            title="Asset Management",
            description="Inventory and ownership of assets",
            category="Asset Management",
            evidence_requirements=["asset_inventory", "classification_schema"],
        ),
        Control(
            control_id="A.9.1",
            framework=Framework.ISO27001,
            title="Access Control",
            description="Business requirements of access control",
            category="Access Control",
            evidence_requirements=["access_policy", "access_reviews", "user_list"],
        ),
    ],
    Framework.HIPAA: [
        Control(
            control_id="164.308(a)(1)",
            framework=Framework.HIPAA,
            title="Security Management Process",
            description="Implement policies and procedures to prevent security violations",
            category="Administrative Safeguards",
            evidence_requirements=["risk_analysis", "risk_management_plan", "sanctions_policy"],
        ),
        Control(
            control_id="164.312(a)(1)",
            framework=Framework.HIPAA,
            title="Access Control",
            description="Implement technical policies for electronic systems",
            category="Technical Safeguards",
            evidence_requirements=["access_controls", "encryption_config", "audit_logs"],
        ),
        Control(
            control_id="164.312(e)(1)",
            framework=Framework.HIPAA,
            title="Transmission Security",
            description="Implement measures to guard against unauthorized access during transmission",
            category="Technical Safeguards",
            evidence_requirements=["tls_config", "encryption_standards", "network_diagram"],
        ),
    ],
    Framework.GDPR: [
        Control(
            control_id="Art.5",
            framework=Framework.GDPR,
            title="Principles of Processing",
            description="Lawfulness, fairness, transparency, purpose limitation",
            category="Data Processing Principles",
            evidence_requirements=["privacy_policy", "consent_records", "processing_records"],
        ),
        Control(
            control_id="Art.32",
            framework=Framework.GDPR,
            title="Security of Processing",
            description="Appropriate technical and organizational measures",
            category="Security",
            evidence_requirements=["security_measures", "encryption_config", "access_controls"],
        ),
        Control(
            control_id="Art.33",
            framework=Framework.GDPR,
            title="Breach Notification",
            description="Notification of personal data breach to supervisory authority",
            category="Breach Management",
            evidence_requirements=["breach_procedure", "breach_log", "notification_templates"],
        ),
    ],
    Framework.PCI_DSS: [
        Control(
            control_id="1.1",
            framework=Framework.PCI_DSS,
            title="Firewall Configuration",
            description="Install and maintain a firewall configuration",
            category="Network Security",
            evidence_requirements=["firewall_rules", "network_diagram", "change_records"],
        ),
        Control(
            control_id="3.4",
            framework=Framework.PCI_DSS,
            title="PAN Encryption",
            description="Render PAN unreadable anywhere it is stored",
            category="Data Protection",
            evidence_requirements=["encryption_config", "key_management", "storage_scan"],
        ),
        Control(
            control_id="8.1",
            framework=Framework.PCI_DSS,
            title="User Identification",
            description="Define and implement policies for user identification",
            category="Access Control",
            evidence_requirements=["user_policy", "unique_ids", "access_logs"],
        ),
    ],
}


class EvidenceCollector:
    """Collects compliance evidence from various sources."""

    def __init__(self):
        self._collections: dict[UUID, EvidenceCollection] = {}
        self._configs: dict[UUID, CollectionConfig] = {}

    async def collect_evidence(
        self,
        organization_id: UUID,
        frameworks: list[Framework],
        sources: dict[str, Any] | None = None,
    ) -> list[EvidenceCollection]:
        """Collect evidence for specified frameworks.
        
        Args:
            organization_id: Organization ID
            frameworks: List of frameworks to collect evidence for
            sources: Optional source configuration
            
        Returns:
            List of evidence collections
        """
        start_time = time.perf_counter()
        collections = []
        
        for framework in frameworks:
            controls = FRAMEWORK_CONTROLS.get(framework, [])
            
            for control in controls:
                collection = await self._collect_for_control(
                    organization_id=organization_id,
                    control=control,
                    sources=sources,
                )
                collections.append(collection)
                self._collections[collection.id] = collection
        
        logger.info(
            "Evidence collection completed",
            organization_id=str(organization_id),
            frameworks=[f.value for f in frameworks],
            collections=len(collections),
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )
        
        return collections

    async def _collect_for_control(
        self,
        organization_id: UUID,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceCollection:
        """Collect evidence for a specific control."""
        collection = EvidenceCollection(
            organization_id=organization_id,
            framework=control.framework,
            control_id=control.control_id,
            control_title=control.title,
            status=EvidenceStatus.COLLECTING,
        )
        
        # Collect evidence based on requirements
        for requirement in control.evidence_requirements:
            evidence = await self._collect_evidence_item(
                requirement=requirement,
                control=control,
                sources=sources,
            )
            if evidence:
                collection.evidence.append(evidence)
            else:
                collection.missing_evidence.append(requirement)
        
        # Update status
        if not collection.missing_evidence:
            collection.status = EvidenceStatus.COLLECTED
        elif collection.evidence:
            collection.status = EvidenceStatus.COLLECTED  # Partial
        else:
            collection.status = EvidenceStatus.PENDING
        
        return collection

    async def _collect_evidence_item(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Collect a specific evidence item."""
        # Map requirements to collection methods
        collectors = {
            # Policy documents
            "code_of_conduct": self._collect_policy_document,
            "ethics_policy": self._collect_policy_document,
            "security_policy": self._collect_policy_document,
            "access_policy": self._collect_policy_document,
            "privacy_policy": self._collect_policy_document,
            "change_policy": self._collect_policy_document,
            "user_policy": self._collect_policy_document,
            "sanctions_policy": self._collect_policy_document,
            "breach_procedure": self._collect_policy_document,
            
            # Configuration evidence
            "mfa_config": self._collect_config_evidence,
            "monitoring_config": self._collect_config_evidence,
            "encryption_config": self._collect_config_evidence,
            "tls_config": self._collect_config_evidence,
            "firewall_rules": self._collect_config_evidence,
            
            # Code artifacts
            "pr_reviews": self._collect_code_artifact,
            "deployment_logs": self._collect_code_artifact,
            "access_logs": self._collect_code_artifact,
            "incident_logs": self._collect_code_artifact,
            "audit_logs": self._collect_code_artifact,
            "breach_log": self._collect_code_artifact,
            
            # Records
            "training_records": self._collect_records,
            "access_reviews": self._collect_records,
            "consent_records": self._collect_records,
            "processing_records": self._collect_records,
            "policy_review_records": self._collect_records,
            "change_records": self._collect_records,
            
            # Technical documentation
            "network_diagram": self._collect_documentation,
            "asset_inventory": self._collect_documentation,
            "classification_schema": self._collect_documentation,
            "risk_analysis": self._collect_documentation,
            "risk_management_plan": self._collect_documentation,
        }
        
        collector = collectors.get(requirement, self._collect_generic)
        return await collector(requirement, control, sources)

    async def _collect_policy_document(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Collect policy document evidence."""
        # In production, would fetch from document management system
        return EvidenceItem(
            evidence_type=EvidenceType.POLICY,
            title=f"{requirement.replace('_', ' ').title()}",
            description=f"Policy document for {control.control_id}",
            source="document_management_system",
            content=f"[Reference to {requirement} document]",
            content_hash=hashlib.sha256(requirement.encode()).hexdigest()[:16],
            controls=[control.control_id],
            frameworks=[control.framework],
            metadata={"requirement": requirement, "auto_collected": True},
        )

    async def _collect_config_evidence(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Collect configuration evidence."""
        return EvidenceItem(
            evidence_type=EvidenceType.CONFIGURATION,
            title=f"{requirement.replace('_', ' ').title()} Configuration",
            description=f"Configuration evidence for {control.control_id}",
            source="infrastructure_scanner",
            content=f"[Configuration snapshot for {requirement}]",
            content_hash=hashlib.sha256(requirement.encode()).hexdigest()[:16],
            controls=[control.control_id],
            frameworks=[control.framework],
            metadata={"requirement": requirement, "auto_collected": True},
        )

    async def _collect_code_artifact(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Collect code artifact evidence."""
        return EvidenceItem(
            evidence_type=EvidenceType.CODE_ARTIFACT,
            title=f"{requirement.replace('_', ' ').title()}",
            description=f"Code artifact for {control.control_id}",
            source="github",
            content=f"[Reference to {requirement} from repository]",
            content_hash=hashlib.sha256(requirement.encode()).hexdigest()[:16],
            controls=[control.control_id],
            frameworks=[control.framework],
            metadata={"requirement": requirement, "auto_collected": True},
        )

    async def _collect_records(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Collect record evidence."""
        return EvidenceItem(
            evidence_type=EvidenceType.AUDIT_TRAIL,
            title=f"{requirement.replace('_', ' ').title()}",
            description=f"Records for {control.control_id}",
            source="compliance_system",
            content=f"[Reference to {requirement} records]",
            content_hash=hashlib.sha256(requirement.encode()).hexdigest()[:16],
            controls=[control.control_id],
            frameworks=[control.framework],
            metadata={"requirement": requirement, "auto_collected": True},
        )

    async def _collect_documentation(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Collect documentation evidence."""
        return EvidenceItem(
            evidence_type=EvidenceType.DOCUMENT,
            title=f"{requirement.replace('_', ' ').title()}",
            description=f"Documentation for {control.control_id}",
            source="documentation_system",
            content=f"[Reference to {requirement} documentation]",
            content_hash=hashlib.sha256(requirement.encode()).hexdigest()[:16],
            controls=[control.control_id],
            frameworks=[control.framework],
            metadata={"requirement": requirement, "auto_collected": True},
        )

    async def _collect_generic(
        self,
        requirement: str,
        control: Control,
        sources: dict[str, Any] | None,
    ) -> EvidenceItem | None:
        """Generic evidence collection."""
        return EvidenceItem(
            evidence_type=EvidenceType.DOCUMENT,
            title=f"{requirement.replace('_', ' ').title()}",
            description=f"Evidence for {control.control_id}",
            source="manual_collection",
            content=f"[Placeholder for {requirement}]",
            content_hash=hashlib.sha256(requirement.encode()).hexdigest()[:16],
            controls=[control.control_id],
            frameworks=[control.framework],
            metadata={"requirement": requirement, "auto_collected": False, "needs_manual_review": True},
        )

    async def get_collection(self, collection_id: UUID) -> EvidenceCollection | None:
        """Get an evidence collection by ID."""
        return self._collections.get(collection_id)

    async def validate_collection(
        self,
        collection_id: UUID,
        validator: str,
    ) -> EvidenceCollection | None:
        """Validate an evidence collection."""
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        
        collection.status = EvidenceStatus.VALIDATED
        collection.validated_at = datetime.utcnow()
        collection.validated_by = validator
        collection.updated_at = datetime.utcnow()
        
        return collection


# Global instance
_collector: EvidenceCollector | None = None


def get_evidence_collector() -> EvidenceCollector:
    """Get or create evidence collector."""
    global _collector
    if _collector is None:
        _collector = EvidenceCollector()
    return _collector
