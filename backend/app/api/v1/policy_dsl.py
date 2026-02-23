"""API endpoints for Compliance-as-Code Policy Language."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.policy_dsl import PolicyDSLService, PolicyStatus


logger = structlog.get_logger()
router = APIRouter()


class CreatePolicyRequest(BaseModel):
    name: str = Field(...)
    slug: str = Field(...)
    dsl_source: str = Field(...)
    framework: str = Field(default="")
    severity: str = Field(default="medium")
    author: str = Field(default="")


class PolicySchema(BaseModel):
    id: str
    name: str
    slug: str
    framework: str
    severity: str
    status: str
    dsl_source: str
    conditions: list[dict[str, Any]]
    actions: list[dict[str, Any]]


class CompileRequest(BaseModel):
    slug: str = Field(...)
    output_format: str = Field(...)


class CompileResultSchema(BaseModel):
    output_format: str
    compiled_code: str
    errors: list[str]
    warnings: list[str]


class ValidationSchema(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    parsed_conditions: int
    parsed_actions: int


class DSLStatsSchema(BaseModel):
    total_policies: int
    active_policies: int
    by_framework: dict[str, int]
    by_severity: dict[str, int]
    compilations: dict[str, int]


@router.post("/policies", response_model=PolicySchema, status_code=status.HTTP_201_CREATED, summary="Create policy")
async def create_policy(request: CreatePolicyRequest, db: DB) -> PolicySchema:
    service = PolicyDSLService(db=db)
    try:
        p = await service.create_policy(name=request.name, slug=request.slug, dsl_source=request.dsl_source, framework=request.framework, severity=request.severity, author=request.author)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return PolicySchema(id=str(p.id), name=p.name, slug=p.slug, framework=p.framework, severity=p.severity.value, status=p.status.value, dsl_source=p.dsl_source, conditions=p.conditions, actions=p.actions)


@router.get("/policies", response_model=list[PolicySchema], summary="List policies")
async def list_policies(db: DB, framework: str | None = None, policy_status: str | None = None) -> list[PolicySchema]:
    service = PolicyDSLService(db=db)
    s = PolicyStatus(policy_status) if policy_status else None
    policies = service.list_policies(framework=framework, status=s)
    return [PolicySchema(id=str(p.id), name=p.name, slug=p.slug, framework=p.framework, severity=p.severity.value, status=p.status.value, dsl_source=p.dsl_source, conditions=p.conditions, actions=p.actions) for p in policies]


@router.post("/compile", response_model=CompileResultSchema, summary="Compile policy")
async def compile_policy(request: CompileRequest, db: DB) -> CompileResultSchema:
    service = PolicyDSLService(db=db)
    c = await service.compile_policy(slug=request.slug, output_format=request.output_format)
    return CompileResultSchema(output_format=c.output_format.value, compiled_code=c.compiled_code, errors=c.errors, warnings=c.warnings)


@router.post("/validate", response_model=ValidationSchema, summary="Validate DSL")
async def validate_dsl(dsl_source: str, db: DB) -> ValidationSchema:
    service = PolicyDSLService(db=db)
    v = service.validate_dsl(dsl_source)
    return ValidationSchema(valid=v.valid, errors=v.errors, warnings=v.warnings, parsed_conditions=v.parsed_conditions, parsed_actions=v.parsed_actions)


@router.get("/stats", response_model=DSLStatsSchema, summary="Get DSL stats")
async def get_stats(db: DB) -> DSLStatsSchema:
    service = PolicyDSLService(db=db)
    s = service.get_stats()
    return DSLStatsSchema(total_policies=s.total_policies, active_policies=s.active_policies, by_framework=s.by_framework, by_severity=s.by_severity, compilations=s.compilations)
