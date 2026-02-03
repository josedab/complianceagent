# ComplianceAgent Backend

The Python/FastAPI backend powering the ComplianceAgent platform.

## Overview

This backend service provides:
- **REST API** for compliance operations, repository management, and user authentication
- **AI Orchestration** via the GitHub Copilot SDK for legal text parsing and code generation
- **Background Processing** with Celery for regulatory monitoring and async analysis
- **Multi-tenant Architecture** with organization-based data isolation

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.104+ |
| Python | 3.12+ |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| Cache/Queue | Redis 7 + Celery |
| Search | Elasticsearch 8 |
| AI | GitHub Copilot SDK |
| Auth | JWT (access + refresh tokens), SAML/SSO |

## Project Structure

```
backend/
├── app/
│   ├── api/v1/              # REST API endpoints
│   │   ├── auth.py          # Authentication (login, register, refresh)
│   │   ├── organizations.py # Organization management
│   │   ├── regulations.py   # Regulation and requirement APIs
│   │   ├── repositories.py  # Repository management
│   │   ├── compliance.py    # Compliance status and actions
│   │   ├── audit.py         # Audit trail and reporting
│   │   ├── billing.py       # Stripe billing integration
│   │   ├── sso.py           # SAML/SSO endpoints
│   │   ├── pr_bot.py        # PR analysis bot
│   │   ├── chat.py          # Compliance chat assistant
│   │   └── ide.py           # IDE integration endpoints
│   │
│   ├── agents/              # AI orchestration layer
│   │   ├── copilot.py       # Copilot SDK client with retry logic
│   │   └── orchestrator.py  # Compliance pipeline coordinator
│   │
│   ├── core/                # Application core
│   │   ├── config.py        # Settings (Pydantic BaseSettings)
│   │   ├── database.py      # Async SQLAlchemy engine
│   │   ├── security.py      # JWT, password hashing
│   │   ├── exceptions.py    # Custom exception classes
│   │   └── dependencies.py  # FastAPI dependencies
│   │
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User, Organization
│   │   ├── regulation.py    # Regulation, Requirement
│   │   ├── repository.py    # Repository, CodebaseMapping
│   │   └── audit.py         # AuditEntry (hash chain)
│   │
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── auth.py          # Login, Token schemas
│   │   ├── regulation.py    # Regulation CRUD schemas
│   │   └── compliance.py    # Compliance action schemas
│   │
│   ├── services/            # Business logic layer
│   │   ├── monitoring/      # Regulatory source crawlers
│   │   ├── parsing/         # Legal text parsing (Copilot)
│   │   ├── mapping/         # Code-to-requirement mapping
│   │   ├── generation/      # Compliant code generation
│   │   ├── audit/           # Audit trail management
│   │   ├── github/          # GitHub API integration
│   │   ├── enterprise/      # SSO/SAML services
│   │   └── billing/         # Stripe subscription logic
│   │
│   ├── workers/             # Celery background tasks
│   │   ├── celery.py        # Celery app configuration
│   │   ├── monitoring.py    # Scheduled source checks
│   │   └── analysis.py      # Repository analysis tasks
│   │
│   └── main.py              # FastAPI application entry point
│
├── alembic/                 # Database migrations
│   ├── versions/            # Migration scripts
│   └── env.py               # Alembic configuration
│
├── tests/                   # Pytest test suite
│   ├── conftest.py          # Shared fixtures
│   ├── test_api_*.py        # API endpoint tests
│   └── test_services_*.py   # Service layer tests
│
├── pyproject.toml           # Python dependencies & tool config
└── alembic.ini              # Alembic configuration
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (or Docker)
- Redis (or Docker)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# From repository root
cd backend

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy environment template
cp ../.env.example ../.env
# Edit .env with your settings

# Start infrastructure (from repo root)
cd ..
make dev

# Run database migrations
cd backend
source .venv/bin/activate
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API is now available at http://localhost:8000. View interactive docs at http://localhost:8000/api/docs.

### Running Celery Workers

```bash
# Worker for processing tasks
celery -A app.workers worker --loglevel=info

# Beat scheduler for periodic tasks (separate terminal)
celery -A app.workers beat --loglevel=info
```

## Development

### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Lint
ruff check .

# Format
ruff format .

# Auto-fix issues
ruff check --fix .
```

### Type Checking

```bash
mypy app --ignore-missing-imports
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_auth.py -v

# Run specific test
pytest tests/test_api_auth.py::test_login_success -v
```

### Database Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Add new field to User"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | JWT signing key (32+ chars) |
| `COPILOT_API_KEY` | For AI | GitHub Copilot SDK API key |
| `GITHUB_APP_ID` | For GitHub | GitHub App ID for repo access |
| `STRIPE_API_KEY` | For billing | Stripe secret key |

## API Overview

| Endpoint Group | Base Path | Description |
|----------------|-----------|-------------|
| Auth | `/api/v1/auth` | Login, register, refresh tokens |
| Organizations | `/api/v1/organizations` | Org management |
| Regulations | `/api/v1/regulations` | Regulation & requirements |
| Repositories | `/api/v1/repositories` | Repo management & analysis |
| Compliance | `/api/v1/compliance` | Status, assessment, code gen |
| Audit | `/api/v1/audit` | Audit trail & reports |
| PR Bot | `/api/v1/pr-bot` | PR analysis automation |
| Chat | `/api/v1/chat` | Compliance chat assistant |
| IDE | `/api/v1/ide` | IDE integration endpoints |

See the [API Reference](../docs/api/reference.md) for complete documentation.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  Services   │────▶│   Models    │
│   (API)     │     │  (Logic)    │     │   (ORM)     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │   Agents    │
       │            │  (Copilot)  │
       │            └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   Celery    │────▶│    Redis    │
│  (Workers)  │     │  (Queue)    │
└─────────────┘     └─────────────┘
```

## Contributing

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make changes following our style guidelines
3. Write tests for new functionality
4. Run `make lint` and `make test`
5. Commit with conventional commit messages
6. Open a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## License

MIT