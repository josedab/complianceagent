"""API endpoints for Real-Time Compliance Pair Programming."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.pair_programming import PairProgrammingService


logger = structlog.get_logger()
router = APIRouter()


# --- Request/Response Models ---

SUPPORTED_LANGUAGES = {"python", "java", "javascript", "typescript", "go", "rust", "csharp", "ruby", "kotlin", "swift"}


class AnalyzeCodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000, description="Code to analyze")
    file_path: str = Field(..., min_length=1, max_length=1000, description="File path for context")
    language: str = Field("python", min_length=1, description="Programming language")


class SuggestionSchema(BaseModel):
    id: str
    file_path: str
    line_number: int
    severity: str
    rule_id: str
    regulation: str
    article: str
    message: str
    explanation: str
    suggested_fix: str
    original_code: str
    confidence: float


class SessionSchema(BaseModel):
    id: str
    repository: str
    language: str
    started_at: str


class RegulationContextSchema(BaseModel):
    regulation: str
    article: str
    title: str
    summary: str
    relevance_score: float
    applicable_patterns: list[str]


# --- Endpoints ---

@router.post("/analyze", response_model=list[SuggestionSchema])
async def analyze_code(req: AnalyzeCodeRequest) -> list[dict]:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail=f"Unsupported language: {req.language}. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}")
    svc = PairProgrammingService()
    suggestions = await svc.analyze_code(req.code, req.file_path, req.language)
    return [
        {"id": str(s.id), "file_path": s.file_path, "line_number": s.line_number,
         "severity": s.severity.value, "rule_id": s.rule_id, "regulation": s.regulation,
         "article": s.article, "message": s.message, "explanation": s.explanation,
         "suggested_fix": s.suggested_fix, "original_code": s.original_code,
         "confidence": s.confidence}
        for s in suggestions
    ]


@router.post("/session", response_model=SessionSchema)
async def start_session(
    repository: str = Query(...),
    language: str = Query("python"),
) -> dict:
    svc = PairProgrammingService()
    from uuid import uuid4
    session = await svc.start_session(uuid4(), repository, language)
    return {"id": str(session.id), "repository": session.repository,
            "language": session.language, "started_at": session.started_at.isoformat()}


@router.get("/context/{language}", response_model=list[RegulationContextSchema])
async def get_regulation_context(language: str) -> list[dict]:
    svc = PairProgrammingService()
    contexts = await svc.get_regulation_context(language)
    return [
        {"regulation": c.regulation, "article": c.article, "title": c.title,
         "summary": c.summary, "relevance_score": c.relevance_score,
         "applicable_patterns": c.applicable_patterns}
        for c in contexts
    ]


@router.get("/rules")
async def get_compliance_rules() -> list[dict]:
    svc = PairProgrammingService()
    return await svc.get_compliance_rules()


# --- Multi-File & Refactoring Models ---

class FileInput(BaseModel):
    file_path: str = Field(..., min_length=1, max_length=1000, description="File path")
    code: str = Field(..., min_length=1, max_length=100000, description="File content")


class MultiFileAnalyzeRequest(BaseModel):
    files: list[FileInput] = Field(..., min_length=1, max_length=50, description="Files to analyze")
    language: str = Field("python", min_length=1, description="Programming language")


class MultiFileAnalysisSchema(BaseModel):
    files_analyzed: int
    total_suggestions: int
    suggestions_by_file: dict[str, list[SuggestionSchema]]
    cross_file_issues: list[dict]
    refactoring_opportunities: list[dict]


class SessionSummarySchema(BaseModel):
    session_id: str
    repository: str
    language: str
    started_at: str
    last_activity: str
    suggestions_given: int
    suggestions_accepted: int
    suggestions_dismissed: int
    suggestions_pending: int
    violations_prevented: int
    acceptance_rate: float


class SuggestionActionSchema(BaseModel):
    id: str
    status: str
    file_path: str
    rule_id: str
    message: str


class RefactoringRequest(BaseModel):
    files: list[FileInput] = Field(..., min_length=1, max_length=50, description="Files to analyze")
    language: str = Field("python", min_length=1, description="Programming language")


class RefactoringSuggestionSchema(BaseModel):
    id: str
    title: str
    description: str
    affected_files: list[str]
    regulation: str
    article: str
    effort_estimate: str
    priority: int
    suggested_approach: str


# --- New Endpoints ---

@router.post("/analyze/multi-file", response_model=MultiFileAnalysisSchema)
async def analyze_multi_file(req: MultiFileAnalyzeRequest) -> dict:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail=f"Unsupported language: {req.language}. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}")
    svc = PairProgrammingService()
    result = await svc.analyze_multi_file(
        [{"file_path": f.file_path, "code": f.code} for f in req.files],
        req.language,
    )
    suggestions_by_file = {}
    for fp, slist in result.suggestions_by_file.items():
        suggestions_by_file[fp] = [
            {"id": str(s.id), "file_path": s.file_path, "line_number": s.line_number,
             "severity": s.severity.value, "rule_id": s.rule_id, "regulation": s.regulation,
             "article": s.article, "message": s.message, "explanation": s.explanation,
             "suggested_fix": s.suggested_fix, "original_code": s.original_code,
             "confidence": s.confidence}
            for s in slist
        ]
    return {
        "files_analyzed": result.files_analyzed,
        "total_suggestions": result.total_suggestions,
        "suggestions_by_file": suggestions_by_file,
        "cross_file_issues": result.cross_file_issues,
        "refactoring_opportunities": result.refactoring_opportunities,
    }


@router.get("/session/{session_id}/summary", response_model=SessionSummarySchema)
async def get_session_summary(session_id: UUID) -> dict:
    svc = PairProgrammingService()
    summary = await svc.get_session_summary(session_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


@router.post("/suggestion/{suggestion_id}/accept", response_model=SuggestionActionSchema)
async def accept_suggestion(suggestion_id: UUID) -> dict:
    svc = PairProgrammingService()
    suggestion = await svc.accept_suggestion(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"id": str(suggestion.id), "status": suggestion.status.value,
            "file_path": suggestion.file_path, "rule_id": suggestion.rule_id,
            "message": suggestion.message}


@router.post("/suggestion/{suggestion_id}/dismiss", response_model=SuggestionActionSchema)
async def dismiss_suggestion(suggestion_id: UUID) -> dict:
    svc = PairProgrammingService()
    suggestion = await svc.dismiss_suggestion(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"id": str(suggestion.id), "status": suggestion.status.value,
            "file_path": suggestion.file_path, "rule_id": suggestion.rule_id,
            "message": suggestion.message}


@router.post("/refactoring", response_model=list[RefactoringSuggestionSchema])
async def get_refactoring_suggestions(req: RefactoringRequest) -> list[dict]:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail=f"Unsupported language: {req.language}. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}")
    svc = PairProgrammingService()
    suggestions = await svc.get_refactoring_suggestions(
        [{"file_path": f.file_path, "code": f.code} for f in req.files],
        req.language,
    )
    return [
        {"id": str(s.id), "title": s.title, "description": s.description,
         "affected_files": s.affected_files, "regulation": s.regulation,
         "article": s.article, "effort_estimate": s.effort_estimate,
         "priority": s.priority, "suggested_approach": s.suggested_approach}
        for s in suggestions
    ]
