# Backend Development Guide

This guide covers the development practices, patterns, and workflows specific to the ComplianceAgent Python/FastAPI backend.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Setting Up Development Environment](#setting-up-development-environment)
- [Development Patterns](#development-patterns)
- [Working with the Database](#working-with-the-database)
- [API Development](#api-development)
- [Service Layer](#service-layer)
- [AI Integration](#ai-integration)
- [Background Tasks](#background-tasks)
- [Testing](#testing)
- [Debugging](#debugging)

---

## Architecture Overview

The backend follows a layered architecture:

```
┌───────────────────────────────────────────────────────────────┐
│                         API Layer                              │
│   FastAPI routers, request validation, authentication         │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                       Service Layer                            │
│   Business logic, orchestration, external integrations        │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                        Data Layer                              │
│   SQLAlchemy models, Pydantic schemas, repositories           │
└───────────────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **Async-first**: All I/O operations use `async/await`
- **Dependency Injection**: FastAPI's `Depends()` for clean dependencies
- **Type Safety**: Full type hints with Pydantic validation
- **Multi-tenancy**: All data scoped by `organization_id`

---

## Project Structure

```
backend/
├── app/
│   ├── api/v1/              # API endpoints (routers)
│   ├── agents/              # AI orchestration (Copilot SDK)
│   ├── core/                # Config, security, database
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic validation schemas
│   ├── services/            # Business logic
│   └── workers/             # Celery background tasks
├── alembic/                 # Database migrations
├── tests/                   # Test suite
└── pyproject.toml           # Dependencies
```

### Directory Responsibilities

| Directory | Purpose |
|-----------|---------|
| `api/v1/` | HTTP routing, request/response handling |
| `services/` | Business logic, external API calls |
| `models/` | Database table definitions |
| `schemas/` | Request/response data shapes |
| `agents/` | AI/Copilot SDK integration |
| `core/` | Cross-cutting concerns (auth, config) |
| `workers/` | Async background task definitions |

---

## Setting Up Development Environment

### Prerequisites

```bash
# Install Python 3.12+
brew install python@3.12  # macOS
# or use pyenv for version management

# Install uv (recommended package manager)
pip install uv

# Install PostgreSQL (or use Docker)
brew install postgresql@16
```

### Installation

```bash
cd backend

# Create virtual environment
uv venv

# Install dependencies (including dev tools)
uv pip install -e ".[dev]"

# Activate virtual environment
source .venv/bin/activate

# Verify installation
python -c "from app.main import app; print('OK')"
```

### Environment Variables

Create a `.env` file in the repository root:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://complianceagent:complianceagent@localhost:5432/complianceagent
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-development-secret-key-min-32-chars

# Optional (for AI features)
COPILOT_API_KEY=your-copilot-api-key

# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
```

---

## Development Patterns

### Async/Await Everywhere

All database and external I/O operations must be async:

```python
# ✅ Correct: Async database query
async def get_regulation(db: AsyncSession, regulation_id: UUID) -> Regulation | None:
    result = await db.execute(
        select(Regulation).where(Regulation.id == regulation_id)
    )
    return result.scalar_one_or_none()

# ❌ Wrong: Blocking call in async context
def get_regulation(db: Session, regulation_id: UUID) -> Regulation | None:
    return db.query(Regulation).filter_by(id=regulation_id).first()
```

### Dependency Injection

Use FastAPI's `Depends()` for clean, testable code:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User

router = APIRouter()

@router.get("/regulations/{id}")
async def get_regulation(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # db and current_user are injected
    ...
```

### Type Hints

All functions must have complete type annotations:

```python
from typing import Sequence
from uuid import UUID
from app.models import Regulation
from app.schemas import RegulationCreate, RegulationResponse

async def create_regulations(
    db: AsyncSession,
    *,
    regulations: Sequence[RegulationCreate],
    organization_id: UUID,
) -> list[Regulation]:
    """Create multiple regulations.
    
    Args:
        db: Database session.
        regulations: List of regulation data to create.
        organization_id: Organization to associate regulations with.
    
    Returns:
        List of created Regulation instances.
    """
    ...
```

### Error Handling

Use custom exceptions that map to HTTP status codes:

```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class NotFoundError(HTTPException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found"
        )

class PermissionDeniedError(HTTPException):
    def __init__(self, action: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied for action: {action}"
        )

# Usage in services
async def get_regulation(db: AsyncSession, id: UUID) -> Regulation:
    regulation = await db.get(Regulation, id)
    if not regulation:
        raise NotFoundError("Regulation", str(id))
    return regulation
```

---

## Working with the Database

### SQLAlchemy Models

Define models in `app/models/`:

```python
# app/models/regulation.py
from datetime import date, datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Date, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Regulation(Base):
    __tablename__ = "regulations"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    framework: Mapped[str] = mapped_column(String(50))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    effective_date: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    organization: Mapped["Organization"] = relationship(back_populates="regulations")
    
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="regulation",
        cascade="all, delete-orphan"
    )
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
```

### Pydantic Schemas

Define schemas in `app/schemas/`:

```python
# app/schemas/regulation.py
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field

class RegulationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    framework: str
    jurisdiction: str
    effective_date: date

class RegulationCreate(RegulationBase):
    pass

class RegulationUpdate(BaseModel):
    name: str | None = None
    status: str | None = None

class RegulationResponse(RegulationBase):
    id: UUID
    status: str
    requirements_count: int
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

### Database Queries

Use SQLAlchemy 2.0 style queries:

```python
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

# Simple query
result = await db.execute(
    select(Regulation).where(Regulation.id == regulation_id)
)
regulation = result.scalar_one_or_none()

# Query with joins (eager loading)
result = await db.execute(
    select(Regulation)
    .where(Regulation.organization_id == org_id)
    .options(selectinload(Regulation.requirements))
    .order_by(Regulation.created_at.desc())
    .limit(20)
)
regulations = result.scalars().all()

# Aggregation
result = await db.execute(
    select(func.count(Requirement.id))
    .where(Requirement.regulation_id == regulation_id)
)
count = result.scalar_one()
```

### Migrations

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Add status column to regulations"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## API Development

### Router Structure

```python
# app/api/v1/regulations.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas.regulation import (
    RegulationCreate,
    RegulationResponse,
    RegulationListResponse,
)
from app.services.regulation import RegulationService

router = APIRouter(prefix="/regulations", tags=["regulations"])

@router.get("", response_model=RegulationListResponse)
async def list_regulations(
    framework: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List regulations for the current organization."""
    service = RegulationService(db)
    return await service.list(
        organization_id=current_user.organization_id,
        framework=framework,
        limit=limit,
        offset=offset,
    )

@router.post("", response_model=RegulationResponse, status_code=status.HTTP_201_CREATED)
async def create_regulation(
    data: RegulationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new regulation."""
    service = RegulationService(db)
    return await service.create(
        data=data,
        organization_id=current_user.organization_id,
    )
```

### Response Models

Always use Pydantic models for responses:

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
    
class RegulationListResponse(PaginatedResponse[RegulationResponse]):
    pass
```

---

## Service Layer

Services contain business logic and are database-agnostic where possible:

```python
# app/services/regulation.py
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Regulation
from app.schemas.regulation import RegulationCreate, RegulationListResponse
from app.core.exceptions import NotFoundError

class RegulationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list(
        self,
        organization_id: UUID,
        *,
        framework: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> RegulationListResponse:
        query = select(Regulation).where(
            Regulation.organization_id == organization_id
        )
        
        if framework:
            query = query.where(Regulation.framework == framework)
        
        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        
        # Get paginated results
        result = await self.db.execute(
            query.order_by(Regulation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = result.scalars().all()
        
        return RegulationListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
    
    async def create(
        self,
        data: RegulationCreate,
        organization_id: UUID,
    ) -> Regulation:
        regulation = Regulation(
            **data.model_dump(),
            organization_id=organization_id,
        )
        self.db.add(regulation)
        await self.db.commit()
        await self.db.refresh(regulation)
        return regulation
```

---

## AI Integration

### Copilot SDK Client

```python
# app/agents/copilot.py
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()

class CopilotClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60),
    )
    async def analyze_legal_text(
        self,
        content: str,
        framework: str,
    ) -> list[ExtractedRequirement]:
        """Extract compliance requirements from legal text."""
        logger.info(
            "analyzing_legal_text",
            framework=framework,
            content_length=len(content),
        )
        
        prompt = self._build_extraction_prompt(content, framework)
        response = await self._call_api(prompt)
        
        return self._parse_requirements(response)
```

---

## Background Tasks

### Celery Tasks

```python
# app/workers/monitoring.py
from celery import shared_task
from app.services.monitoring import MonitoringService

@shared_task(bind=True, max_retries=3)
def check_regulatory_sources(self):
    """Periodic task to check for regulatory updates."""
    try:
        service = MonitoringService()
        updated = service.check_all_sources()
        return {"sources_checked": len(updated)}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

# Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    "check-regulatory-sources": {
        "task": "app.workers.monitoring.check_regulatory_sources",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
}
```

---

## Testing

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_api_auth.py         # Auth endpoint tests
├── test_api_regulations.py  # Regulation endpoint tests
├── test_services_*.py       # Service layer tests
└── test_agents_*.py         # AI agent tests
```

### Fixtures

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
async def client(db_session):
    """Create a test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers for testing."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### Test Examples

```python
# tests/test_api_regulations.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_regulations(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/regulations", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_create_regulation(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/regulations",
        headers=auth_headers,
        json={
            "name": "Test Regulation",
            "framework": "gdpr",
            "jurisdiction": "eu",
            "effective_date": "2024-01-01",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Regulation"
```

---

## Debugging

### Logging

```python
import structlog

logger = structlog.get_logger()

async def process_regulation(regulation_id: UUID):
    logger.info("processing_regulation", regulation_id=str(regulation_id))
    
    try:
        # ... processing
        logger.info("regulation_processed", requirement_count=len(requirements))
    except Exception as e:
        logger.error("processing_failed", error=str(e), regulation_id=str(regulation_id))
        raise
```

### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "env": {"PYTHONPATH": "${workspaceFolder}/backend"}
    },
    {
      "name": "Backend: Tests",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "-x"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker exec -it complianceagent-postgres-1 psql -U complianceagent -d complianceagent

# Useful queries
\dt                           # List tables
\d regulations                # Describe table
SELECT * FROM regulations LIMIT 5;
```

---

## Next Steps

- [API Reference](../api/reference.md) - Complete endpoint documentation
- [Architecture Overview](../architecture/overview.md) - System design
- [Testing Guide](testing.md) - Comprehensive testing strategies
