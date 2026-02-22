"""API endpoints for Automated Compliance Remediation Workflows."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.remediation_workflow import (
    RemediationPriority,
    RemediationWorkflowService,
    WorkflowState,
)


logger = structlog.get_logger()
router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    title: str = Field(..., min_length=1)
    violation_id: str = Field(...)
    framework: str = Field(...)
    repository: str = Field(...)
    priority: str = Field(default="medium")
    description: str = Field(default="")


class ApproveRequest(BaseModel):
    approver: str = Field(...)


class WorkflowSchema(BaseModel):
    id: str
    title: str
    description: str
    state: str
    priority: str
    violation_id: str
    framework: str
    repository: str
    fixes_count: int
    pr_number: int | None
    pr_url: str | None
    rollback_available: bool
    created_at: str | None


class FixSchema(BaseModel):
    id: str
    file_path: str
    description: str
    confidence: float


class ApprovalStepSchema(BaseModel):
    id: str
    approver_role: str
    approver_name: str
    status: str
    comment: str
    decided_at: str | None
    order: int


class ApprovalChainSchema(BaseModel):
    id: str
    workflow_id: str | None
    steps: list[ApprovalStepSchema]
    current_step: int
    is_complete: bool
    final_status: str


class ProcessApprovalRequest(BaseModel):
    step_id: str
    approved: bool
    comment: str = ""


class RollbackRequest(BaseModel):
    reason: str = ""
    rolled_back_by: str = "user"


class RollbackRecordSchema(BaseModel):
    id: str
    workflow_id: str | None
    reason: str
    rolled_back_by: str
    original_state: str
    rolled_back_at: str
    files_reverted: list[str]
    success: bool


class RemediationAnalyticsSchema(BaseModel):
    total_workflows: int
    completed_workflows: int
    in_progress_workflows: int
    failed_workflows: int
    rolled_back_workflows: int
    avg_time_to_remediate_hours: float
    fix_success_rate: float
    auto_fix_rate: float
    top_violation_types: list[dict[str, Any]]
    monthly_trend: list[dict[str, Any]]


def _wf_to_schema(wf) -> WorkflowSchema:
    return WorkflowSchema(
        id=str(wf.id),
        title=wf.title,
        description=wf.description,
        state=wf.state.value,
        priority=wf.priority.value,
        violation_id=wf.violation_id,
        framework=wf.framework,
        repository=wf.repository,
        fixes_count=len(wf.fixes),
        pr_number=wf.pr_number,
        pr_url=wf.pr_url,
        rollback_available=wf.rollback_available,
        created_at=wf.created_at.isoformat() if wf.created_at else None,
    )


@router.get(
    "/analytics", response_model=RemediationAnalyticsSchema, summary="Get remediation analytics"
)
async def get_analytics(db: DB, copilot: CopilotDep) -> RemediationAnalyticsSchema:
    """Get remediation workflow analytics."""
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    analytics = service.get_analytics()
    return RemediationAnalyticsSchema(**analytics.to_dict())


@router.get(
    "/rollback-history", response_model=list[RollbackRecordSchema], summary="Get rollback history"
)
async def get_rollback_history(
    db: DB, copilot: CopilotDep, workflow_id: str | None = None
) -> list[RollbackRecordSchema]:
    """Get rollback history for workflows."""
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    records = service.get_rollback_history(workflow_id)
    return [RollbackRecordSchema(**r.to_dict()) for r in records]


@router.post(
    "/workflows",
    response_model=WorkflowSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create remediation workflow",
)
async def create_workflow(
    request: CreateWorkflowRequest, db: DB, copilot: CopilotDep
) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    priority = (
        RemediationPriority(request.priority)
        if request.priority in [p.value for p in RemediationPriority]
        else RemediationPriority.MEDIUM
    )
    wf = await service.create_workflow(
        title=request.title,
        violation_id=request.violation_id,
        framework=request.framework,
        repository=request.repository,
        priority=priority,
        description=request.description,
    )
    return _wf_to_schema(wf)


@router.get("/workflows", response_model=list[WorkflowSchema], summary="List workflows")
async def list_workflows(
    db: DB, copilot: CopilotDep, state: str | None = None
) -> list[WorkflowSchema]:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    ws = WorkflowState(state) if state else None
    workflows = await service.list_workflows(state=ws)
    return [_wf_to_schema(wf) for wf in workflows]


@router.post(
    "/workflows/{workflow_id}/generate", response_model=WorkflowSchema, summary="Generate fixes"
)
async def generate_fixes(workflow_id: str, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.generate_fixes(UUID(workflow_id))
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post(
    "/workflows/{workflow_id}/approve", response_model=WorkflowSchema, summary="Approve workflow"
)
async def approve_workflow(
    workflow_id: str, request: ApproveRequest, db: DB, copilot: CopilotDep
) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.approve_workflow(UUID(workflow_id), request.approver)
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/workflows/{workflow_id}/merge", response_model=WorkflowSchema, summary="Merge workflow"
)
async def merge_workflow(workflow_id: str, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.merge_workflow(UUID(workflow_id))
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/workflows/{workflow_id}/rollback", response_model=WorkflowSchema, summary="Rollback workflow"
)
async def rollback_workflow(workflow_id: str, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.rollback_workflow(UUID(workflow_id))
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/workflows/{workflow_id}/approval-chain",
    response_model=ApprovalChainSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create approval chain",
)
async def create_approval_chain(
    workflow_id: str, db: DB, copilot: CopilotDep
) -> ApprovalChainSchema:
    """Create a multi-level approval chain for a workflow."""
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    chain = service.create_approval_chain(workflow_id)
    return ApprovalChainSchema(**chain.to_dict())


@router.post(
    "/workflows/{workflow_id}/process-approval",
    response_model=ApprovalChainSchema,
    summary="Process approval step",
)
async def process_approval(
    workflow_id: str, request: ProcessApprovalRequest, db: DB, copilot: CopilotDep
) -> ApprovalChainSchema:
    """Process an approval or rejection in the chain."""
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    chain = service.process_approval(
        workflow_id, request.step_id, request.approved, request.comment
    )
    return ApprovalChainSchema(**chain.to_dict())


@router.post(
    "/workflows/{workflow_id}/rollback-with-record",
    response_model=RollbackRecordSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Rollback workflow with record",
)
async def rollback_workflow_with_record(
    workflow_id: str, request: RollbackRequest, db: DB, copilot: CopilotDep
) -> RollbackRecordSchema:
    """Roll back a remediation workflow and create a rollback record."""
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    record = service.rollback_workflow_with_record(
        workflow_id, request.reason, request.rolled_back_by
    )
    return RollbackRecordSchema(**record.to_dict())


@router.get("/config", summary="Get workflow configuration")
async def get_config(db: DB, copilot: CopilotDep) -> dict:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    cfg = await service.get_config()
    return {
        "auto_merge_low_risk": cfg.auto_merge_low_risk,
        "require_ci_pass": cfg.require_ci_pass,
        "require_review": cfg.require_review,
        "max_auto_fixes_per_day": cfg.max_auto_fixes_per_day,
    }


# ---------------------------------------------------------------------------
# v2: Fix Templates, State Validation & Template Application
# ---------------------------------------------------------------------------


class FixTemplateSchema(BaseModel):
    """A reusable compliance fix template."""

    id: str
    framework: str
    violation_pattern: str
    description: str
    language: str
    file_pattern: str
    confidence: float
    tags: list[str]


class ApplyTemplateRequest(BaseModel):
    """Request to apply a fix template."""

    template_id: str = Field(..., description="Template identifier")
    variables: dict[str, str] = Field(default_factory=dict, description="Template variables")
    file_path: str = Field("", description="Target file path")


class ApplyTemplateResponse(BaseModel):
    """Result of applying a fix template."""

    file_path: str
    fixed_code: str
    description: str
    violation_ref: str
    confidence: float


class TransitionValidationRequest(BaseModel):
    """Request to validate a workflow state transition."""

    current_state: str
    target_state: str


class TransitionValidationResponse(BaseModel):
    """Result of state transition validation."""

    valid: bool
    current_state: str
    target_state: str
    allowed_transitions: list[str]


@router.get("/templates", response_model=list[FixTemplateSchema], summary="List fix templates")
async def list_fix_templates(
    framework: str | None = None,
) -> list[FixTemplateSchema]:
    """List all available compliance fix templates, optionally filtered by framework."""
    from app.services.remediation_workflow.fix_templates import (
        BUILTIN_TEMPLATES,
        get_templates_for_framework,
    )

    templates = get_templates_for_framework(framework) if framework else BUILTIN_TEMPLATES
    return [
        FixTemplateSchema(
            id=t.id,
            framework=t.framework,
            violation_pattern=t.violation_pattern,
            description=t.description,
            language=t.language.value,
            file_pattern=t.file_pattern,
            confidence=t.confidence,
            tags=t.tags,
        )
        for t in templates
    ]


@router.get(
    "/templates/{template_id}", response_model=FixTemplateSchema, summary="Get fix template"
)
async def get_fix_template(template_id: str) -> FixTemplateSchema:
    """Get a specific fix template by ID."""
    from app.services.remediation_workflow.fix_templates import get_template_by_id

    template = get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return FixTemplateSchema(
        id=template.id,
        framework=template.framework,
        violation_pattern=template.violation_pattern,
        description=template.description,
        language=template.language.value,
        file_pattern=template.file_pattern,
        confidence=template.confidence,
        tags=template.tags,
    )


@router.post("/templates/apply", response_model=ApplyTemplateResponse, summary="Apply fix template")
async def apply_fix_template(request: ApplyTemplateRequest) -> ApplyTemplateResponse:
    """Instantiate a fix template with provided variables to generate a concrete fix."""
    from app.services.remediation_workflow.fix_templates import apply_template, get_template_by_id

    template = get_template_by_id(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {request.template_id} not found")

    fix = apply_template(template, variables=request.variables, file_path=request.file_path)
    return ApplyTemplateResponse(
        file_path=fix.file_path,
        fixed_code=fix.fixed_code,
        description=fix.description,
        violation_ref=fix.violation_ref,
        confidence=fix.confidence,
    )


@router.post(
    "/validate-transition",
    response_model=TransitionValidationResponse,
    summary="Validate state transition",
)
async def validate_state_transition(
    request: TransitionValidationRequest,
) -> TransitionValidationResponse:
    """Check whether a workflow state transition is valid."""
    from app.services.remediation_workflow.fix_templates import (
        VALID_TRANSITIONS,
        validate_transition,
    )
    from app.services.remediation_workflow.models import WorkflowState

    try:
        current = WorkflowState(request.current_state)
        target = WorkflowState(request.target_state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid state: {exc}") from exc

    valid = validate_transition(current, target)
    allowed = [s.value for s in VALID_TRANSITIONS.get(current, [])]
    return TransitionValidationResponse(
        valid=valid,
        current_state=current.value,
        target_state=target.value,
        allowed_transitions=allowed,
    )
