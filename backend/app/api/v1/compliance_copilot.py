"""API endpoints for AI Compliance Co-Pilot."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_copilot import ComplianceCopilotService, ViolationSeverity


logger = structlog.get_logger()
router = APIRouter()


class StartSessionRequest(BaseModel):
    repo: str = Field(...)
    user_id: str = Field(default="")

class SessionSchema(BaseModel):
    id: str
    repo: str
    user_id: str
    violations_found: int
    fixes_proposed: int
    fixes_accepted: int
    started_at: str | None

class AnalyzeRequest(BaseModel):
    repo: str = Field(...)
    frameworks: list[str] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)

class ViolationSchema(BaseModel):
    id: str
    file_path: str
    line_start: int
    line_end: int
    rule_id: str
    framework: str
    article_ref: str
    severity: str
    message: str

class AnalysisResultSchema(BaseModel):
    repo: str
    total_files: int
    files_analyzed: int
    violations: list[ViolationSchema]
    score: float
    frameworks_checked: list[str]

class FixSchema(BaseModel):
    id: str
    violation_id: str
    file_path: str
    original_code: str
    fixed_code: str
    explanation: str
    article_reference: str
    confidence: float
    status: str

class ExplainRequest(BaseModel):
    regulation: str = Field(...)
    article: str = Field(default="")

class ExplanationSchema(BaseModel):
    regulation: str
    article: str
    plain_language: str
    technical_implications: list[str]
    code_examples: list[dict[str, str]]
    related_articles: list[str]


@router.post("/sessions", response_model=SessionSchema, status_code=status.HTTP_201_CREATED, summary="Start copilot session")
async def start_session(request: StartSessionRequest, db: DB) -> SessionSchema:
    service = ComplianceCopilotService(db=db)
    session = await service.start_session(repo=request.repo, user_id=request.user_id)
    return SessionSchema(
        id=str(session.id), repo=session.repo, user_id=session.user_id,
        violations_found=session.violations_found, fixes_proposed=session.fixes_proposed,
        fixes_accepted=session.fixes_accepted,
        started_at=session.started_at.isoformat() if session.started_at else None,
    )

@router.post("/analyze", response_model=AnalysisResultSchema, summary="Analyze codebase")
async def analyze_codebase(request: AnalyzeRequest, db: DB) -> AnalysisResultSchema:
    service = ComplianceCopilotService(db=db)
    analysis = await service.analyze_codebase(
        repo=request.repo, frameworks=request.frameworks or None, file_paths=request.file_paths or None,
    )
    return AnalysisResultSchema(
        repo=analysis.repo, total_files=analysis.total_files, files_analyzed=analysis.files_analyzed,
        violations=[
            ViolationSchema(
                id=str(v.id), file_path=v.file_path, line_start=v.line_start, line_end=v.line_end,
                rule_id=v.rule_id, framework=v.framework, article_ref=v.article_ref,
                severity=v.severity.value, message=v.message,
            ) for v in analysis.violations
        ],
        score=analysis.score, frameworks_checked=analysis.frameworks_checked,
    )

@router.post("/violations/{violation_id}/fix", response_model=FixSchema, summary="Propose fix")
async def propose_fix(violation_id: UUID, db: DB) -> FixSchema:
    service = ComplianceCopilotService(db=db)
    fix = await service.propose_fix(violation_id)
    return FixSchema(
        id=str(fix.id), violation_id=str(fix.violation_id), file_path=fix.file_path,
        original_code=fix.original_code, fixed_code=fix.fixed_code,
        explanation=fix.explanation, article_reference=fix.article_reference,
        confidence=fix.confidence, status=fix.status.value,
    )

@router.post("/fixes/{fix_id}/accept", summary="Accept fix")
async def accept_fix(fix_id: UUID, db: DB) -> dict:
    service = ComplianceCopilotService(db=db)
    fix = await service.accept_fix(fix_id)
    if not fix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fix not found")
    return {"status": "accepted", "fix_id": str(fix_id)}

@router.post("/fixes/{fix_id}/reject", summary="Reject fix")
async def reject_fix(fix_id: UUID, db: DB) -> dict:
    service = ComplianceCopilotService(db=db)
    fix = await service.reject_fix(fix_id)
    if not fix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fix not found")
    return {"status": "rejected", "fix_id": str(fix_id)}

@router.post("/explain", response_model=ExplanationSchema, summary="Explain regulation")
async def explain_regulation(request: ExplainRequest, db: DB) -> ExplanationSchema:
    service = ComplianceCopilotService(db=db)
    explanation = await service.explain_regulation(regulation=request.regulation, article=request.article)
    return ExplanationSchema(
        regulation=explanation.regulation, article=explanation.article,
        plain_language=explanation.plain_language,
        technical_implications=explanation.technical_implications,
        code_examples=explanation.code_examples, related_articles=explanation.related_articles,
    )

@router.get("/violations", response_model=list[ViolationSchema], summary="List violations")
async def list_violations(db: DB, framework: str | None = None, severity: str | None = None, limit: int = 50) -> list[ViolationSchema]:
    service = ComplianceCopilotService(db=db)
    s = ViolationSeverity(severity) if severity else None
    violations = service.list_violations(framework=framework, severity=s, limit=limit)
    return [
        ViolationSchema(
            id=str(v.id), file_path=v.file_path, line_start=v.line_start, line_end=v.line_end,
            rule_id=v.rule_id, framework=v.framework, article_ref=v.article_ref,
            severity=v.severity.value, message=v.message,
        ) for v in violations
    ]
