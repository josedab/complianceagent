# Development Guide

This guide covers the development setup, workflow, and best practices for contributing to ComplianceAgent.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Running the Application](#running-the-application)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| Docker | 24+ | Container runtime |
| Docker Compose | v2+ | Multi-container orchestration |
| uv | Latest | Python package manager (recommended) |
| Git | 2.40+ | Version control |

### Installing Prerequisites

```bash
# macOS (Homebrew)
brew install python@3.12 node docker docker compose git
pip install uv

# Ubuntu/Debian
sudo apt update && sudo apt install -y python3.12 nodejs npm docker.io git
pip install uv

# Windows (Chocolatey)
choco install python312 nodejs docker-desktop git
pip install uv
```

---

## Project Structure

```
complianceagent/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   │   ├── auth.py        # Authentication routes
│   │   │   ├── regulations.py # Regulation management
│   │   │   ├── repositories.py# Repository management
│   │   │   ├── compliance.py  # Compliance operations
│   │   │   ├── audit.py       # Audit trail
│   │   │   └── billing.py     # Stripe billing
│   │   ├── agents/            # AI orchestration layer
│   │   │   ├── copilot.py     # GitHub Copilot SDK client
│   │   │   └── orchestrator.py# Compliance pipeline coordinator
│   │   ├── core/              # Application core
│   │   │   ├── config.py      # Configuration settings
│   │   │   ├── database.py    # Database connection
│   │   │   ├── security.py    # Auth & encryption
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   └── metrics.py     # Prometheus metrics
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic validation schemas
│   │   ├── services/          # Business logic
│   │   │   ├── monitoring/    # Regulatory source monitoring
│   │   │   ├── parsing/       # Legal text parsing
│   │   │   ├── mapping/       # Codebase mapping
│   │   │   ├── generation/    # Code generation
│   │   │   └── audit/         # Audit trail management
│   │   └── workers/           # Celery background tasks
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite
│   └── pyproject.toml         # Python dependencies
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   │   ├── (auth)/        # Auth pages (login, signup)
│   │   │   └── dashboard/     # Dashboard pages
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # API client, utilities
│   │   └── types/             # TypeScript type definitions
│   ├── tests/                 # Jest test suite
│   └── package.json           # Node dependencies
│
├── docker/                     # Docker configuration
│   ├── docker-compose.yml     # Development
│   ├── docker-compose.prod.yml# Production
│   ├── Dockerfile.backend     # Backend image
│   └── Dockerfile.frontend    # Frontend image
│
├── infrastructure/             # Infrastructure as Code
│   ├── aws/                   # AWS Terraform
│   └── monitoring/            # Grafana, Prometheus config
│
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── Makefile                    # Development commands
└── .env.example               # Environment template
```

---

## Development Setup

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/josedab/complianceagent.git
cd complianceagent

# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Minimum: set SECRET_KEY to a random string
```

### 2. Install Dependencies

```bash
# Install both backend and frontend dependencies
make install

# Or separately:
make install-backend
make install-frontend
```

### 3. Install Pre-commit Hooks

```bash
make install-hooks
```

### 4. Start Infrastructure

```bash
# Start PostgreSQL, Redis, Elasticsearch, MinIO
make dev

# Verify services are running
docker ps
```

### 5. Initialize Database

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

---

## Running the Application

### Full Stack (Docker)

```bash
# Start all services
make up

# Access:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
```

### Development Mode (Hot Reload)

```bash
# Terminal 1: Start infrastructure
make dev

# Terminal 2: Run backend with hot reload
make run-backend

# Terminal 3: Run frontend with hot reload
make run-frontend

# Terminal 4 (optional): Run Celery workers
make run-workers
```

### Available Make Commands

```bash
make help          # Show all available commands

# Development
make dev           # Start infrastructure only
make run-backend   # Run FastAPI with uvicorn --reload
make run-frontend  # Run Next.js dev server
make run-workers   # Run Celery workers

# Testing
make test          # Run all tests
make test-backend  # Backend tests with coverage
make test-frontend # Frontend tests

# Code Quality
make lint          # Run all linters
make format        # Format all code
make type-check    # Run type checkers
make pre-commit    # Run all pre-commit hooks

# Database
make migrate       # Run migrations
make migrate-new MSG="description"  # Create new migration

# Docker
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make logs          # View logs
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feat/your-feature-name
```

**Branch naming conventions:**
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

Follow the [style guidelines](#code-quality) while coding.

### 3. Test Your Changes

```bash
# Run tests
make test

# Check code quality
make lint
make type-check
```

### 4. Commit with Conventional Commits

```bash
git add .
git commit -m "feat(api): add endpoint for bulk analysis"
```

**Commit types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `ci`, `chore`

### 5. Push and Create PR

```bash
git push origin feat/your-feature-name
# Then open a PR on GitHub
```

---

## Code Quality

### Backend (Python)

We use **Ruff** for linting and formatting, **mypy** for type checking.

```bash
# Lint
cd backend && ruff check .

# Format
cd backend && ruff format .

# Type check
cd backend && mypy app --ignore-missing-imports
```

**Python conventions:**
- Type hints on all functions
- Docstrings for public APIs
- Async/await for I/O operations
- Pydantic for data validation

```python
# Example: Proper function signature
async def process_regulation(
    regulation_id: UUID,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> ProcessingResult:
    """Process a regulation and extract requirements.
    
    Args:
        regulation_id: The regulation's unique identifier.
        db: Database session.
        force_refresh: If True, reprocess even if cached.
    
    Returns:
        ProcessingResult with extracted requirements.
    
    Raises:
        RegulationNotFoundError: If regulation doesn't exist.
    """
    ...
```

### Frontend (TypeScript)

We use **ESLint** for linting, **TypeScript** strict mode.

```bash
# Lint
cd frontend && npm run lint

# Type check
cd frontend && npm run type-check
```

**TypeScript conventions:**
- Explicit types for props and return values
- Interface definitions for API responses
- React Server Components where applicable

```typescript
// Example: Typed component
interface RegulationCardProps {
  regulation: Regulation;
  onSelect: (id: string) => void;
  isLoading?: boolean;
}

export function RegulationCard({
  regulation,
  onSelect,
  isLoading = false,
}: RegulationCardProps): JSX.Element {
  // ...
}
```

---

## Testing

### Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_auth.py -v

# Run specific test
pytest tests/test_api_auth.py::test_login_success -v
```

**Test organization:**
```
tests/
├── conftest.py          # Shared fixtures
├── test_api_*.py        # API endpoint tests
├── test_services_*.py   # Service layer tests
├── test_agents_*.py     # AI agent tests
└── test_models_*.py     # Model tests
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm run test:watch
```

### Integration Tests

```bash
# Ensure all services are running
make up

# Run integration tests
cd backend
pytest tests/integration/ -v
```

---

## Debugging

### Backend Debugging

**VS Code launch.json:**
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
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

**Using structlog:**
```python
import structlog
logger = structlog.get_logger()

logger.info("Processing regulation", regulation_id=str(reg.id), name=reg.name)
logger.error("Failed to parse", error=str(e), content_preview=content[:100])
```

### Frontend Debugging

**React DevTools:** Install the browser extension for component inspection.

**Next.js debugging:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Frontend: Next.js",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/frontend",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"]
    }
  ]
}
```

### Database Inspection

```bash
# Connect to PostgreSQL
docker exec -it complianceagent-postgres-1 psql -U complianceagent -d complianceagent

# View tables
\dt

# Inspect a table
SELECT * FROM regulations LIMIT 10;
```

---

## Common Tasks

### Adding a New API Endpoint

1. Create/update schema in `backend/app/schemas/`
2. Add route in `backend/app/api/v1/`
3. Implement service logic in `backend/app/services/`
4. Write tests in `backend/tests/`
5. Update API documentation

### Adding a New Regulatory Framework

1. Add framework to `RegulationFramework` enum in `backend/app/models/regulation.py`
2. Create parser in `backend/app/services/parsing/`
3. Add monitoring source in `backend/app/services/monitoring/`
4. Create migration: `make migrate-new MSG="add xyz framework"`
5. Add documentation in `docs/frameworks/`

### Adding a Frontend Component

1. Create component in `frontend/src/components/`
2. Add types in `frontend/src/types/`
3. Write tests in `frontend/src/__tests__/`
4. Export from appropriate index file

### Creating a Database Migration

```bash
# After modifying models
cd backend
source .venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Add xyz column to regulations"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head
```

---

## Environment Variables

See [Configuration Reference](../guides/configuration.md) for the complete list.

**Essential development variables:**
```bash
# .env
DATABASE_URL=postgresql+asyncpg://complianceagent:complianceagent@localhost:5432/complianceagent
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-development-secret-key
DEBUG=true
COPILOT_API_KEY=your-copilot-key  # For AI features
```

---

## Detailed Development Guides

For in-depth coverage of specific areas, see these dedicated guides:

| Guide | Description |
|-------|-------------|
| [Backend Development](backend.md) | Python patterns, async practices, SQLAlchemy usage, service layer |
| [Frontend Development](frontend.md) | Next.js patterns, React components, state management, styling |
| [Testing Guide](testing.md) | Test strategies, pytest/Jest patterns, integration tests, CI/CD |
| [IDE Extension](../../ide-extension/README.md) | VS Code extension development and patterns |

---

## Next Steps

- Read the [Architecture Overview](../architecture/overview.md)
- Check the [API Reference](../api/reference.md)
- Review [Contributing Guidelines](../../CONTRIBUTING.md)
