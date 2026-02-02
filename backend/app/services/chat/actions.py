"""Action Handler - Execute actions triggered from chat."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger()

# UTC timezone for Python < 3.11 compatibility
UTC = timezone.utc


class ActionType(str, Enum):
    """Types of actions that can be triggered from chat."""
    # Code actions
    GENERATE_FIX = "generate_fix"
    CREATE_PR = "create_pr"
    ANALYZE_FILE = "analyze_file"
    ANALYZE_REPOSITORY = "analyze_repository"
    
    # Navigation actions
    SHOW_FILE = "show_file"
    SHOW_REQUIREMENT = "show_requirement"
    SHOW_MAPPING = "show_mapping"
    SHOW_REGULATION = "show_regulation"
    
    # Query actions
    SEARCH_CODE = "search_code"
    SEARCH_REGULATIONS = "search_regulations"
    EXPLAIN_REGULATION = "explain_regulation"
    
    # Status actions
    GET_COMPLIANCE_STATUS = "get_compliance_status"
    GET_VIOLATIONS = "get_violations"
    
    # Context actions
    SET_REPOSITORY = "set_repository"
    SET_REGULATION_FILTER = "set_regulation_filter"


@dataclass
class ChatAction:
    """An action to be executed from chat."""
    id: UUID = field(default_factory=uuid4)
    type: ActionType = ActionType.SHOW_FILE
    parameters: dict[str, Any] = field(default_factory=dict)
    
    # Display info
    label: str = ""
    description: str = ""
    icon: str = "arrow-right"  # UI icon name
    
    # Execution state
    executed: bool = False
    executed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "parameters": self.parameters,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "executed": self.executed,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "result": self.result,
            "error": self.error,
        }


class ActionHandler:
    """Handles execution of chat actions."""

    def __init__(
        self,
        db_session=None,
        github_client=None,
        copilot_client=None,
    ):
        self.db = db_session
        self.github = github_client
        self.copilot = copilot_client

    async def execute(
        self,
        action: ChatAction,
        organization_id: UUID,
        user_id: UUID | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        """Execute an action and return the result."""
        logger.info(
            "Executing chat action",
            action_type=action.type.value,
            action_id=str(action.id),
        )
        
        try:
            handler = self._get_handler(action.type)
            result = await handler(action, organization_id, user_id, access_token)
            
            action.executed = True
            action.executed_at = datetime.now(UTC)
            action.result = result
            
            return result
            
        except Exception as e:
            action.executed = True
            action.executed_at = datetime.now(UTC)
            action.error = str(e)
            logger.exception("Action execution failed", error=str(e))
            raise

    def _get_handler(self, action_type: ActionType):
        """Get the handler function for an action type."""
        handlers = {
            ActionType.GENERATE_FIX: self._handle_generate_fix,
            ActionType.CREATE_PR: self._handle_create_pr,
            ActionType.ANALYZE_FILE: self._handle_analyze_file,
            ActionType.ANALYZE_REPOSITORY: self._handle_analyze_repository,
            ActionType.SHOW_FILE: self._handle_show_file,
            ActionType.SHOW_REQUIREMENT: self._handle_show_requirement,
            ActionType.SHOW_MAPPING: self._handle_show_mapping,
            ActionType.SHOW_REGULATION: self._handle_show_regulation,
            ActionType.SEARCH_CODE: self._handle_search_code,
            ActionType.SEARCH_REGULATIONS: self._handle_search_regulations,
            ActionType.EXPLAIN_REGULATION: self._handle_explain_regulation,
            ActionType.GET_COMPLIANCE_STATUS: self._handle_get_compliance_status,
            ActionType.GET_VIOLATIONS: self._handle_get_violations,
            ActionType.SET_REPOSITORY: self._handle_set_repository,
            ActionType.SET_REGULATION_FILTER: self._handle_set_regulation_filter,
        }
        return handlers.get(action_type, self._handle_unknown)

    async def _handle_generate_fix(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Generate a fix for a compliance issue."""
        if not self.copilot:
            raise ValueError("Copilot client not available")
        
        requirement_id = action.parameters.get("requirement_id")
        file_path = action.parameters.get("file_path")
        violation = action.parameters.get("violation")
        
        # Generate fix using Copilot
        from app.agents.copilot import CopilotMessage
        
        async with self.copilot:
            response = await self.copilot.generate_compliant_code(
                requirement={"title": violation.get("message", "Fix compliance issue")},
                gaps=[violation] if violation else [],
                existing_code={file_path: action.parameters.get("file_content", "")},
                language=action.parameters.get("language", "python"),
            )
        
        return {
            "success": True,
            "fix": response,
            "files_generated": len(response.get("files", [])),
        }

    async def _handle_create_pr(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Create a PR with fixes."""
        from app.workers.pr_bot_tasks import create_fix_pr
        
        result = create_fix_pr.delay(
            owner=action.parameters.get("owner"),
            repo=action.parameters.get("repo"),
            pr_number=action.parameters.get("source_pr_number"),
            fixes=action.parameters.get("fixes", []),
            access_token=token or "",
            organization_id=str(org_id),
        )
        
        return {
            "success": True,
            "task_id": result.id,
            "message": "PR creation queued",
        }

    async def _handle_analyze_file(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Analyze a file for compliance issues."""
        file_path = action.parameters.get("file_path")
        content = action.parameters.get("content", "")
        
        from app.services.pr_review.analyzer import PRAnalyzer
        
        analyzer = PRAnalyzer()
        violations = await analyzer.analyze_diff_content(content, file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "violations": [
                {
                    "line": v.line_start,
                    "code": v.code,
                    "message": v.message,
                    "severity": v.severity.value,
                    "regulation": v.regulation,
                }
                for v in violations
            ],
            "total_violations": len(violations),
        }

    async def _handle_analyze_repository(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Trigger repository analysis."""
        from app.workers.analysis_tasks import analyze_repository
        
        repository_id = action.parameters.get("repository_id")
        
        result = analyze_repository.delay(repository_id, str(org_id))
        
        return {
            "success": True,
            "task_id": result.id,
            "message": "Repository analysis queued",
        }

    async def _handle_show_file(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get file content to display."""
        if not self.github or not token:
            return {
                "success": False,
                "error": "GitHub access not available",
                "action_url": f"/files/{action.parameters.get('file_path')}",
            }
        
        owner = action.parameters.get("owner")
        repo = action.parameters.get("repo")
        path = action.parameters.get("file_path")
        
        from app.services.github.client import GitHubClient
        
        async with GitHubClient(access_token=token) as client:
            file = await client.get_file_content(owner, repo, path)
            
            return {
                "success": True,
                "file_path": path,
                "content": file.content,
                "sha": file.sha,
            }

    async def _handle_show_requirement(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get requirement details."""
        if not self.db:
            return {"success": False, "error": "Database not available"}
        
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.requirement import Requirement
        
        requirement_id = UUID(action.parameters.get("requirement_id"))
        
        result = await self.db.execute(
            select(Requirement)
            .options(selectinload(Requirement.regulation))
            .where(Requirement.id == requirement_id)
        )
        req = result.scalar_one_or_none()
        
        if not req:
            return {"success": False, "error": "Requirement not found"}
        
        return {
            "success": True,
            "requirement": {
                "id": str(req.id),
                "reference_id": req.reference_id,
                "title": req.title,
                "description": req.description,
                "regulation": req.regulation.name if req.regulation else None,
                "category": req.category,
                "obligation_type": req.obligation_type,
            },
            "deep_link": f"/requirements/{req.id}",
        }

    async def _handle_show_mapping(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get mapping details."""
        if not self.db:
            return {"success": False, "error": "Database not available"}
        
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.codebase import CodebaseMapping
        
        mapping_id = UUID(action.parameters.get("mapping_id"))
        
        result = await self.db.execute(
            select(CodebaseMapping)
            .options(
                selectinload(CodebaseMapping.requirement),
                selectinload(CodebaseMapping.repository),
            )
            .where(CodebaseMapping.id == mapping_id)
        )
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            return {"success": False, "error": "Mapping not found"}
        
        return {
            "success": True,
            "mapping": {
                "id": str(mapping.id),
                "requirement": mapping.requirement.title if mapping.requirement else None,
                "repository": mapping.repository.full_name if mapping.repository else None,
                "status": mapping.compliance_status.value if mapping.compliance_status else None,
                "affected_files": mapping.affected_files,
                "gaps": mapping.gaps,
            },
            "deep_link": f"/mappings/{mapping.id}",
        }

    async def _handle_show_regulation(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get regulation details."""
        if not self.db:
            return {"success": False, "error": "Database not available"}
        
        from sqlalchemy import select
        from app.models.regulation import Regulation
        
        regulation_id = UUID(action.parameters.get("regulation_id"))
        
        result = await self.db.execute(
            select(Regulation).where(Regulation.id == regulation_id)
        )
        reg = result.scalar_one_or_none()
        
        if not reg:
            return {"success": False, "error": "Regulation not found"}
        
        return {
            "success": True,
            "regulation": {
                "id": str(reg.id),
                "name": reg.name,
                "framework": reg.framework.value if reg.framework else None,
                "description": reg.description,
                "jurisdiction": reg.jurisdiction,
            },
            "deep_link": f"/regulations/{reg.id}",
        }

    async def _handle_search_code(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Search code in repositories."""
        query = action.parameters.get("query", "")
        repository = action.parameters.get("repository")
        
        if self.github and token:
            owner, repo = repository.split("/") if repository else (None, None)
            
            from app.services.github.client import GitHubClient
            async with GitHubClient(access_token=token) as client:
                results = await client.search_code(query, owner, repo)
                
                return {
                    "success": True,
                    "results": [
                        {
                            "path": r.get("path"),
                            "repository": r.get("repository", {}).get("full_name"),
                            "url": r.get("html_url"),
                        }
                        for r in results[:10]
                    ],
                    "total": len(results),
                }
        
        return {"success": False, "error": "GitHub access not available"}

    async def _handle_search_regulations(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Search regulations."""
        if not self.db:
            return {"success": False, "error": "Database not available"}
        
        query = action.parameters.get("query", "")
        
        from sqlalchemy import select, or_
        from app.models.regulation import Regulation
        
        result = await self.db.execute(
            select(Regulation)
            .where(
                or_(
                    Regulation.name.ilike(f"%{query}%"),
                    Regulation.description.ilike(f"%{query}%"),
                )
            )
            .limit(10)
        )
        regs = list(result.scalars().all())
        
        return {
            "success": True,
            "results": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "framework": r.framework.value if r.framework else None,
                }
                for r in regs
            ],
            "total": len(regs),
        }

    async def _handle_explain_regulation(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get explanation of a regulation."""
        regulation = action.parameters.get("regulation")
        
        # Use Copilot to generate explanation
        if self.copilot:
            from app.agents.copilot import CopilotMessage
            
            async with self.copilot:
                response = await self.copilot.chat(
                    messages=[CopilotMessage(
                        role="user",
                        content=f"Explain {regulation} regulation for software developers. Focus on practical implementation requirements.",
                    )],
                    system_message="You are a compliance expert. Provide clear, actionable explanations.",
                    temperature=0.5,
                )
                
                return {
                    "success": True,
                    "regulation": regulation,
                    "explanation": response.content,
                }
        
        return {"success": False, "error": "Copilot not available"}

    async def _handle_get_compliance_status(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get compliance status for a repository."""
        if not self.db:
            return {"success": False, "error": "Database not available"}
        
        repository = action.parameters.get("repository")
        
        from sqlalchemy import select
        from app.models.codebase import Repository
        
        result = await self.db.execute(
            select(Repository)
            .where(Repository.full_name == repository)
            .where(Repository.organization_id == org_id)
        )
        repo = result.scalar_one_or_none()
        
        if not repo:
            return {"success": False, "error": "Repository not found"}
        
        return {
            "success": True,
            "repository": repository,
            "compliance_score": repo.compliance_score,
            "total_requirements": repo.total_requirements,
            "compliant_requirements": repo.compliant_requirements,
            "critical_gaps": repo.gaps_critical,
            "high_gaps": repo.gaps_major,
            "last_analyzed": repo.last_analyzed_at.isoformat() if repo.last_analyzed_at else None,
        }

    async def _handle_get_violations(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Get violations for a repository or file."""
        if not self.db:
            return {"success": False, "error": "Database not available"}
        
        repository = action.parameters.get("repository")
        file_path = action.parameters.get("file_path")
        
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.codebase import CodebaseMapping, Repository
        
        query = (
            select(CodebaseMapping)
            .options(selectinload(CodebaseMapping.requirement))
        )
        
        if repository:
            query = query.join(Repository).where(Repository.full_name == repository)
        
        result = await self.db.execute(query.limit(20))
        mappings = list(result.scalars().all())
        
        violations = []
        for mapping in mappings:
            if mapping.gaps:
                for gap in mapping.gaps:
                    if not file_path or gap.get("file_path") == file_path:
                        violations.append({
                            "requirement": mapping.requirement.title if mapping.requirement else "Unknown",
                            "severity": gap.get("severity"),
                            "description": gap.get("description"),
                            "file_path": gap.get("file_path"),
                        })
        
        return {
            "success": True,
            "violations": violations,
            "total": len(violations),
        }

    async def _handle_set_repository(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Set active repository context."""
        repository = action.parameters.get("repository")
        return {
            "success": True,
            "context_updated": True,
            "repository": repository,
        }

    async def _handle_set_regulation_filter(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Set regulation filter context."""
        regulations = action.parameters.get("regulations", [])
        return {
            "success": True,
            "context_updated": True,
            "regulations": regulations,
        }

    async def _handle_unknown(
        self, action: ChatAction, org_id: UUID, user_id: UUID | None, token: str | None
    ) -> dict[str, Any]:
        """Handle unknown action type."""
        return {
            "success": False,
            "error": f"Unknown action type: {action.type.value}",
        }

    def create_actions_from_response(
        self,
        response_content: str,
        context: dict[str, Any],
    ) -> list[ChatAction]:
        """Extract potential actions from an assistant response."""
        actions = []
        content_lower = response_content.lower()
        
        # Detect fix suggestions
        if "would you like me to generate a fix" in content_lower or "i can fix this" in content_lower:
            actions.append(ChatAction(
                type=ActionType.GENERATE_FIX,
                label="Generate Fix",
                description="Generate a compliance fix for this issue",
                icon="wrench",
                parameters=context,
            ))
        
        # Detect PR creation suggestions
        if "create a pr" in content_lower or "create a pull request" in content_lower:
            actions.append(ChatAction(
                type=ActionType.CREATE_PR,
                label="Create PR",
                description="Create a pull request with the fixes",
                icon="git-pull-request",
                parameters=context,
            ))
        
        # Detect analysis suggestions
        if "analyze" in content_lower and context.get("repository"):
            actions.append(ChatAction(
                type=ActionType.ANALYZE_REPOSITORY,
                label="Analyze Repository",
                description=f"Run compliance analysis on {context.get('repository')}",
                icon="search",
                parameters={"repository_id": context.get("repository_id")},
            ))
        
        return actions
