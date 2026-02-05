# Getting Started with ComplianceAgent

This guide walks you through setting up ComplianceAgent for local development and your first compliance analysis.

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** v2+
- **Python 3.12+** (for backend development)
- **Node.js 20+** (for frontend development)
- **Git**
- **GitHub Copilot API key** (optional for AI features)

## Quick Start (5 minutes)

The fastest way to get ComplianceAgent running:

```bash
# 1. Clone the repository
git clone https://github.com/josedab/complianceagent.git
cd complianceagent

# 2. Copy environment template
cp .env.example .env

# 3. Start all services with Docker
cd docker
docker compose up -d

# 4. Wait for services to be ready (about 30 seconds)
docker compose logs -f
# Press Ctrl+C when you see "Application startup complete"
```

Access the application:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## Development Setup

For active development, run services individually for hot-reloading.

### Step 1: Start Infrastructure

```bash
# Start databases and supporting services
make dev

# This starts:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - Elasticsearch (port 9200)
# - MinIO (port 9000)
```

### Step 2: Set Up Backend

```bash
cd backend

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run database migrations
alembic upgrade head

# Start the API server with hot-reload
uvicorn app.main:app --reload --port 8000
```

The API is now available at http://localhost:8000.

### Step 3: Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard is now available at http://localhost:3000.

### Step 4: Start Background Workers (Optional)

For features like regulatory monitoring and async analysis:

```bash
cd backend
source .venv/bin/activate

# Start Celery worker
celery -A app.workers worker --loglevel=info

# In a separate terminal, start the scheduler
celery -A app.workers beat --loglevel=info
```

## Configuration

### Essential Environment Variables

Edit `.env` to configure:

```bash
# Required for AI features
COPILOT_API_KEY=your-copilot-api-key

# Database (defaults work for local Docker)
DATABASE_URL=postgresql+asyncpg://complianceagent:complianceagent@localhost:5432/complianceagent

# Security (change in production!)
SECRET_KEY=change-me-to-a-secure-random-string
```

### GitHub Integration (Optional)

To analyze private repositories:

1. Create a GitHub App at https://github.com/settings/apps
2. Configure permissions: Contents (read), Pull requests (write)
3. Add to `.env`:

```bash
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
```

## Your First Compliance Analysis

### 1. Create an Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "password": "SecurePassword123!",
    "full_name": "Jane Developer"
  }'
```

### 2. Log In

```bash
# Get access token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "password": "SecurePassword123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 3. Create an Organization

```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Company",
    "industry": "technology"
  }'
```

### 4. Add a Repository

```bash
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "myorg/myrepo",
    "provider": "github"
  }'
```

### 5. Check Compliance Status

```bash
curl http://localhost:8000/api/v1/compliance/status \
  -H "Authorization: Bearer $TOKEN"
```

## Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# With coverage report
cd backend && pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Common Commands

```bash
# View all available commands
make help

# Lint code
make lint

# Format code
make format

# Type check
make type-check

# Run pre-commit hooks
make pre-commit

# View logs
make logs

# Stop all services
make down

# Clean up
make clean
```

## Project Structure

```
complianceagent/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # REST API endpoints
│   │   ├── agents/        # AI orchestration (Copilot SDK)
│   │   ├── core/          # Config, security, database
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic by domain
│   │   └── workers/       # Celery background tasks
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/           # Next.js App Router pages
│       ├── components/    # React components
│       └── lib/           # API client, utilities
├── docker/                # Docker configuration
├── infrastructure/        # Terraform (AWS)
└── docs/                  # Documentation
```

## Troubleshooting

### Database connection refused

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View logs
docker logs complianceagent-postgres-1

# Restart infrastructure
make dev-down && make dev
```

### Port already in use

```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Copilot API errors

1. Verify your API key is set in `.env`
2. Check the backend logs for detailed errors
3. Ensure you have Copilot API access

### Frontend not connecting to backend

Ensure `NEXT_PUBLIC_API_URL` in `.env` matches your backend URL:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Next Steps

- Read the [API Reference](../api/reference.md) for all endpoints
- Review the [Architecture Overview](../architecture/overview.md)
- Check [CONTRIBUTING.md](../../CONTRIBUTING.md) to contribute

## Getting Help

- **Issues**: https://github.com/josedab/complianceagent/issues
- **Discussions**: https://github.com/josedab/complianceagent/discussions
