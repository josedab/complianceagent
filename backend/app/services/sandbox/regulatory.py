"""Regulatory Sandbox Integration - Connect to official regulatory sandboxes."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

import structlog


logger = structlog.get_logger()


class SandboxProvider(str, Enum):
    """Official regulatory sandbox providers."""
    EU_AI_ACT = "eu_ai_act"
    UK_FCA = "uk_fca"
    SINGAPORE_MAS = "singapore_mas"
    AUSTRALIA_ASIC = "australia_asic"
    HONG_KONG_HKMA = "hong_kong_hkma"
    JAPAN_FSA = "japan_fsa"
    DUTCH_AFM = "dutch_afm"
    INTERNAL = "internal"  # Organization's own sandbox


class ApplicationStatus(str, Enum):
    """Sandbox application status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class TestPhase(str, Enum):
    """Sandbox testing phases."""
    PREPARATION = "preparation"
    INITIAL_TESTING = "initial_testing"
    SCALED_TESTING = "scaled_testing"
    EVALUATION = "evaluation"
    EXIT = "exit"


@dataclass
class SandboxRequirement:
    """A requirement for sandbox participation."""
    id: str
    category: str
    description: str
    mandatory: bool = True
    evidence_required: list[str] = field(default_factory=list)
    status: str = "pending"  # pending, met, not_met, in_progress
    notes: str = ""


@dataclass
class SandboxApplication:
    """A sandbox application."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    provider: SandboxProvider = SandboxProvider.EU_AI_ACT
    status: ApplicationStatus = ApplicationStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: datetime | None = None
    
    # Application details
    project_name: str = ""
    project_description: str = ""
    innovation_description: str = ""
    target_market: list[str] = field(default_factory=list)
    ai_system_type: str = ""
    risk_classification: str = ""
    
    # Requirements
    requirements: list[SandboxRequirement] = field(default_factory=list)
    requirements_met_count: int = 0
    requirements_total_count: int = 0
    
    # Testing scope
    testing_scope: dict[str, Any] = field(default_factory=dict)
    testing_duration_months: int = 12
    testing_start_date: datetime | None = None
    testing_end_date: datetime | None = None
    
    # Contacts
    primary_contact: str = ""
    regulatory_liaison: str = ""
    
    # Status tracking
    status_history: list[dict[str, Any]] = field(default_factory=list)
    feedback: list[str] = field(default_factory=list)


@dataclass
class SandboxTest:
    """A test conducted in the sandbox."""
    id: UUID = field(default_factory=uuid4)
    application_id: UUID | None = None
    name: str = ""
    description: str = ""
    phase: TestPhase = TestPhase.INITIAL_TESTING
    
    # Test configuration
    test_type: str = ""  # "functional", "compliance", "performance", "user"
    test_parameters: dict[str, Any] = field(default_factory=dict)
    safeguards: list[str] = field(default_factory=list)
    
    # Execution
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"  # pending, running, completed, failed
    
    # Results
    results: dict[str, Any] = field(default_factory=dict)
    compliance_findings: list[dict[str, Any]] = field(default_factory=list)
    issues_found: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass 
class SandboxEvidence:
    """Evidence collected for sandbox requirements."""
    id: UUID = field(default_factory=uuid4)
    application_id: UUID | None = None
    requirement_id: str = ""
    evidence_type: str = ""  # document, test_result, certification, attestation
    title: str = ""
    description: str = ""
    file_reference: str | None = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    verified: bool = False
    verified_by: str | None = None


# Sandbox provider configurations
SANDBOX_PROVIDERS = {
    SandboxProvider.EU_AI_ACT: {
        "name": "EU AI Act Regulatory Sandbox",
        "authority": "European Commission / National Authorities",
        "region": "EU",
        "website": "https://digital-strategy.ec.europa.eu/en/policies/regulatory-sandboxes",
        "eligibility": [
            "AI system provider operating in the EU",
            "Developing high-risk AI system under EU AI Act",
            "Commitment to consumer protection",
        ],
        "duration_months": 24,
        "requirements": [
            SandboxRequirement(
                id="EUAI-REQ-001",
                category="AI System Documentation",
                description="Technical documentation of AI system",
                mandatory=True,
                evidence_required=["System architecture", "Algorithm description", "Training data documentation"],
            ),
            SandboxRequirement(
                id="EUAI-REQ-002",
                category="Risk Assessment",
                description="Conformity assessment for high-risk AI",
                mandatory=True,
                evidence_required=["Risk classification", "Impact assessment", "Mitigation measures"],
            ),
            SandboxRequirement(
                id="EUAI-REQ-003",
                category="Human Oversight",
                description="Human oversight measures documentation",
                mandatory=True,
                evidence_required=["Oversight procedures", "Human intervention capabilities"],
            ),
            SandboxRequirement(
                id="EUAI-REQ-004",
                category="Transparency",
                description="User information and transparency measures",
                mandatory=True,
                evidence_required=["User disclosure mechanisms", "Explainability documentation"],
            ),
            SandboxRequirement(
                id="EUAI-REQ-005",
                category="Data Governance",
                description="Training data governance practices",
                mandatory=True,
                evidence_required=["Data quality processes", "Bias assessment", "Data provenance"],
            ),
        ],
    },
    SandboxProvider.UK_FCA: {
        "name": "FCA Regulatory Sandbox",
        "authority": "Financial Conduct Authority",
        "region": "UK",
        "website": "https://www.fca.org.uk/firms/innovation/regulatory-sandbox",
        "eligibility": [
            "Innovation in financial services",
            "Consumer benefit demonstration",
            "Need for sandbox testing",
        ],
        "duration_months": 6,
        "requirements": [
            SandboxRequirement(
                id="FCA-REQ-001",
                category="Innovation",
                description="Demonstrate genuine innovation",
                mandatory=True,
                evidence_required=["Innovation description", "Market gap analysis"],
            ),
            SandboxRequirement(
                id="FCA-REQ-002",
                category="Consumer Benefit",
                description="Clear consumer benefit",
                mandatory=True,
                evidence_required=["Consumer benefit analysis", "User research"],
            ),
            SandboxRequirement(
                id="FCA-REQ-003",
                category="Testing Need",
                description="Demonstrate need for sandbox testing",
                mandatory=True,
                evidence_required=["Regulatory uncertainty explanation", "Testing plan"],
            ),
        ],
    },
    SandboxProvider.SINGAPORE_MAS: {
        "name": "MAS FinTech Regulatory Sandbox",
        "authority": "Monetary Authority of Singapore",
        "region": "Singapore",
        "website": "https://www.mas.gov.sg/development/fintech/sandbox",
        "eligibility": [
            "Financial technology innovation",
            "Singapore market focus",
            "Risk management capability",
        ],
        "duration_months": 9,
        "requirements": [
            SandboxRequirement(
                id="MAS-REQ-001",
                category="Technology",
                description="Novel technology or application",
                mandatory=True,
                evidence_required=["Technology description", "Patent/IP status"],
            ),
            SandboxRequirement(
                id="MAS-REQ-002",
                category="Risk Management",
                description="Adequate risk management",
                mandatory=True,
                evidence_required=["Risk assessment", "Control framework"],
            ),
        ],
    },
}


class RegulatorySandboxIntegration:
    """Manages regulatory sandbox applications and testing."""
    
    def __init__(self):
        self._applications: dict[UUID, SandboxApplication] = {}
        self._tests: dict[UUID, SandboxTest] = {}
        self._evidence: dict[UUID, SandboxEvidence] = {}
        self._by_org: dict[UUID, list[UUID]] = {}
    
    # =========================
    # APPLICATION MANAGEMENT
    # =========================
    
    async def get_available_sandboxes(
        self,
        region: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get list of available regulatory sandboxes."""
        sandboxes = []
        for provider, config in SANDBOX_PROVIDERS.items():
            if region and config["region"] != region:
                continue
            sandboxes.append({
                "provider": provider.value,
                "name": config["name"],
                "authority": config["authority"],
                "region": config["region"],
                "website": config["website"],
                "eligibility": config["eligibility"],
                "duration_months": config["duration_months"],
                "requirements_count": len(config.get("requirements", [])),
            })
        return sandboxes
    
    async def create_application(
        self,
        organization_id: UUID,
        provider: SandboxProvider,
        project_name: str,
        project_description: str,
        ai_system_type: str = "",
    ) -> SandboxApplication:
        """Create a new sandbox application."""
        config = SANDBOX_PROVIDERS.get(provider, {})
        requirements = [
            SandboxRequirement(
                id=req.id,
                category=req.category,
                description=req.description,
                mandatory=req.mandatory,
                evidence_required=req.evidence_required,
            )
            for req in config.get("requirements", [])
        ]
        
        application = SandboxApplication(
            organization_id=organization_id,
            provider=provider,
            project_name=project_name,
            project_description=project_description,
            ai_system_type=ai_system_type,
            requirements=requirements,
            requirements_total_count=len(requirements),
            testing_duration_months=config.get("duration_months", 12),
        )
        
        application.status_history.append({
            "status": ApplicationStatus.DRAFT.value,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Application created",
        })
        
        self._applications[application.id] = application
        if organization_id not in self._by_org:
            self._by_org[organization_id] = []
        self._by_org[organization_id].append(application.id)
        
        logger.info(
            "Created sandbox application",
            application_id=str(application.id),
            provider=provider.value,
        )
        
        return application
    
    async def get_application(self, application_id: UUID) -> SandboxApplication | None:
        """Get an application by ID."""
        return self._applications.get(application_id)
    
    async def list_applications(
        self,
        organization_id: UUID,
    ) -> list[SandboxApplication]:
        """List applications for an organization."""
        app_ids = self._by_org.get(organization_id, [])
        return [self._applications[aid] for aid in app_ids if aid in self._applications]
    
    async def update_application(
        self,
        application_id: UUID,
        updates: dict[str, Any],
    ) -> SandboxApplication | None:
        """Update an application."""
        app = self._applications.get(application_id)
        if not app:
            return None
        
        for key, value in updates.items():
            if hasattr(app, key):
                setattr(app, key, value)
        
        return app
    
    async def submit_application(
        self,
        application_id: UUID,
    ) -> SandboxApplication | None:
        """Submit an application for review."""
        app = self._applications.get(application_id)
        if not app:
            return None
        
        # Check requirements
        met_count = sum(1 for r in app.requirements if r.status == "met")
        mandatory_met = all(
            r.status == "met" for r in app.requirements if r.mandatory
        )
        
        if not mandatory_met:
            raise ValueError("All mandatory requirements must be met before submission")
        
        app.status = ApplicationStatus.SUBMITTED
        app.submitted_at = datetime.utcnow()
        app.requirements_met_count = met_count
        app.status_history.append({
            "status": ApplicationStatus.SUBMITTED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Application submitted for review",
        })
        
        logger.info("Submitted sandbox application", application_id=str(application_id))
        
        return app
    
    # =========================
    # REQUIREMENTS & EVIDENCE
    # =========================
    
    async def check_pre_submission(
        self,
        application_id: UUID,
    ) -> dict[str, Any]:
        """Check if application is ready for submission."""
        app = self._applications.get(application_id)
        if not app:
            raise ValueError("Application not found")
        
        results = {
            "ready": True,
            "requirements_status": [],
            "missing_mandatory": [],
            "missing_optional": [],
        }
        
        for req in app.requirements:
            req_status = {
                "id": req.id,
                "category": req.category,
                "description": req.description,
                "mandatory": req.mandatory,
                "status": req.status,
                "evidence_required": req.evidence_required,
            }
            results["requirements_status"].append(req_status)
            
            if req.status != "met":
                if req.mandatory:
                    results["missing_mandatory"].append(req.id)
                    results["ready"] = False
                else:
                    results["missing_optional"].append(req.id)
        
        results["total_requirements"] = len(app.requirements)
        results["met_requirements"] = len(app.requirements) - len(results["missing_mandatory"]) - len(results["missing_optional"])
        
        return results
    
    async def update_requirement_status(
        self,
        application_id: UUID,
        requirement_id: str,
        status: str,
        notes: str = "",
    ) -> SandboxRequirement | None:
        """Update requirement status."""
        app = self._applications.get(application_id)
        if not app:
            return None
        
        for req in app.requirements:
            if req.id == requirement_id:
                req.status = status
                req.notes = notes
                app.requirements_met_count = sum(1 for r in app.requirements if r.status == "met")
                return req
        
        return None
    
    async def add_evidence(
        self,
        application_id: UUID,
        requirement_id: str,
        evidence_type: str,
        title: str,
        description: str = "",
        file_reference: str | None = None,
    ) -> SandboxEvidence:
        """Add evidence for a requirement."""
        evidence = SandboxEvidence(
            application_id=application_id,
            requirement_id=requirement_id,
            evidence_type=evidence_type,
            title=title,
            description=description,
            file_reference=file_reference,
        )
        
        self._evidence[evidence.id] = evidence
        
        # Auto-update requirement to in_progress
        await self.update_requirement_status(application_id, requirement_id, "in_progress")
        
        return evidence
    
    async def get_evidence_for_requirement(
        self,
        application_id: UUID,
        requirement_id: str,
    ) -> list[SandboxEvidence]:
        """Get all evidence for a requirement."""
        return [
            e for e in self._evidence.values()
            if e.application_id == application_id and e.requirement_id == requirement_id
        ]
    
    # =========================
    # SANDBOX TESTING
    # =========================
    
    async def create_test(
        self,
        application_id: UUID,
        name: str,
        test_type: str,
        description: str = "",
        parameters: dict[str, Any] | None = None,
        safeguards: list[str] | None = None,
    ) -> SandboxTest:
        """Create a sandbox test."""
        app = self._applications.get(application_id)
        if not app or app.status not in [ApplicationStatus.ACTIVE, ApplicationStatus.APPROVED]:
            raise ValueError("Application must be approved/active to create tests")
        
        test = SandboxTest(
            application_id=application_id,
            name=name,
            description=description,
            test_type=test_type,
            test_parameters=parameters or {},
            safeguards=safeguards or [],
        )
        
        self._tests[test.id] = test
        
        logger.info("Created sandbox test", test_id=str(test.id), application_id=str(application_id))
        
        return test
    
    async def run_test(
        self,
        test_id: UUID,
    ) -> SandboxTest:
        """Run a sandbox test."""
        test = self._tests.get(test_id)
        if not test:
            raise ValueError("Test not found")
        
        test.started_at = datetime.utcnow()
        test.status = "running"
        
        # Simulate test execution
        # In production, this would integrate with actual testing systems
        test.results = {
            "execution_time_ms": 1500,
            "scenarios_tested": 10,
            "scenarios_passed": 9,
            "scenarios_failed": 1,
        }
        
        test.compliance_findings = [
            {
                "finding": "AI transparency requirement partially met",
                "severity": "medium",
                "recommendation": "Enhance user notification mechanism",
            }
        ]
        
        test.completed_at = datetime.utcnow()
        test.status = "completed"
        
        test.recommendations = [
            "Address compliance finding before scaled testing",
            "Document user feedback collection process",
        ]
        
        return test
    
    async def get_test_results(
        self,
        application_id: UUID,
    ) -> list[SandboxTest]:
        """Get all tests for an application."""
        return [
            t for t in self._tests.values()
            if t.application_id == application_id
        ]
    
    # =========================
    # REPORTING
    # =========================
    
    async def generate_sandbox_report(
        self,
        application_id: UUID,
    ) -> dict[str, Any]:
        """Generate a comprehensive sandbox participation report."""
        app = self._applications.get(application_id)
        if not app:
            raise ValueError("Application not found")
        
        tests = await self.get_test_results(application_id)
        
        return {
            "application_id": str(app.id),
            "provider": app.provider.value,
            "project_name": app.project_name,
            "status": app.status.value,
            "created_at": app.created_at.isoformat(),
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            
            "requirements_summary": {
                "total": app.requirements_total_count,
                "met": app.requirements_met_count,
                "completion_percentage": (app.requirements_met_count / app.requirements_total_count * 100) if app.requirements_total_count else 0,
            },
            
            "testing_summary": {
                "total_tests": len(tests),
                "completed_tests": len([t for t in tests if t.status == "completed"]),
                "findings_count": sum(len(t.compliance_findings) for t in tests),
            },
            
            "status_history": app.status_history,
            "feedback": app.feedback,
            
            "next_steps": self._generate_next_steps(app, tests),
        }
    
    def _generate_next_steps(
        self,
        app: SandboxApplication,
        tests: list[SandboxTest],
    ) -> list[str]:
        """Generate next steps based on application status."""
        steps = []
        
        if app.status == ApplicationStatus.DRAFT:
            unmet = [r for r in app.requirements if r.status != "met" and r.mandatory]
            if unmet:
                steps.append(f"Complete {len(unmet)} mandatory requirements")
            else:
                steps.append("Submit application for review")
        
        elif app.status == ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
            steps.append("Review and address regulator feedback")
            steps.append("Resubmit with additional information")
        
        elif app.status == ApplicationStatus.APPROVED:
            steps.append("Begin sandbox testing phase")
            steps.append("Set up safeguards and monitoring")
        
        elif app.status == ApplicationStatus.ACTIVE:
            pending_tests = [t for t in tests if t.status != "completed"]
            if pending_tests:
                steps.append(f"Complete {len(pending_tests)} pending tests")
            
            findings = [f for t in tests for f in t.compliance_findings]
            if findings:
                steps.append(f"Address {len(findings)} compliance findings")
        
        return steps


# Singleton instance
_sandbox_integration: RegulatorySandboxIntegration | None = None


def get_regulatory_sandbox_integration() -> RegulatorySandboxIntegration:
    """Get or create the regulatory sandbox integration singleton."""
    global _sandbox_integration
    if _sandbox_integration is None:
        _sandbox_integration = RegulatorySandboxIntegration()
    return _sandbox_integration
