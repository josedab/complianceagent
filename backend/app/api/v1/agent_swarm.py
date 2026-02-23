"""API endpoints for Agent Swarm orchestration."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.agent_swarm import AgentSwarmService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class LaunchSwarmRequest(BaseModel):
    repo: str = Field(..., description="Repository to analyze")
    frameworks: list[str] = Field(..., description="Compliance frameworks to apply")
    files: list[str] = Field(default_factory=list, description="Specific files to target")


class AgentSchema(BaseModel):
    id: str
    role: str
    status: str
    findings_count: int


class SwarmSessionSchema(BaseModel):
    id: str
    repo: str
    frameworks: list[str]
    files: list[str]
    status: str
    agents: list[AgentSchema]
    findings: list[dict[str, Any]]
    created_at: str | None


class SwarmStatsSchema(BaseModel):
    total_sessions: int
    active_sessions: int
    total_findings: int
    agents_deployed: int


# --- Endpoints ---


@router.post("/sessions", response_model=SwarmSessionSchema, status_code=status.HTTP_201_CREATED, summary="Launch agent swarm")
async def launch_swarm(request: LaunchSwarmRequest, db: DB) -> SwarmSessionSchema:
    service = AgentSwarmService(db=db)
    session = await service.launch_swarm(
        repo=request.repo,
        frameworks=request.frameworks,
        files=request.files,
    )
    logger.info("swarm_launched", repo=request.repo, frameworks=request.frameworks)
    return SwarmSessionSchema(
        id=str(session.id), repo=session.repo, frameworks=session.frameworks,
        files=session.files, status=session.status,
        agents=[
            AgentSchema(id=str(a.id), role=a.role, status=a.status, findings_count=a.findings_count)
            for a in session.agents
        ],
        findings=session.findings,
        created_at=session.created_at.isoformat() if session.created_at else None,
    )


@router.get("/sessions", response_model=list[SwarmSessionSchema], summary="List swarm sessions")
async def list_sessions(db: DB) -> list[SwarmSessionSchema]:
    service = AgentSwarmService(db=db)
    sessions = await service.list_sessions()
    return [
        SwarmSessionSchema(
            id=str(s.id), repo=s.repo, frameworks=s.frameworks,
            files=s.files, status=s.status,
            agents=[
                AgentSchema(id=str(a.id), role=a.role, status=a.status, findings_count=a.findings_count)
                for a in s.agents
            ],
            findings=s.findings,
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SwarmSessionSchema, summary="Get swarm session")
async def get_session(session_id: str, db: DB) -> SwarmSessionSchema:
    service = AgentSwarmService(db=db)
    session = await service.get_session(session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SwarmSessionSchema(
        id=str(session.id), repo=session.repo, frameworks=session.frameworks,
        files=session.files, status=session.status,
        agents=[
            AgentSchema(id=str(a.id), role=a.role, status=a.status, findings_count=a.findings_count)
            for a in session.agents
        ],
        findings=session.findings,
        created_at=session.created_at.isoformat() if session.created_at else None,
    )


@router.get("/stats", response_model=SwarmStatsSchema, summary="Get swarm stats")
async def get_stats(db: DB) -> SwarmStatsSchema:
    service = AgentSwarmService(db=db)
    s = await service.get_stats()
    return SwarmStatsSchema(
        total_sessions=s.total_sessions,
        active_sessions=s.active_sessions,
        total_findings=s.total_findings,
        agents_deployed=s.agents_deployed,
    )
