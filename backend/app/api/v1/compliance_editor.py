"""API endpoints for Compliance Editor."""


import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_editor import ComplianceEditorService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class CreateSessionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")


class OpenFileRequest(BaseModel):
    path: str = Field(..., description="File path to open")
    content: str = Field(..., description="File content")
    language: str = Field(default="python", description="Programming language")


class ApplyFixRequest(BaseModel):
    fix_id: str = Field(..., description="Fix identifier to apply")


class InlineFixSchema(BaseModel):
    id: str
    line: int
    description: str
    original: str
    replacement: str
    severity: str


class FileSchema(BaseModel):
    path: str
    language: str
    issues_count: int
    fixes_available: int


class EditorSessionSchema(BaseModel):
    id: str
    user_id: str
    files: list[FileSchema]
    status: str
    created_at: str | None


class EditorStatsSchema(BaseModel):
    total_sessions: int
    active_sessions: int
    total_fixes_applied: int
    total_issues_found: int


# --- Endpoints ---


@router.post("/sessions", response_model=EditorSessionSchema, status_code=status.HTTP_201_CREATED, summary="Create editor session")
async def create_session(request: CreateSessionRequest, db: DB) -> EditorSessionSchema:
    service = ComplianceEditorService(db=db)
    session = await service.create_session(user_id=request.user_id)
    logger.info("editor_session_created", user_id=request.user_id)
    return EditorSessionSchema(
        id=str(session.id), user_id=session.user_id,
        files=[
            FileSchema(path=f.path, language=f.language, issues_count=f.issues_count, fixes_available=f.fixes_available)
            for f in session.files
        ],
        status=session.status,
        created_at=session.created_at.isoformat() if session.created_at else None,
    )


@router.post("/sessions/{session_id}/files", response_model=FileSchema, status_code=status.HTTP_201_CREATED, summary="Open file in session")
async def open_file(session_id: str, request: OpenFileRequest, db: DB) -> FileSchema:
    service = ComplianceEditorService(db=db)
    f = await service.open_file(
        session_id=session_id,
        path=request.path,
        content=request.content,
        language=request.language,
    )
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    logger.info("file_opened", session_id=session_id, path=request.path)
    return FileSchema(
        path=f.path, language=f.language,
        issues_count=f.issues_count, fixes_available=f.fixes_available,
    )


@router.post("/sessions/{session_id}/files/{path:path}/fix", summary="Apply inline fix")
async def apply_fix(session_id: str, path: str, request: ApplyFixRequest, db: DB) -> dict:
    service = ComplianceEditorService(db=db)
    result = await service.apply_fix(
        session_id=session_id,
        path=path,
        fix_id=request.fix_id,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fix or session not found")
    logger.info("fix_applied", session_id=session_id, path=path, fix_id=request.fix_id)
    return {"status": "applied", "fix_id": request.fix_id, "path": path}


@router.get("/sessions/{session_id}/files/{path:path}/fixes", response_model=list[InlineFixSchema], summary="Get inline fixes")
async def get_inline_fixes(session_id: str, path: str, db: DB) -> list[InlineFixSchema]:
    service = ComplianceEditorService(db=db)
    fixes = await service.get_inline_fixes(session_id=session_id, path=path)
    return [
        InlineFixSchema(
            id=str(f.id), line=f.line, description=f.description,
            original=f.original, replacement=f.replacement, severity=f.severity,
        )
        for f in fixes
    ]


@router.get("/sessions/{session_id}", response_model=EditorSessionSchema, summary="Get editor session")
async def get_session(session_id: str, db: DB) -> EditorSessionSchema:
    service = ComplianceEditorService(db=db)
    session = await service.get_session(session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return EditorSessionSchema(
        id=str(session.id), user_id=session.user_id,
        files=[
            FileSchema(path=f.path, language=f.language, issues_count=f.issues_count, fixes_available=f.fixes_available)
            for f in session.files
        ],
        status=session.status,
        created_at=session.created_at.isoformat() if session.created_at else None,
    )


@router.delete("/sessions/{session_id}", summary="Close editor session")
async def close_session(session_id: str, db: DB) -> dict:
    service = ComplianceEditorService(db=db)
    ok = await service.close_session(session_id=session_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    logger.info("editor_session_closed", session_id=session_id)
    return {"status": "closed", "session_id": session_id}


@router.get("/stats", response_model=EditorStatsSchema, summary="Get editor stats")
async def get_stats(db: DB) -> EditorStatsSchema:
    service = ComplianceEditorService(db=db)
    s = await service.get_stats()
    return EditorStatsSchema(
        total_sessions=s.total_sessions,
        active_sessions=s.active_sessions,
        total_fixes_applied=s.total_fixes_applied,
        total_issues_found=s.total_issues_found,
    )
