"""API endpoints for Compliance-as-Code Policy SDK."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.policy_sdk import PolicySDKService, PolicyCategory, PolicyLanguage, PolicySeverity

logger = structlog.get_logger()
router = APIRouter()


class CreatePolicyRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    source_code: str = Field(..., min_length=1)
    language: str = Field(default="yaml")
    category: str = Field(default="custom")
    severity: str = Field(default="medium")
    frameworks: list[str] = Field(default_factory=list)
    author: str = Field(default="")


class PublishRequest(BaseModel):
    publisher: str = Field(...)


class PolicySchema(BaseModel):
    id: str
    name: str
    description: str
    version: str
    language: str
    category: str
    severity: str
    frameworks: list[str]
    is_community: bool
    author: str


class ValidationSchema(BaseModel):
    policy_id: str
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    coverage: float


@router.get("/policies", response_model=list[PolicySchema], summary="List policies")
async def list_policies(db: DB, copilot: CopilotDep, category: str | None = None, framework: str | None = None) -> list[PolicySchema]:
    service = PolicySDKService(db=db, copilot_client=copilot)
    cat = PolicyCategory(category) if category and category in [c.value for c in PolicyCategory] else None
    policies = await service.list_policies(category=cat, framework=framework)
    return [PolicySchema(
        id=str(p.id), name=p.name, description=p.description, version=p.version,
        language=p.language.value, category=p.category.value, severity=p.severity.value,
        frameworks=p.frameworks, is_community=p.is_community, author=p.author,
    ) for p in policies]


@router.post("/policies", response_model=PolicySchema, status_code=status.HTTP_201_CREATED, summary="Create policy")
async def create_policy(request: CreatePolicyRequest, db: DB, copilot: CopilotDep) -> PolicySchema:
    service = PolicySDKService(db=db, copilot_client=copilot)
    lang = PolicyLanguage(request.language) if request.language in [l.value for l in PolicyLanguage] else PolicyLanguage.YAML
    cat = PolicyCategory(request.category) if request.category in [c.value for c in PolicyCategory] else PolicyCategory.CUSTOM
    sev = PolicySeverity(request.severity) if request.severity in [s.value for s in PolicySeverity] else PolicySeverity.MEDIUM
    policy = await service.create_policy(
        name=request.name, description=request.description, source_code=request.source_code,
        language=lang, category=cat, severity=sev, frameworks=request.frameworks, author=request.author,
    )
    return PolicySchema(
        id=str(policy.id), name=policy.name, description=policy.description, version=policy.version,
        language=policy.language.value, category=policy.category.value, severity=policy.severity.value,
        frameworks=policy.frameworks, is_community=policy.is_community, author=policy.author,
    )


@router.post("/policies/{policy_id}/validate", response_model=ValidationSchema, summary="Validate policy")
async def validate_policy(policy_id: str, db: DB, copilot: CopilotDep) -> ValidationSchema:
    service = PolicySDKService(db=db, copilot_client=copilot)
    result = await service.validate_policy(UUID(policy_id))
    return ValidationSchema(
        policy_id=str(result.policy_id), is_valid=result.is_valid,
        errors=result.errors, warnings=result.warnings, coverage=result.coverage,
    )


@router.post("/policies/{policy_id}/publish", summary="Publish policy to marketplace")
async def publish_policy(policy_id: str, request: PublishRequest, db: DB, copilot: CopilotDep) -> dict:
    service = PolicySDKService(db=db, copilot_client=copilot)
    entry = await service.publish_to_marketplace(UUID(policy_id), request.publisher)
    if not entry:
        raise HTTPException(status_code=400, detail="Policy not found or validation failed")
    return {"id": str(entry.id), "published": True, "publisher": entry.publisher}


@router.get("/marketplace", summary="Search policy marketplace")
async def search_marketplace(db: DB, copilot: CopilotDep, query: str | None = None,
                              category: str | None = None, framework: str | None = None) -> list[dict]:
    service = PolicySDKService(db=db, copilot_client=copilot)
    cat = PolicyCategory(category) if category and category in [c.value for c in PolicyCategory] else None
    entries = await service.search_marketplace(query=query, category=cat, framework=framework)
    return [{"id": str(e.id), "name": e.policy.name, "publisher": e.publisher,
             "installs": e.installs, "stars": e.stars, "verified": e.verified} for e in entries]


@router.get("/sdks", summary="List available SDK packages")
async def list_sdks(db: DB, copilot: CopilotDep) -> list[dict]:
    service = PolicySDKService(db=db, copilot_client=copilot)
    return await service.get_sdk_info()
