"""API endpoints for Compliance Co-Pilot IDE Agent."""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.ide_agent import (
    AgentConfig,
    AgentSession,
    AgentStatus,
    AgentTriggerType,
    IDEAgentService,
    get_ide_agent_service,
)


logger = structlog.get_logger()
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class AnalyzeCodeRequest(BaseModel):
    """Request to analyze code for compliance violations."""

    code: str = Field(..., description="The code to analyze")
    file_path: str = Field(..., description="Path to the file being analyzed")
    language: str = Field(default="python", description="Programming language")
    regulations: list[str] | None = Field(
        default=None,
        description="List of regulations to check. If not provided, uses org defaults.",
    )
    trigger_type: str = Field(
        default="manual",
        description="What triggered this analysis",
    )
    auto_fix: bool = Field(
        default=False,
        description="Whether to automatically apply high-confidence fixes",
    )


class SessionResponse(BaseModel):
    """Response containing agent session details."""

    id: str
    organization_id: str | None
    user_id: str | None
    repository_id: str | None
    trigger_type: str
    status: str
    current_step: str
    progress: float
    violations_found: int
    fixes_applied: int
    pending_approval_count: int
    actions: list[dict[str, Any]]
    started_at: str
    completed_at: str | None
    error_message: str | None


class ViolationResponse(BaseModel):
    """Response containing a compliance violation."""

    id: str
    rule_id: str
    rule_name: str
    regulation: str
    article_reference: str | None
    severity: str
    message: str
    location: dict[str, Any] | None
    original_code: str
    confidence: float


class FixResponse(BaseModel):
    """Response containing a proposed fix."""

    id: str
    violation_id: str | None
    fixed_code: str
    explanation: str
    confidence: str
    confidence_score: float
    imports_to_add: list[str]
    breaking_changes: bool
    test_suggestions: list[str]


class RefactorPlanResponse(BaseModel):
    """Response containing a refactor plan."""

    id: str
    session_id: str | None
    total_violations: int
    fixable_violations: int
    manual_review_required: int
    changes_by_file: dict[str, list[dict[str, Any]]]
    changes_by_regulation: dict[str, list[dict[str, Any]]]
    execution_order: list[str]
    estimated_impact: str
    breaking_change_risk: bool
    diff_preview: str


class ConfigUpdateRequest(BaseModel):
    """Request to update agent configuration."""

    enabled_triggers: list[str] | None = None
    auto_fix_enabled: bool | None = None
    auto_fix_confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_fix_max_files: int | None = Field(default=None, ge=1, le=100)
    require_approval_for_refactor: bool | None = None
    require_approval_for_issues: bool | None = None
    require_approval_for_prs: bool | None = None
    enabled_regulations: list[str] | None = None
    excluded_paths: list[str] | None = None
    included_languages: list[str] | None = None
    notify_on_violations: bool | None = None
    notify_on_auto_fix: bool | None = None


class ConfigResponse(BaseModel):
    """Response containing agent configuration."""

    organization_id: str | None
    enabled_triggers: list[str]
    auto_fix_enabled: bool
    auto_fix_confidence_threshold: float
    auto_fix_max_files: int
    require_approval_for_refactor: bool
    require_approval_for_issues: bool
    require_approval_for_prs: bool
    enabled_regulations: list[str]
    excluded_paths: list[str]
    included_languages: list[str]
    notify_on_violations: bool
    notify_on_auto_fix: bool


class ApproveActionRequest(BaseModel):
    """Request to approve or reject an action."""

    action_id: str
    approved: bool = True
    reason: str | None = None


class BulkFixRequest(BaseModel):
    """Request to apply fixes in bulk."""

    session_id: str
    fix_ids: list[str] | None = Field(
        default=None,
        description="List of fix IDs to apply. If not provided, applies all pending fixes.",
    )
    dry_run: bool = Field(
        default=True,
        description="If true, simulates the fixes without applying them.",
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _session_to_response(session: AgentSession) -> SessionResponse:
    """Convert AgentSession to response model."""
    return SessionResponse(
        id=str(session.id),
        organization_id=str(session.organization_id) if session.organization_id else None,
        user_id=str(session.user_id) if session.user_id else None,
        repository_id=str(session.repository_id) if session.repository_id else None,
        trigger_type=session.trigger_type.value,
        status=session.status.value,
        current_step=session.current_step,
        progress=session.progress,
        violations_found=session.violations_found,
        fixes_applied=session.fixes_applied,
        pending_approval_count=session.pending_approval_count,
        actions=[a.to_dict() for a in session.actions],
        started_at=session.started_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        error_message=session.error_message,
    )


def _config_to_response(config: AgentConfig) -> ConfigResponse:
    """Convert AgentConfig to response model."""
    return ConfigResponse(
        organization_id=str(config.organization_id) if config.organization_id else None,
        enabled_triggers=[t.value for t in config.enabled_triggers],
        auto_fix_enabled=config.auto_fix_enabled,
        auto_fix_confidence_threshold=config.auto_fix_confidence_threshold,
        auto_fix_max_files=config.auto_fix_max_files,
        require_approval_for_refactor=config.require_approval_for_refactor,
        require_approval_for_issues=config.require_approval_for_issues,
        require_approval_for_prs=config.require_approval_for_prs,
        enabled_regulations=config.enabled_regulations,
        excluded_paths=config.excluded_paths,
        included_languages=config.included_languages,
        notify_on_violations=config.notify_on_violations,
        notify_on_auto_fix=config.notify_on_auto_fix,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/analyze", response_model=SessionResponse)
async def analyze_code(
    request: AnalyzeCodeRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SessionResponse:
    """Analyze code for compliance violations and generate fixes.

    This endpoint starts a full agent session that:
    1. Analyzes code for compliance violations
    2. Generates proposed fixes for each violation
    3. Creates a refactor plan
    4. Optionally auto-applies high-confidence fixes

    The session can be monitored and actions can be approved/rejected.
    """
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    try:
        trigger_type = AgentTriggerType(request.trigger_type)
    except ValueError:
        trigger_type = AgentTriggerType.MANUAL

    session = await service.run_full_analysis(
        code=request.code,
        file_path=request.file_path,
        language=request.language,
        trigger_type=trigger_type,
        user_id=member.user_id,
        auto_fix=request.auto_fix,
    )

    return _session_to_response(session)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
) -> list[SessionResponse]:
    """List agent sessions for the organization."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    agent_status = None
    if status_filter:
        try:
            agent_status = AgentStatus(status_filter)
        except ValueError:
            pass

    sessions = service.list_sessions(status=agent_status, limit=limit)
    return [_session_to_response(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SessionResponse:
    """Get details of a specific agent session."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    try:
        uuid_session_id = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    session = service.get_session(uuid_session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return _session_to_response(session)


@router.post("/sessions/{session_id}/approve")
async def approve_action(
    session_id: str,
    request: ApproveActionRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Approve or reject a pending action in a session."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    try:
        uuid_session_id = UUID(session_id)
        uuid_action_id = UUID(request.action_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )

    if request.approved:
        action = await service.approve_action(uuid_session_id, uuid_action_id)
    else:
        action = await service.reject_action(
            uuid_session_id,
            uuid_action_id,
            reason=request.reason or "",
        )

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found or already processed",
        )

    return {
        "action_id": str(action.id),
        "approved": request.approved,
        "executed": action.executed,
    }


@router.post("/sessions/{session_id}/cancel")
async def cancel_session(
    session_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Cancel an active agent session."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    try:
        uuid_session_id = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    session = service.cancel_session(uuid_session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already completed",
        )

    return {
        "session_id": str(session.id),
        "status": session.status.value,
        "cancelled": True,
    }


@router.post("/bulk-fix")
async def apply_bulk_fixes(
    request: BulkFixRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Apply multiple fixes from a session.

    Can be run as a dry-run to preview changes, or applied directly.
    """
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    try:
        uuid_session_id = UUID(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    session = service.get_session(uuid_session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Collect all proposed fixes from session actions
    all_fixes = []
    for action in session.actions:
        all_fixes.extend(action.proposed_fixes)

    # Filter by fix IDs if provided
    if request.fix_ids:
        fix_id_set = set(request.fix_ids)
        all_fixes = [f for f in all_fixes if str(f.id) in fix_id_set]

    if not all_fixes:
        return {
            "session_id": str(session.id),
            "fixes_applied": 0,
            "message": "No fixes to apply",
        }

    result = await service.apply_fixes(
        session=session,
        fixes=all_fixes,
        dry_run=request.dry_run,
    )

    return {
        "session_id": str(session.id),
        **result,
    }


# ============================================================================
# Configuration Endpoints
# ============================================================================


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ConfigResponse:
    """Get IDE agent configuration for the organization."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)
    config = service.get_config(organization.id)
    return _config_to_response(config)


@router.put("/config", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ConfigResponse:
    """Update IDE agent configuration for the organization."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    config = service.update_config(organization.id, updates)

    return _config_to_response(config)


# ============================================================================
# Quick Actions Endpoints
# ============================================================================


@router.post("/quick-analyze")
async def quick_analyze(
    code: str,
    language: str = "python",
    regulations: list[str] | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Quick code analysis without creating a full session.

    Returns violations only, without generating fixes.
    Useful for real-time IDE integration.
    """
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    session = await service.start_session(
        trigger_type=AgentTriggerType.MANUAL,
        trigger_context={"quick_analyze": True},
        user_id=member.user_id,
    )

    violations = await service.analyze_code(
        session=session,
        code=code,
        file_path="<inline>",
        language=language,
        regulations=regulations,
    )

    return {
        "violations": [v.to_dict() for v in violations],
        "count": len(violations),
        "analyzed_at": datetime.now(UTC).isoformat(),
    }


@router.post("/suggest-fix")
async def suggest_single_fix(
    code: str,
    violation_rule_id: str,
    violation_message: str,
    regulation: str,
    language: str = "python",
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> dict[str, Any]:
    """Get a fix suggestion for a specific violation.

    Useful for IDE quick-fix actions.
    """
    from app.services.ide_agent.models import ComplianceViolation

    service = get_ide_agent_service(db=db, organization_id=organization.id)

    session = await service.start_session(
        trigger_type=AgentTriggerType.MANUAL,
        trigger_context={"suggest_fix": True},
        user_id=member.user_id,
    )

    # Create a violation object
    violation = ComplianceViolation(
        rule_id=violation_rule_id,
        rule_name=violation_rule_id,
        regulation=regulation,
        message=violation_message,
        original_code=code,
        confidence=0.8,
    )

    fixes = await service.generate_fixes(
        session=session,
        violations=[violation],
        code=code,
        language=language,
    )

    if not fixes:
        return {
            "fix": None,
            "message": "Could not generate a fix for this violation",
        }

    return {
        "fix": fixes[0].to_dict(),
        "generated_at": datetime.now(UTC).isoformat(),
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get("/stats")
async def get_agent_stats(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    days: int = Query(30, ge=1, le=365),
) -> dict[str, Any]:
    """Get statistics for the IDE agent."""
    service = get_ide_agent_service(db=db, organization_id=organization.id)

    sessions = service.list_sessions(limit=1000)

    # Calculate stats
    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.status == AgentStatus.COMPLETED)
    total_violations = sum(s.violations_found for s in sessions)
    total_fixes = sum(s.fixes_applied for s in sessions)

    # Status breakdown
    status_counts = {}
    for s in sessions:
        status_counts[s.status.value] = status_counts.get(s.status.value, 0) + 1

    # Trigger breakdown
    trigger_counts = {}
    for s in sessions:
        trigger_counts[s.trigger_type.value] = trigger_counts.get(s.trigger_type.value, 0) + 1

    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "completion_rate": completed_sessions / total_sessions if total_sessions > 0 else 0,
        "total_violations_found": total_violations,
        "total_fixes_applied": total_fixes,
        "fix_rate": total_fixes / total_violations if total_violations > 0 else 0,
        "by_status": status_counts,
        "by_trigger": trigger_counts,
    }


# ============================================================================
# WebSocket Streaming Endpoint
# ============================================================================


class WebSocketConnectionManager:
    """Manages WebSocket connections for streaming IDE agent updates."""

    def __init__(self):
        # Map of session_id -> list of connected WebSocket clients
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept a new WebSocket connection and add to session's clients."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove a WebSocket connection from the session's clients."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")

    async def broadcast_to_session(self, session_id: str, message: dict) -> None:
        """Broadcast a message to all clients connected to a session."""
        if session_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(websocket)
            # Clean up disconnected clients
            for ws in disconnected:
                self.disconnect(ws, session_id)


# Global connection manager
ws_manager = WebSocketConnectionManager()


@router.websocket("/stream/{session_id}")
async def stream_session(
    websocket: WebSocket,
    session_id: str,
    db: DB,
):
    """WebSocket endpoint for streaming IDE agent session updates.

    Provides real-time updates on:
    - Session progress and status changes
    - Violations as they are detected
    - Fix suggestions as they are generated
    - Action approvals and executions

    Messages sent to client:
    - {"type": "connected", "session_id": "..."}
    - {"type": "progress", "status": "...", "step": "...", "progress": 0.0}
    - {"type": "violation", "violation": {...}}
    - {"type": "fix", "fix": {...}}
    - {"type": "action", "action": {...}}
    - {"type": "completed", "session": {...}}
    - {"type": "error", "message": "..."}

    Messages from client:
    - {"action": "approve", "action_id": "..."}
    - {"action": "reject", "action_id": "...", "reason": "..."}
    - {"action": "cancel"}
    - {"action": "subscribe"}
    """
    await ws_manager.connect(websocket, session_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Get initial session state if it exists
        from app.core.database import get_db_context

        async with get_db_context() as session_db:
            from sqlalchemy import select
            from app.models.ide_agent import IDEAgentSession

            result = await session_db.execute(
                select(IDEAgentSession).where(IDEAgentSession.id == UUID(session_id))
            )
            session = result.scalar_one_or_none()

            if session:
                await websocket.send_json({
                    "type": "progress",
                    "status": session.status.value if hasattr(session.status, 'value') else session.status,
                    "step": session.current_step,
                    "progress": session.progress,
                    "violations_found": session.violations_found,
                    "fixes_applied": session.fixes_applied,
                    "pending_approval_count": session.pending_approval_count,
                })

        # Listen for client messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0,  # Heartbeat timeout
                )
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                continue

            action = data.get("action")

            if action == "subscribe":
                # Client is subscribing to updates
                await websocket.send_json({
                    "type": "subscribed",
                    "session_id": session_id,
                })

            elif action == "approve":
                # Approve an action
                action_id = data.get("action_id")
                if action_id:
                    async with get_db_context() as action_db:
                        from app.models.ide_agent import IDEAgentAction

                        result = await action_db.execute(
                            select(IDEAgentAction).where(
                                IDEAgentAction.id == UUID(action_id)
                            )
                        )
                        action_obj = result.scalar_one_or_none()

                        if action_obj:
                            action_obj.approved = True
                            action_obj.approved_at = datetime.now(UTC)
                            await action_db.commit()

                            await ws_manager.broadcast_to_session(session_id, {
                                "type": "action_approved",
                                "action_id": action_id,
                                "timestamp": datetime.now(UTC).isoformat(),
                            })

            elif action == "reject":
                # Reject an action
                action_id = data.get("action_id")
                reason = data.get("reason", "")
                if action_id:
                    async with get_db_context() as action_db:
                        from app.models.ide_agent import IDEAgentAction

                        result = await action_db.execute(
                            select(IDEAgentAction).where(
                                IDEAgentAction.id == UUID(action_id)
                            )
                        )
                        action_obj = result.scalar_one_or_none()

                        if action_obj:
                            action_obj.approved = False
                            action_obj.rejection_reason = reason
                            await action_db.commit()

                            await ws_manager.broadcast_to_session(session_id, {
                                "type": "action_rejected",
                                "action_id": action_id,
                                "reason": reason,
                                "timestamp": datetime.now(UTC).isoformat(),
                            })

            elif action == "cancel":
                # Cancel the session
                async with get_db_context() as cancel_db:
                    from app.models.ide_agent import IDEAgentSession, AgentStatus as DBAgentStatus

                    result = await cancel_db.execute(
                        select(IDEAgentSession).where(
                            IDEAgentSession.id == UUID(session_id)
                        )
                    )
                    session = result.scalar_one_or_none()

                    if session:
                        session.status = DBAgentStatus.CANCELLED
                        session.completed_at = datetime.now(UTC)
                        await cancel_db.commit()

                        await ws_manager.broadcast_to_session(session_id, {
                            "type": "cancelled",
                            "session_id": session_id,
                            "timestamp": datetime.now(UTC).isoformat(),
                        })

            elif action == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(UTC).isoformat(),
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, session_id)


# ============================================================================
# Streaming Helper Functions
# ============================================================================


async def stream_progress_update(
    session_id: str,
    status: str,
    step: str,
    progress: float,
    violations_found: int = 0,
    fixes_applied: int = 0,
) -> None:
    """Stream a progress update to all connected clients."""
    await ws_manager.broadcast_to_session(str(session_id), {
        "type": "progress",
        "status": status,
        "step": step,
        "progress": progress,
        "violations_found": violations_found,
        "fixes_applied": fixes_applied,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def stream_violation(session_id: str, violation: dict) -> None:
    """Stream a detected violation to all connected clients."""
    await ws_manager.broadcast_to_session(str(session_id), {
        "type": "violation",
        "violation": violation,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def stream_fix(session_id: str, fix: dict) -> None:
    """Stream a generated fix to all connected clients."""
    await ws_manager.broadcast_to_session(str(session_id), {
        "type": "fix",
        "fix": fix,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def stream_action(session_id: str, action: dict) -> None:
    """Stream an action update to all connected clients."""
    await ws_manager.broadcast_to_session(str(session_id), {
        "type": "action",
        "action": action,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def stream_completion(session_id: str, session: dict) -> None:
    """Stream session completion to all connected clients."""
    await ws_manager.broadcast_to_session(str(session_id), {
        "type": "completed",
        "session": session,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def stream_error(session_id: str, message: str) -> None:
    """Stream an error to all connected clients."""
    await ws_manager.broadcast_to_session(str(session_id), {
        "type": "error",
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
    })


# ============================================================================
# RAG Search Endpoints
# ============================================================================


class RAGSearchRequest(BaseModel):
    """Request to search regulations using RAG."""

    query: str = Field(..., description="Search query for regulations")
    regulations: list[str] | None = Field(default=None, description="Filter by regulation names")
    top_k: int = Field(default=5, ge=1, le=20, description="Max results to return")


class RAGSearchResultSchema(BaseModel):
    """Response containing a RAG search result."""

    regulation: str
    article: str
    text: str
    relevance_score: float
    metadata: dict[str, Any] = {}


@router.post("/rag-search", response_model=list[RAGSearchResultSchema])
async def search_regulations(
    request: RAGSearchRequest,
    db: DB,
) -> list[RAGSearchResultSchema]:
    """Search regulation corpus using RAG for context-aware compliance assistance."""
    from uuid import uuid4

    service = IDEAgentService(db=db, organization_id=uuid4())
    results = await service.search_regulations(
        query=request.query,
        regulations=request.regulations,
        top_k=request.top_k,
    )
    return [RAGSearchResultSchema(**r.to_dict()) for r in results]


# ============================================================================
# Feedback Learning Loop Endpoints
# ============================================================================


class FeedbackRequest(BaseModel):
    """Request to submit feedback on a suggestion."""

    session_id: str | None = None
    violation_id: str | None = None
    fix_id: str | None = None
    rating: str = Field(..., description="helpful, not_helpful, incorrect, partially_helpful")
    comment: str = ""
    was_applied: bool = False


class FeedbackResponseSchema(BaseModel):
    """Response containing submitted feedback."""

    id: str
    rating: str
    comment: str
    was_applied: bool
    submitted_at: str


class FeedbackStatsSchema(BaseModel):
    """Response containing aggregated feedback statistics."""

    total_feedback: int
    helpful_count: int
    not_helpful_count: int
    incorrect_count: int
    application_rate: float
    top_appreciated_rules: list[str]
    top_rejected_rules: list[str]


@router.post("/feedback", response_model=FeedbackResponseSchema, status_code=201)
async def submit_feedback(
    request: FeedbackRequest,
    db: DB,
) -> FeedbackResponseSchema:
    """Submit feedback on an IDE copilot suggestion to improve future recommendations."""
    from uuid import uuid4

    service = IDEAgentService(db=db, organization_id=uuid4())
    feedback = service.submit_feedback(
        session_id=UUID(request.session_id) if request.session_id else None,
        violation_id=UUID(request.violation_id) if request.violation_id else None,
        fix_id=UUID(request.fix_id) if request.fix_id else None,
        rating=request.rating,
        comment=request.comment,
        was_applied=request.was_applied,
    )
    return FeedbackResponseSchema(
        id=str(feedback.id),
        rating=feedback.rating.value,
        comment=feedback.comment,
        was_applied=feedback.was_applied,
        submitted_at=feedback.submitted_at.isoformat(),
    )


@router.get("/feedback/stats", response_model=FeedbackStatsSchema)
async def get_feedback_stats(db: DB) -> FeedbackStatsSchema:
    """Get aggregated feedback statistics for the IDE copilot."""
    from uuid import uuid4

    service = IDEAgentService(db=db, organization_id=uuid4())
    stats = service.get_feedback_stats()
    return FeedbackStatsSchema(**stats.to_dict())
