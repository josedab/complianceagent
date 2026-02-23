"""Compliance Editor Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_editor.models import (
    EditorFile,
    EditorSession,
    EditorStats,
    FileLanguage,
    InlineFix,
)


logger = structlog.get_logger()

_COMPLIANCE_PATTERNS: list[dict] = [
    {
        "pattern": "personal_data",
        "rule_id": "GDPR-PD-001",
        "framework": "GDPR",
        "message": "Personal data detected — ensure GDPR-compliant processing",
        "fix_hint": "# GDPR: Ensure consent and data minimization\n",
    },
    {
        "pattern": "patient",
        "rule_id": "HIPAA-PHI-001",
        "framework": "HIPAA",
        "message": "Potential PHI detected — ensure HIPAA safeguards",
        "fix_hint": "# HIPAA: Encrypt PHI and restrict access\n",
    },
    {
        "pattern": "card_number",
        "rule_id": "PCI-DSS-001",
        "framework": "PCI-DSS",
        "message": "Payment card data detected — ensure PCI-DSS compliance",
        "fix_hint": "# PCI-DSS: Tokenize card data, never store raw PANs\n",
    },
]


class ComplianceEditorService:
    """Service for in-editor compliance diagnostics and inline fixes."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._sessions: dict[UUID, EditorSession] = {}
        self._fixes: dict[str, list[InlineFix]] = {}
        self._total_files_opened: int = 0

    def _run_diagnostics(self, content: str, path: str) -> list[dict]:
        """Run compliance pattern matching on file content."""
        diagnostics: list[dict] = []
        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            lower_line = line.lower()
            for pattern_info in _COMPLIANCE_PATTERNS:
                if pattern_info["pattern"] in lower_line:
                    diagnostics.append({
                        "line": line_num,
                        "severity": "warning",
                        "rule_id": pattern_info["rule_id"],
                        "framework": pattern_info["framework"],
                        "message": pattern_info["message"],
                        "source": line.strip(),
                    })
        return diagnostics

    def _generate_fixes(self, path: str, content: str, diagnostics: list[dict]) -> list[InlineFix]:
        """Generate inline fixes for detected diagnostics."""
        fixes: list[InlineFix] = []
        lines = content.splitlines()
        for diag in diagnostics:
            line_num = diag["line"]
            original = lines[line_num - 1] if line_num <= len(lines) else ""
            pattern_info = next(
                (p for p in _COMPLIANCE_PATTERNS if p["rule_id"] == diag["rule_id"]),
                None,
            )
            if not pattern_info:
                continue
            fix = InlineFix(
                file_path=path,
                line_start=line_num,
                line_end=line_num,
                original_code=original,
                fixed_code=pattern_info["fix_hint"] + original,
                rule_id=diag["rule_id"],
                framework=diag["framework"],
                explanation=diag["message"],
                confidence=0.85,
            )
            fixes.append(fix)
        return fixes

    async def create_session(self, user_id: str) -> EditorSession:
        """Create a new editor session."""
        session = EditorSession(
            user_id=user_id,
            started_at=datetime.now(UTC),
        )
        self._sessions[session.id] = session
        logger.info("Editor session created", session_id=str(session.id), user_id=user_id)
        return session

    async def open_file(
        self,
        session_id: UUID,
        path: str,
        content: str,
        language: str,
    ) -> EditorFile:
        """Open a file in the editor and run compliance diagnostics."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        diagnostics = self._run_diagnostics(content, path)
        penalty = len(diagnostics) * 5.0
        posture_score = max(0.0, 100.0 - penalty)

        editor_file = EditorFile(
            path=path,
            content=content,
            language=FileLanguage(language),
            diagnostics=diagnostics,
            posture_score=posture_score,
            last_saved_at=datetime.now(UTC),
        )
        session.files.append(editor_file)
        session.active_file = path
        session.total_diagnostics += len(diagnostics)
        self._total_files_opened += 1

        fixes = self._generate_fixes(path, content, diagnostics)
        key = f"{session_id}:{path}"
        self._fixes[key] = fixes

        logger.info(
            "File opened",
            path=path,
            diagnostics=len(diagnostics),
            posture_score=posture_score,
        )
        return editor_file

    async def apply_fix(self, session_id: UUID, file_path: str, fix_id: UUID) -> InlineFix | None:
        """Apply an inline fix to a file."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        key = f"{session_id}:{file_path}"
        fixes = self._fixes.get(key, [])
        fix = next((f for f in fixes if f.id == fix_id), None)
        if not fix:
            return None

        # Apply fix to file content
        editor_file = next((f for f in session.files if f.path == file_path), None)
        if editor_file:
            lines = editor_file.content.splitlines()
            if fix.line_start <= len(lines):
                lines[fix.line_start - 1] = fix.fixed_code
                editor_file.content = "\n".join(lines)
                editor_file.diagnostics = self._run_diagnostics(editor_file.content, file_path)
                penalty = len(editor_file.diagnostics) * 5.0
                editor_file.posture_score = max(0.0, 100.0 - penalty)

        session.fixes_applied += 1
        logger.info("Fix applied", fix_id=str(fix_id), rule_id=fix.rule_id)
        return fix

    async def get_inline_fixes(self, session_id: UUID, file_path: str) -> list[InlineFix]:
        """Get available inline fixes for a file in a session."""
        key = f"{session_id}:{file_path}"
        return self._fixes.get(key, [])

    async def get_session(self, session_id: UUID) -> EditorSession | None:
        """Get an editor session by ID."""
        return self._sessions.get(session_id)

    async def close_session(self, session_id: UUID) -> bool:
        """Close an editor session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Editor session closed", session_id=str(session_id))
            return True
        return False

    async def get_stats(self) -> EditorStats:
        """Get editor usage statistics."""
        all_sessions = list(self._sessions.values())
        total_diagnostics = sum(s.total_diagnostics for s in all_sessions)
        total_fixes = sum(s.fixes_applied for s in all_sessions)

        all_files = [f for s in all_sessions for f in s.files]
        avg_posture = (
            sum(f.posture_score for f in all_files) / len(all_files) if all_files else 100.0
        )

        return EditorStats(
            total_sessions=len(self._sessions),
            files_opened=self._total_files_opened,
            diagnostics_shown=total_diagnostics,
            fixes_applied=total_fixes,
            avg_posture_score=round(avg_posture, 2),
        )
