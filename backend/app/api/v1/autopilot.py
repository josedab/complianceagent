"""API endpoints for Agentic Compliance Autopilot."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.autopilot import (
    RemediationStatus,
    RemediationPriority,
    RemediationType,
    ApprovalStatus,
    AutopilotConfig,
    AutopilotEngine,
    get_autopilot_engine,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class AutopilotConfigRequest(BaseModel):
    """Configuration for autopilot."""
    
    enabled: bool = True
    auto_remediate_low_risk: bool = False
    auto_create_prs: bool = True
    auto_merge_approved: bool = False
    require_approval_for_critical: bool = True
    require_approval_for_code_changes: bool = True
    pr_branch_prefix: str = "compliance-fix/"
    pr_title_prefix: str = "[Compliance] "
    pr_labels: list[str] = Field(default_factory=lambda: ["compliance", "automated"])


class CreateSessionRequest(BaseModel):
    """Request to create an autopilot session."""
    
    name: str | None = None
    config: AutopilotConfigRequest | None = None


class ViolationInput(BaseModel):
    """Input for a compliance violation."""
    
    rule_id: str
    rule_name: str
    regulation: str = "General"
    requirement: str | None = None
    article: str | None = None
    severity: str = "medium"
    description: str
    impact: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    repository_id: str | None = None


class AnalyzeRequest(BaseModel):
    """Request to analyze violations."""
    
    violations: list[ViolationInput]


class ApproveActionRequest(BaseModel):
    """Request to approve an action."""
    
    comment: str | None = None


class RejectActionRequest(BaseModel):
    """Request to reject an action."""
    
    reason: str


class ActionResponse(BaseModel):
    """Response for a remediation action."""
    
    id: str
    violation_id: str
    action_type: str
    title: str
    description: str
    automated: bool
    requires_approval: bool
    status: str
    approval_status: str
    file_path: str | None
    original_code: str | None
    fixed_code: str | None
    diff: str | None
    pr_url: str | None
    branch_name: str | None
    approved_by: str | None
    approved_at: str | None
    created_at: str


class ViolationResponse(BaseModel):
    """Response for a compliance violation."""
    
    id: str
    rule_id: str
    rule_name: str
    regulation: str
    requirement: str | None
    severity: str
    priority: str
    description: str
    file_path: str | None
    line_number: int | None


class PlanResponse(BaseModel):
    """Response for a remediation plan."""
    
    id: str
    name: str
    description: str
    total_violations: int
    remediated_count: int
    pending_count: int
    failed_count: int
    status: str
    created_at: str
    updated_at: str


class PlanDetailResponse(PlanResponse):
    """Detailed plan response."""
    
    violations: list[ViolationResponse]
    actions: list[ActionResponse]


class SessionResponse(BaseModel):
    """Response for an autopilot session."""
    
    id: str
    name: str
    status: str
    total_violations: int
    total_actions: int
    completed_actions: int
    failed_actions: int
    pending_approvals: int
    started_at: str
    completed_at: str | None


class ExecutionResultResponse(BaseModel):
    """Response for action execution."""
    
    action_id: str
    success: bool
    execution_time_ms: float | None
    files_modified: list[str]
    pr_created: bool
    pr_url: str | None
    validation_passed: bool
    error: str | None


# ============================================================================
# Session Management
# ============================================================================


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SessionResponse:
    """Create a new autopilot session.
    
    The autopilot can analyze compliance violations and generate
    automated remediation plans with code fixes and pull requests.
    """
    engine = get_autopilot_engine()
    
    config = None
    if request.config:
        config = AutopilotConfig(
            enabled=request.config.enabled,
            auto_remediate_low_risk=request.config.auto_remediate_low_risk,
            auto_create_prs=request.config.auto_create_prs,
            auto_merge_approved=request.config.auto_merge_approved,
            require_approval_for_critical=request.config.require_approval_for_critical,
            require_approval_for_code_changes=request.config.require_approval_for_code_changes,
            pr_branch_prefix=request.config.pr_branch_prefix,
            pr_title_prefix=request.config.pr_title_prefix,
            pr_labels=request.config.pr_labels,
        )
    
    session = await engine.create_session(
        organization_id=organization.id,
        name=request.name,
        config=config,
    )
    
    return SessionResponse(
        id=str(session.id),
        name=session.name,
        status=session.status.value,
        total_violations=session.total_violations,
        total_actions=session.total_actions,
        completed_actions=session.completed_actions,
        failed_actions=session.failed_actions,
        pending_approvals=session.pending_approvals,
        started_at=session.started_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SessionResponse:
    """Get an autopilot session by ID."""
    engine = get_autopilot_engine()
    
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )
    
    session = await engine.get_session(session_uuid)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    return SessionResponse(
        id=str(session.id),
        name=session.name,
        status=session.status.value,
        total_violations=session.total_violations,
        total_actions=session.total_actions,
        completed_actions=session.completed_actions,
        failed_actions=session.failed_actions,
        pending_approvals=session.pending_approvals,
        started_at=session.started_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )


# ============================================================================
# Analysis and Planning
# ============================================================================


@router.post("/sessions/{session_id}/analyze", response_model=PlanDetailResponse)
async def analyze_violations(
    session_id: str,
    request: AnalyzeRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PlanDetailResponse:
    """Analyze violations and generate a remediation plan.
    
    Takes a list of compliance violations and generates:
    - Remediation actions with automated fixes
    - Code diffs and PR suggestions
    - Validation and rollback steps
    """
    engine = get_autopilot_engine()
    
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )
    
    session = await engine.get_session(session_uuid)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    violations_data = [v.model_dump() for v in request.violations]
    plan = await engine.analyze_violations(session_uuid, violations_data)
    
    return PlanDetailResponse(
        id=str(plan.id),
        name=plan.name,
        description=plan.description,
        total_violations=plan.total_violations,
        remediated_count=plan.remediated_count,
        pending_count=plan.pending_count,
        failed_count=plan.failed_count,
        status=plan.status.value,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        violations=[
            ViolationResponse(
                id=str(v.id),
                rule_id=v.rule_id,
                rule_name=v.rule_name,
                regulation=v.regulation,
                requirement=v.requirement,
                severity=v.severity,
                priority=v.priority.value,
                description=v.description,
                file_path=v.file_path,
                line_number=v.line_number,
            )
            for v in plan.violations
        ],
        actions=[
            ActionResponse(
                id=str(a.id),
                violation_id=str(a.violation_id),
                action_type=a.action_type.value,
                title=a.title,
                description=a.description,
                automated=a.automated,
                requires_approval=a.requires_approval,
                status=a.status.value,
                approval_status=a.approval_status.value,
                file_path=a.file_path,
                original_code=a.original_code,
                fixed_code=a.fixed_code,
                diff=a.diff,
                pr_url=a.pr_url,
                branch_name=a.branch_name,
                approved_by=a.approved_by,
                approved_at=a.approved_at.isoformat() if a.approved_at else None,
                created_at=a.created_at.isoformat(),
            )
            for a in plan.actions
        ],
    )


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse)
async def get_plan(
    plan_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PlanDetailResponse:
    """Get a remediation plan by ID."""
    engine = get_autopilot_engine()
    
    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format",
        )
    
    plan = await engine.get_plan(plan_uuid)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )
    
    return PlanDetailResponse(
        id=str(plan.id),
        name=plan.name,
        description=plan.description,
        total_violations=plan.total_violations,
        remediated_count=plan.remediated_count,
        pending_count=plan.pending_count,
        failed_count=plan.failed_count,
        status=plan.status.value,
        created_at=plan.created_at.isoformat(),
        updated_at=plan.updated_at.isoformat(),
        violations=[
            ViolationResponse(
                id=str(v.id),
                rule_id=v.rule_id,
                rule_name=v.rule_name,
                regulation=v.regulation,
                requirement=v.requirement,
                severity=v.severity,
                priority=v.priority.value,
                description=v.description,
                file_path=v.file_path,
                line_number=v.line_number,
            )
            for v in plan.violations
        ],
        actions=[
            ActionResponse(
                id=str(a.id),
                violation_id=str(a.violation_id),
                action_type=a.action_type.value,
                title=a.title,
                description=a.description,
                automated=a.automated,
                requires_approval=a.requires_approval,
                status=a.status.value,
                approval_status=a.approval_status.value,
                file_path=a.file_path,
                original_code=a.original_code,
                fixed_code=a.fixed_code,
                diff=a.diff,
                pr_url=a.pr_url,
                branch_name=a.branch_name,
                approved_by=a.approved_by,
                approved_at=a.approved_at.isoformat() if a.approved_at else None,
                created_at=a.created_at.isoformat(),
            )
            for a in plan.actions
        ],
    )


# ============================================================================
# Approval Workflow
# ============================================================================


@router.get("/approvals/pending", response_model=list[ActionResponse])
async def get_pending_approvals(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[ActionResponse]:
    """Get all actions pending approval for the organization."""
    engine = get_autopilot_engine()
    
    actions = await engine.get_pending_approvals(organization.id)
    
    return [
        ActionResponse(
            id=str(a.id),
            violation_id=str(a.violation_id),
            action_type=a.action_type.value,
            title=a.title,
            description=a.description,
            automated=a.automated,
            requires_approval=a.requires_approval,
            status=a.status.value,
            approval_status=a.approval_status.value,
            file_path=a.file_path,
            original_code=a.original_code,
            fixed_code=a.fixed_code,
            diff=a.diff,
            pr_url=a.pr_url,
            branch_name=a.branch_name,
            approved_by=a.approved_by,
            approved_at=a.approved_at.isoformat() if a.approved_at else None,
            created_at=a.created_at.isoformat(),
        )
        for a in actions
    ]


@router.post("/actions/{action_id}/approve", response_model=ActionResponse)
async def approve_action(
    action_id: str,
    request: ApproveActionRequest | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> ActionResponse:
    """Approve a remediation action for execution."""
    engine = get_autopilot_engine()
    
    try:
        action_uuid = UUID(action_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action ID format",
        )
    
    approver = f"User:{member.user_id}" if hasattr(member, 'user_id') else "Authorized Approver"
    
    action = await engine.approve_action(action_uuid, approver)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )
    
    return ActionResponse(
        id=str(action.id),
        violation_id=str(action.violation_id),
        action_type=action.action_type.value,
        title=action.title,
        description=action.description,
        automated=action.automated,
        requires_approval=action.requires_approval,
        status=action.status.value,
        approval_status=action.approval_status.value,
        file_path=action.file_path,
        original_code=action.original_code,
        fixed_code=action.fixed_code,
        diff=action.diff,
        pr_url=action.pr_url,
        branch_name=action.branch_name,
        approved_by=action.approved_by,
        approved_at=action.approved_at.isoformat() if action.approved_at else None,
        created_at=action.created_at.isoformat(),
    )


@router.post("/actions/{action_id}/reject", response_model=ActionResponse)
async def reject_action(
    action_id: str,
    request: RejectActionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ActionResponse:
    """Reject a remediation action."""
    engine = get_autopilot_engine()
    
    try:
        action_uuid = UUID(action_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action ID format",
        )
    
    rejector = f"User:{member.user_id}" if hasattr(member, 'user_id') else "Authorized User"
    
    action = await engine.reject_action(action_uuid, rejector, request.reason)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )
    
    return ActionResponse(
        id=str(action.id),
        violation_id=str(action.violation_id),
        action_type=action.action_type.value,
        title=action.title,
        description=action.description,
        automated=action.automated,
        requires_approval=action.requires_approval,
        status=action.status.value,
        approval_status=action.approval_status.value,
        file_path=action.file_path,
        original_code=action.original_code,
        fixed_code=action.fixed_code,
        diff=action.diff,
        pr_url=action.pr_url,
        branch_name=action.branch_name,
        approved_by=action.approved_by,
        approved_at=action.approved_at.isoformat() if action.approved_at else None,
        created_at=action.created_at.isoformat(),
    )


# ============================================================================
# Execution
# ============================================================================


@router.post("/actions/{action_id}/execute", response_model=ExecutionResultResponse)
async def execute_action(
    action_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ExecutionResultResponse:
    """Execute a single remediation action."""
    engine = get_autopilot_engine()
    
    try:
        action_uuid = UUID(action_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action ID format",
        )
    
    try:
        result = await engine.execute_action(action_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return ExecutionResultResponse(
        action_id=str(result.action_id),
        success=result.success,
        execution_time_ms=result.execution_time_ms,
        files_modified=result.files_modified,
        pr_created=result.pr_created,
        pr_url=result.pr_url,
        validation_passed=result.validation_passed,
        error=result.error,
    )


@router.post("/plans/{plan_id}/execute", response_model=list[ExecutionResultResponse])
async def execute_plan(
    plan_id: str,
    execute_approved_only: bool = True,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> list[ExecutionResultResponse]:
    """Execute all actions in a remediation plan.
    
    By default, only executes approved actions. Set execute_approved_only=false
    to execute all actions (not recommended for production).
    """
    engine = get_autopilot_engine()
    
    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan ID format",
        )
    
    try:
        results = await engine.execute_plan(plan_uuid, execute_approved_only)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return [
        ExecutionResultResponse(
            action_id=str(r.action_id),
            success=r.success,
            execution_time_ms=r.execution_time_ms,
            files_modified=r.files_modified,
            pr_created=r.pr_created,
            pr_url=r.pr_url,
            validation_passed=r.validation_passed,
            error=r.error,
        )
        for r in results
    ]


@router.post("/actions/{action_id}/rollback", response_model=ExecutionResultResponse)
async def rollback_action(
    action_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ExecutionResultResponse:
    """Rollback a completed remediation action."""
    engine = get_autopilot_engine()
    
    try:
        action_uuid = UUID(action_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action ID format",
        )
    
    try:
        result = await engine.rollback_action(action_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return ExecutionResultResponse(
        action_id=str(result.action_id),
        success=result.success,
        execution_time_ms=result.execution_time_ms,
        files_modified=result.files_modified,
        pr_created=result.pr_created,
        pr_url=result.pr_url,
        validation_passed=result.validation_passed,
        error=result.error,
    )


# ============================================================================
# Quick Actions
# ============================================================================


@router.post("/quick-fix")
async def quick_fix(
    violations: list[ViolationInput],
    auto_approve_low_risk: bool = False,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Quick fix endpoint for CI/CD integration.
    
    Creates a session, analyzes violations, and optionally auto-approves
    low-risk fixes. Returns a summary suitable for pipeline output.
    """
    engine = get_autopilot_engine()
    
    # Create session
    config = AutopilotConfig(
        auto_remediate_low_risk=auto_approve_low_risk,
    )
    session = await engine.create_session(
        organization_id=organization.id if organization else UUID('00000000-0000-0000-0000-000000000000'),
        name="Quick Fix Session",
        config=config,
    )
    
    # Analyze violations
    violations_data = [v.model_dump() for v in violations]
    plan = await engine.analyze_violations(session.id, violations_data)
    
    # Auto-approve low risk if enabled
    approved_count = 0
    if auto_approve_low_risk:
        for action in plan.actions:
            violation = next((v for v in plan.violations if v.id == action.violation_id), None)
            if violation and violation.severity == "low":
                await engine.approve_action(action.id, "auto-approved")
                approved_count += 1
    
    return {
        "session_id": str(session.id),
        "plan_id": str(plan.id),
        "summary": {
            "total_violations": plan.total_violations,
            "actions_generated": len(plan.actions),
            "auto_approved": approved_count,
            "pending_approval": len(plan.actions) - approved_count,
        },
        "actions": [
            {
                "id": str(a.id),
                "title": a.title,
                "type": a.action_type.value,
                "file": a.file_path,
                "status": a.approval_status.value,
                "has_fix": a.fixed_code is not None,
            }
            for a in plan.actions
        ],
        "next_steps": [
            f"Review and approve pending actions at /autopilot/approvals/pending",
            f"Execute approved actions: POST /autopilot/plans/{plan.id}/execute",
        ] if len(plan.actions) > approved_count else [
            f"Execute approved actions: POST /autopilot/plans/{plan.id}/execute",
        ],
    }
