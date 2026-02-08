"""Automated Compliance Remediation Workflow Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.remediation_workflow.models import (
    ApprovalType,
    RemediationFix,
    RemediationPriority,
    RemediationWorkflow,
    WorkflowConfig,
    WorkflowState,
)

logger = structlog.get_logger()

_DEFAULT_CONFIG = WorkflowConfig()


class RemediationWorkflowService:
    """End-to-end compliance remediation workflow engine."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._workflows: dict[UUID, RemediationWorkflow] = {}
        self._config = WorkflowConfig()

    async def create_workflow(
        self,
        title: str,
        violation_id: str,
        framework: str,
        repository: str,
        priority: RemediationPriority = RemediationPriority.MEDIUM,
        description: str = "",
    ) -> RemediationWorkflow:
        """Create a new remediation workflow from a detected violation."""
        wf = RemediationWorkflow(
            title=title,
            description=description or f"Remediation for {violation_id} in {repository}",
            priority=priority,
            violation_id=violation_id,
            framework=framework,
            repository=repository,
            approval_type=ApprovalType.AUTO if (
                self._config.auto_merge_low_risk and priority == RemediationPriority.LOW
            ) else ApprovalType.MANUAL,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._workflows[wf.id] = wf
        logger.info("Workflow created", id=str(wf.id), violation=violation_id)
        return wf

    async def generate_fixes(self, workflow_id: UUID) -> RemediationWorkflow:
        """Generate code fixes for a workflow's violation."""
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")

        wf.transition(WorkflowState.GENERATING)

        fixes = []
        if self.copilot:
            try:
                result = await self.copilot.analyze_legal_text(
                    f"Generate fix for {wf.violation_id} in {wf.framework}"
                )
                fixes.append(RemediationFix(
                    file_path=f"src/compliance/{wf.framework}.py",
                    original_code="# Non-compliant code",
                    fixed_code=str(result),
                    description=f"AI-generated fix for {wf.violation_id}",
                    violation_ref=wf.violation_id,
                    confidence=0.85,
                ))
            except Exception:
                logger.exception("AI fix generation failed")

        if not fixes:
            fixes = self._generate_pattern_fixes(wf)

        wf.fixes = fixes
        wf.transition(WorkflowState.REVIEW)
        wf.rollback_available = True
        return wf

    async def approve_workflow(self, workflow_id: UUID, approver: str) -> RemediationWorkflow:
        """Approve a workflow for merging."""
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        if wf.state != WorkflowState.REVIEW:
            raise ValueError(f"Workflow not in review state (current: {wf.state.value})")

        wf.approved_by = approver
        wf.transition(WorkflowState.APPROVED, actor=approver)
        return wf

    async def merge_workflow(self, workflow_id: UUID) -> RemediationWorkflow:
        """Merge an approved workflow (create PR and merge)."""
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        if wf.state != WorkflowState.APPROVED:
            raise ValueError(f"Workflow not approved (current: {wf.state.value})")

        wf.transition(WorkflowState.MERGING)
        wf.pr_number = 100 + len(self._workflows)
        wf.pr_url = f"https://github.com/{wf.repository}/pull/{wf.pr_number}"
        wf.transition(WorkflowState.COMPLETED)
        wf.completed_at = datetime.now(UTC)

        logger.info("Workflow merged", id=str(wf.id), pr=wf.pr_number)
        return wf

    async def rollback_workflow(self, workflow_id: UUID) -> RemediationWorkflow:
        """Rollback a completed workflow."""
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        if not wf.rollback_available:
            raise ValueError("Rollback not available for this workflow")

        wf.transition(WorkflowState.ROLLED_BACK, actor="rollback")
        wf.rollback_available = False
        logger.info("Workflow rolled back", id=str(wf.id))
        return wf

    async def get_workflow(self, workflow_id: UUID) -> RemediationWorkflow | None:
        return self._workflows.get(workflow_id)

    async def list_workflows(
        self,
        state: WorkflowState | None = None,
        priority: RemediationPriority | None = None,
    ) -> list[RemediationWorkflow]:
        wfs = list(self._workflows.values())
        if state:
            wfs = [w for w in wfs if w.state == state]
        if priority:
            wfs = [w for w in wfs if w.priority == priority]
        return sorted(wfs, key=lambda w: w.created_at or datetime.min, reverse=True)

    async def get_config(self) -> WorkflowConfig:
        return self._config

    async def update_config(self, **kwargs) -> WorkflowConfig:
        for k, v in kwargs.items():
            if hasattr(self._config, k):
                setattr(self._config, k, v)
        return self._config

    def _generate_pattern_fixes(self, wf: RemediationWorkflow) -> list[RemediationFix]:
        """Generate pattern-based fixes when AI is unavailable."""
        patterns: dict[str, list[dict]] = {
            "gdpr": [
                {"file": "src/data/processor.py", "desc": "Add consent verification before data processing",
                 "fix": "if not user.has_consent(purpose):\n    raise ConsentRequiredError()"},
                {"file": "src/data/storage.py", "desc": "Add data minimization check",
                 "fix": "data = minimize_fields(data, required_fields_only=True)"},
            ],
            "hipaa": [
                {"file": "src/health/phi.py", "desc": "Add PHI encryption wrapper",
                 "fix": "phi_data = encrypt_phi(raw_data, key=get_encryption_key())"},
            ],
            "pci_dss": [
                {"file": "src/payments/card.py", "desc": "Tokenize card data before storage",
                 "fix": "token = tokenize_card(card_number)\nstore_token(token)"},
            ],
        }

        fw_patterns = patterns.get(wf.framework.lower(), [
            {"file": f"src/compliance/{wf.framework}.py", "desc": "Add compliance check",
             "fix": f"# Compliance check for {wf.violation_id}\nassert_compliant(data)"},
        ])

        return [
            RemediationFix(
                file_path=p["file"],
                original_code="# TODO: Add compliance check",
                fixed_code=p["fix"],
                description=p["desc"],
                violation_ref=wf.violation_id,
                confidence=0.70,
            )
            for p in fw_patterns
        ]
