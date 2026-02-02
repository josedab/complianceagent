"""PR Analysis Queue - Manages async PR review tasks."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger()


class PRTaskStatus(str, Enum):
    """Status of a PR analysis task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PRTaskPriority(int, Enum):
    """Priority levels for PR analysis tasks."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class PRAnalysisTask:
    """A task to analyze a PR for compliance."""
    id: UUID = field(default_factory=uuid4)
    owner: str = ""
    repo: str = ""
    pr_number: int = 0
    head_sha: str = ""
    base_sha: str = ""
    organization_id: UUID | None = None
    
    # Task metadata
    status: PRTaskStatus = PRTaskStatus.PENDING
    priority: PRTaskPriority = PRTaskPriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # Configuration
    deep_analysis: bool = True
    enabled_regulations: list[str] = field(default_factory=list)
    post_comments: bool = True
    create_check_run: bool = True
    auto_label: bool = True
    
    # Results
    result: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "owner": self.owner,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "base_sha": self.base_sha,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "deep_analysis": self.deep_analysis,
            "enabled_regulations": self.enabled_regulations,
            "post_comments": self.post_comments,
            "create_check_run": self.create_check_run,
            "auto_label": self.auto_label,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PRAnalysisTask":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]) if data.get("id") else uuid4(),
            owner=data.get("owner", ""),
            repo=data.get("repo", ""),
            pr_number=data.get("pr_number", 0),
            head_sha=data.get("head_sha", ""),
            base_sha=data.get("base_sha", ""),
            organization_id=UUID(data["organization_id"]) if data.get("organization_id") else None,
            status=PRTaskStatus(data.get("status", "pending")),
            priority=PRTaskPriority(data.get("priority", 1)),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            deep_analysis=data.get("deep_analysis", True),
            enabled_regulations=data.get("enabled_regulations", []),
            post_comments=data.get("post_comments", True),
            create_check_run=data.get("create_check_run", True),
            auto_label=data.get("auto_label", True),
            result=data.get("result", {}),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )


class PRAnalysisQueue:
    """Queue manager for PR analysis tasks using Redis."""

    QUEUE_KEY = "complianceagent:pr_analysis:queue"
    TASK_KEY_PREFIX = "complianceagent:pr_analysis:task:"
    PROCESSING_SET = "complianceagent:pr_analysis:processing"

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._local_queue: list[PRAnalysisTask] = []  # Fallback for testing

    async def enqueue(self, task: PRAnalysisTask) -> str:
        """Add a task to the queue."""
        task_id = str(task.id)
        
        if self.redis:
            import json
            # Store task data
            await self.redis.set(
                f"{self.TASK_KEY_PREFIX}{task_id}",
                json.dumps(task.to_dict()),
                ex=86400 * 7,  # 7 day TTL
            )
            # Add to priority queue (sorted set by priority + timestamp)
            score = task.priority.value * 1_000_000_000 + int(task.created_at.timestamp())
            await self.redis.zadd(self.QUEUE_KEY, {task_id: score})
        else:
            self._local_queue.append(task)
        
        logger.info(
            "PR analysis task enqueued",
            task_id=task_id,
            repo=f"{task.owner}/{task.repo}",
            pr_number=task.pr_number,
        )
        return task_id

    async def dequeue(self) -> PRAnalysisTask | None:
        """Get the next task from the queue."""
        if self.redis:
            import json
            # Get highest priority task
            result = await self.redis.zpopmax(self.QUEUE_KEY)
            if not result:
                return None
            
            task_id = result[0][0]
            task_data = await self.redis.get(f"{self.TASK_KEY_PREFIX}{task_id}")
            if not task_data:
                return None
            
            task = PRAnalysisTask.from_dict(json.loads(task_data))
            task.status = PRTaskStatus.IN_PROGRESS
            task.started_at = datetime.now(timezone.utc)
            
            # Mark as processing
            await self.redis.sadd(self.PROCESSING_SET, task_id)
            await self.redis.set(
                f"{self.TASK_KEY_PREFIX}{task_id}",
                json.dumps(task.to_dict()),
            )
            return task
        else:
            if not self._local_queue:
                return None
            # Sort by priority
            self._local_queue.sort(key=lambda t: t.priority.value, reverse=True)
            task = self._local_queue.pop(0)
            task.status = PRTaskStatus.IN_PROGRESS
            task.started_at = datetime.now(timezone.utc)
            return task

    async def complete(self, task: PRAnalysisTask, result: dict[str, Any]) -> None:
        """Mark a task as completed."""
        task.status = PRTaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.result = result
        
        if self.redis:
            import json
            task_id = str(task.id)
            await self.redis.set(
                f"{self.TASK_KEY_PREFIX}{task_id}",
                json.dumps(task.to_dict()),
                ex=86400,  # 1 day TTL for completed tasks
            )
            await self.redis.srem(self.PROCESSING_SET, task_id)
        
        logger.info(
            "PR analysis task completed",
            task_id=str(task.id),
            repo=f"{task.owner}/{task.repo}",
            pr_number=task.pr_number,
        )

    async def fail(self, task: PRAnalysisTask, error: str) -> bool:
        """Mark a task as failed. Returns True if should retry."""
        task.retry_count += 1
        task.error_message = error
        
        if task.retry_count < task.max_retries:
            # Re-queue for retry with lower priority
            task.status = PRTaskStatus.PENDING
            task.priority = PRTaskPriority.LOW
            await self.enqueue(task)
            logger.warning(
                "PR analysis task failed, will retry",
                task_id=str(task.id),
                retry_count=task.retry_count,
                error=error,
            )
            return True
        
        task.status = PRTaskStatus.FAILED
        task.completed_at = datetime.now(timezone.utc)
        
        if self.redis:
            import json
            task_id = str(task.id)
            await self.redis.set(
                f"{self.TASK_KEY_PREFIX}{task_id}",
                json.dumps(task.to_dict()),
                ex=86400 * 7,
            )
            await self.redis.srem(self.PROCESSING_SET, task_id)
        
        logger.error(
            "PR analysis task failed permanently",
            task_id=str(task.id),
            error=error,
        )
        return False

    async def get_task(self, task_id: str) -> PRAnalysisTask | None:
        """Get a task by ID."""
        if self.redis:
            import json
            task_data = await self.redis.get(f"{self.TASK_KEY_PREFIX}{task_id}")
            if task_data:
                return PRAnalysisTask.from_dict(json.loads(task_data))
        else:
            for task in self._local_queue:
                if str(task.id) == task_id:
                    return task
        return None

    async def get_queue_size(self) -> int:
        """Get number of pending tasks."""
        if self.redis:
            return await self.redis.zcard(self.QUEUE_KEY)
        return len(self._local_queue)

    async def cancel_for_pr(self, owner: str, repo: str, pr_number: int) -> int:
        """Cancel all pending tasks for a specific PR."""
        cancelled = 0
        if self.redis:
            import json
            # Get all pending task IDs
            task_ids = await self.redis.zrange(self.QUEUE_KEY, 0, -1)
            for task_id in task_ids:
                task_data = await self.redis.get(f"{self.TASK_KEY_PREFIX}{task_id}")
                if task_data:
                    task = PRAnalysisTask.from_dict(json.loads(task_data))
                    if task.owner == owner and task.repo == repo and task.pr_number == pr_number:
                        await self.redis.zrem(self.QUEUE_KEY, task_id)
                        task.status = PRTaskStatus.CANCELLED
                        await self.redis.set(
                            f"{self.TASK_KEY_PREFIX}{task_id}",
                            json.dumps(task.to_dict()),
                        )
                        cancelled += 1
        else:
            self._local_queue = [
                t for t in self._local_queue
                if not (t.owner == owner and t.repo == repo and t.pr_number == pr_number)
            ]
        return cancelled
