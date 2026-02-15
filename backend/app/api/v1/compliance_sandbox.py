"""API endpoints for Compliance Sandbox Environments."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.compliance_sandbox import (
    ComplianceSandboxService,
    DifficultyLevel,
    SandboxStatus,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request Models ---


class CreateSandboxRequest(BaseModel):
    scenario_id: str = Field(..., description="ID of the scenario to provision")


class CheckViolationRequest(BaseModel):
    submitted_code: str = Field(..., description="Code submitted as the fix for the violation")


# --- Response Models ---


class ViolationScenarioSchema(BaseModel):
    id: str
    type: str
    title: str
    description: str
    file_path: str
    code_snippet: str
    points: int
    regulation_article: str


class SandboxScenarioSchema(BaseModel):
    id: str
    title: str
    description: str
    regulation: str
    difficulty: str
    estimated_minutes: int
    learning_objectives: list[str]
    prerequisites: list[str]
    tags: list[str]
    violations: list[ViolationScenarioSchema]


class SandboxScenarioSummarySchema(BaseModel):
    id: str
    title: str
    description: str
    regulation: str
    difficulty: str
    estimated_minutes: int
    tags: list[str]
    violation_count: int


class SandboxResourcesSchema(BaseModel):
    cpu_limit: float
    memory_limit_mb: int
    storage_limit_mb: int
    max_duration_minutes: int


class SandboxProgressSchema(BaseModel):
    completed_violations: int
    total_violations: int
    score: int
    time_elapsed_minutes: float
    hints_used: int
    completed_at: str | None


class SandboxEnvironmentSchema(BaseModel):
    id: str
    org_id: str
    user_id: str
    scenario_id: str
    status: str
    created_at: str
    expires_at: str
    resources: SandboxResourcesSchema
    connection_info: dict
    progress: SandboxProgressSchema


class CheckViolationResultSchema(BaseModel):
    violation_id: str
    passed: bool
    points_earned: int
    feedback: str
    regulation_article: str


class SandboxResultSchema(BaseModel):
    id: str
    sandbox_id: str
    scenario_id: str
    score: int
    max_score: int
    completion_pct: float
    time_minutes: float
    violations_fixed: list[str]
    violations_missed: list[str]
    feedback: str
    badge_earned: str | None


class HintResponseSchema(BaseModel):
    violation_id: str
    hint: str


class SandboxBadgeSchema(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    criteria: str
    earned_at: str | None


class LeaderboardEntrySchema(BaseModel):
    user_id: str
    total_score: int
    scenarios_completed: int
    badges_count: int


# --- Helpers ---


def _scenario_to_summary(s) -> SandboxScenarioSummarySchema:
    return SandboxScenarioSummarySchema(
        id=s.id,
        title=s.title,
        description=s.description,
        regulation=s.regulation,
        difficulty=s.difficulty.value,
        estimated_minutes=s.estimated_minutes,
        tags=s.tags,
        violation_count=len(s.violations),
    )


def _scenario_to_schema(s) -> SandboxScenarioSchema:
    return SandboxScenarioSchema(
        id=s.id,
        title=s.title,
        description=s.description,
        regulation=s.regulation,
        difficulty=s.difficulty.value,
        estimated_minutes=s.estimated_minutes,
        learning_objectives=s.learning_objectives,
        prerequisites=s.prerequisites,
        tags=s.tags,
        violations=[
            ViolationScenarioSchema(
                id=v.id,
                type=v.type.value,
                title=v.title,
                description=v.description,
                file_path=v.file_path,
                code_snippet=v.code_snippet,
                points=v.points,
                regulation_article=v.regulation_article,
            )
            for v in s.violations
        ],
    )


def _sandbox_to_schema(s) -> SandboxEnvironmentSchema:
    return SandboxEnvironmentSchema(
        id=str(s.id),
        org_id=str(s.org_id),
        user_id=str(s.user_id),
        scenario_id=s.scenario_id,
        status=s.status.value,
        created_at=s.created_at.isoformat(),
        expires_at=s.expires_at.isoformat(),
        resources=SandboxResourcesSchema(
            cpu_limit=s.resources.cpu_limit,
            memory_limit_mb=s.resources.memory_limit_mb,
            storage_limit_mb=s.resources.storage_limit_mb,
            max_duration_minutes=s.resources.max_duration_minutes,
        ),
        connection_info=s.connection_info,
        progress=SandboxProgressSchema(
            completed_violations=s.progress.completed_violations,
            total_violations=s.progress.total_violations,
            score=s.progress.score,
            time_elapsed_minutes=s.progress.time_elapsed_minutes,
            hints_used=s.progress.hints_used,
            completed_at=s.progress.completed_at.isoformat() if s.progress.completed_at else None,
        ),
    )


# --- Endpoints ---


@router.get(
    "/scenarios",
    response_model=list[SandboxScenarioSummarySchema],
    summary="List available scenarios",
    description="List sandbox training scenarios with optional difficulty and regulation filters.",
)
async def list_scenarios(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    difficulty: DifficultyLevel | None = None,
    regulation: str | None = Query(None, description="Filter by regulation (e.g., GDPR, HIPAA)"),
) -> list[SandboxScenarioSummarySchema]:
    service = ComplianceSandboxService(db=db)
    scenarios = await service.list_scenarios(difficulty=difficulty, regulation=regulation)
    return [_scenario_to_summary(s) for s in scenarios]


@router.get(
    "/scenarios/{scenario_id}",
    response_model=SandboxScenarioSchema,
    summary="Get scenario details",
    description="Get full details of a sandbox scenario including violations to fix.",
)
async def get_scenario(
    scenario_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SandboxScenarioSchema:
    service = ComplianceSandboxService(db=db)
    scenario = await service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return _scenario_to_schema(scenario)


@router.post(
    "/environments",
    response_model=SandboxEnvironmentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create sandbox environment",
    description="Provision a new ephemeral sandbox environment for a training scenario.",
)
async def create_sandbox(
    request: CreateSandboxRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SandboxEnvironmentSchema:
    service = ComplianceSandboxService(db=db)
    try:
        sandbox = await service.create_sandbox(
            org_id=organization.id,
            user_id=member.user_id,
            scenario_id=request.scenario_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _sandbox_to_schema(sandbox)


@router.get(
    "/environments",
    response_model=list[SandboxEnvironmentSchema],
    summary="List user sandboxes",
    description="List sandbox environments belonging to the current user.",
)
async def list_user_sandboxes(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    sandbox_status: SandboxStatus | None = Query(None, alias="status", description="Filter by sandbox status"),
) -> list[SandboxEnvironmentSchema]:
    service = ComplianceSandboxService(db=db)
    sandboxes = await service.list_user_sandboxes(user_id=member.user_id, status=sandbox_status)
    return [_sandbox_to_schema(s) for s in sandboxes]


@router.get(
    "/environments/{sandbox_id}",
    response_model=SandboxEnvironmentSchema,
    summary="Get sandbox status",
    description="Get the current status and progress of a sandbox environment.",
)
async def get_sandbox(
    sandbox_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SandboxEnvironmentSchema:
    service = ComplianceSandboxService(db=db)
    sandbox = await service.get_sandbox(sandbox_id)
    if sandbox is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandbox not found")
    return _sandbox_to_schema(sandbox)


@router.post(
    "/environments/{sandbox_id}/check/{violation_id}",
    response_model=CheckViolationResultSchema,
    summary="Check a violation fix",
    description="Submit code to check if a specific violation has been fixed.",
)
async def check_violation(
    sandbox_id: UUID,
    violation_id: str,
    request: CheckViolationRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CheckViolationResultSchema:
    service = ComplianceSandboxService(db=db)
    try:
        result = await service.check_violation(
            sandbox_id=sandbox_id,
            violation_id=violation_id,
            submitted_code=request.submitted_code,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return CheckViolationResultSchema(**result)


@router.post(
    "/environments/{sandbox_id}/submit",
    response_model=SandboxResultSchema,
    summary="Submit final solution",
    description="Submit the sandbox for final scoring and receive results and feedback.",
)
async def submit_solution(
    sandbox_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SandboxResultSchema:
    service = ComplianceSandboxService(db=db)
    try:
        result = await service.submit_solution(sandbox_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SandboxResultSchema(
        id=str(result.id),
        sandbox_id=str(result.sandbox_id),
        scenario_id=result.scenario_id,
        score=result.score,
        max_score=result.max_score,
        completion_pct=result.completion_pct,
        time_minutes=result.time_minutes,
        violations_fixed=result.violations_fixed,
        violations_missed=result.violations_missed,
        feedback=result.feedback,
        badge_earned=result.badge_earned,
    )


@router.post(
    "/environments/{sandbox_id}/hint/{violation_id}",
    response_model=HintResponseSchema,
    summary="Get hint",
    description="Get a hint for a specific violation. Hints count toward your final score.",
)
async def get_hint(
    sandbox_id: UUID,
    violation_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> HintResponseSchema:
    service = ComplianceSandboxService(db=db)
    try:
        hint = await service.get_hint(sandbox_id, violation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HintResponseSchema(violation_id=violation_id, hint=hint)


@router.get(
    "/badges",
    response_model=list[SandboxBadgeSchema],
    summary="Get user badges",
    description="Get badges earned by the current user through sandbox completions.",
)
async def get_user_badges(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[SandboxBadgeSchema]:
    service = ComplianceSandboxService(db=db)
    badges = await service.get_user_badges(member.user_id)
    return [
        SandboxBadgeSchema(
            id=b.id,
            name=b.name,
            description=b.description,
            icon=b.icon,
            criteria=b.criteria,
            earned_at=b.earned_at.isoformat() if b.earned_at else None,
        )
        for b in badges
    ]


@router.get(
    "/leaderboard",
    response_model=list[LeaderboardEntrySchema],
    summary="Get sandbox leaderboard",
    description="Get the top scores across all sandbox training sessions.",
)
async def get_leaderboard(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    limit: int = Query(20, ge=1, le=100, description="Maximum entries to return"),
) -> list[LeaderboardEntrySchema]:
    service = ComplianceSandboxService(db=db)
    entries = await service.get_leaderboard(limit=limit)
    return [LeaderboardEntrySchema(**e) for e in entries]


@router.delete(
    "/environments/{sandbox_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Terminate sandbox",
    description="Terminate a running sandbox environment.",
)
async def terminate_sandbox(
    sandbox_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> None:
    service = ComplianceSandboxService(db=db)
    terminated = await service.terminate_sandbox(sandbox_id)
    if not terminated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandbox not found")


# --- What-If Simulation Endpoints ---


class WhatIfScenarioSchema(BaseModel):
    id: str
    title: str
    description: str
    change_type: str
    jurisdiction: str
    regulation: str
    effective_date: str
    probability: float


class WhatIfImpactSchema(BaseModel):
    scenario_id: str
    overall_risk_score: float
    affected_modules: list[dict]
    estimated_effort_hours: float
    estimated_cost_usd: float
    compliance_gap_count: int
    recommendations: list[str]
    heatmap: list[dict]


class RunWhatIfRequest(BaseModel):
    scenario_id: str = Field(..., description="What-if scenario to simulate")
    repo: str = Field(default="", description="Repository to analyze")


@router.get(
    "/whatif-scenarios",
    response_model=list[WhatIfScenarioSchema],
    summary="List what-if scenarios",
    description="List available regulatory change what-if simulation scenarios.",
)
async def list_whatif_scenarios(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[WhatIfScenarioSchema]:
    service = ComplianceSandboxService(db=db)
    scenarios = await service.list_whatif_scenarios()
    return [
        WhatIfScenarioSchema(
            id=s.id, title=s.title, description=s.description,
            change_type=s.change_type, jurisdiction=s.jurisdiction,
            regulation=s.regulation, effective_date=s.effective_date,
            probability=s.probability,
        )
        for s in scenarios
    ]


@router.post(
    "/whatif-simulate",
    response_model=WhatIfImpactSchema,
    summary="Run what-if simulation",
    description="Simulate impact of a regulatory change on your codebase.",
)
async def run_whatif_simulation(
    request: RunWhatIfRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> WhatIfImpactSchema:
    service = ComplianceSandboxService(db=db)
    try:
        impact = await service.run_whatif_simulation(
            scenario_id=request.scenario_id, repo=request.repo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return WhatIfImpactSchema(
        scenario_id=impact.scenario_id,
        overall_risk_score=impact.overall_risk_score,
        affected_modules=impact.affected_modules,
        estimated_effort_hours=impact.estimated_effort_hours,
        estimated_cost_usd=impact.estimated_cost_usd,
        compliance_gap_count=impact.compliance_gap_count,
        recommendations=impact.recommendations,
        heatmap=impact.heatmap,
    )
