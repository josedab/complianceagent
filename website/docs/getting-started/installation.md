---
sidebar_position: 1
title: Installation
description: Install ComplianceAgent using Docker or from source
---

# Installation

ComplianceAgent can be deployed using Docker (recommended) or installed from source for development.

## Prerequisites

Before installing ComplianceAgent, ensure you have:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | v2+ | Multi-container orchestration |
| Git | 2.30+ | Clone repository |

For development installations, you'll also need:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| uv | Latest | Python package manager (recommended) |

## Docker Installation (Recommended)

The fastest way to get ComplianceAgent running is with Docker Compose.

### 1. Clone the Repository

```bash
git clone https://github.com/josedab/complianceagent.git
cd complianceagent
```

### 2. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required settings
SECRET_KEY=your-secret-key-min-32-chars
COPILOT_API_KEY=your-github-copilot-api-key

# Optional: GitHub integration
GITHUB_APP_ID=your-github-app-id
GITHUB_APP_PRIVATE_KEY=your-private-key

# Optional: Billing (Stripe)
STRIPE_API_KEY=sk_test_...
```

:::tip Generating a Secret Key
Generate a secure secret key with:
```bash
openssl rand -hex 32
```
:::

### 3. Start Services

```bash
cd docker
docker compose up -d
```

This starts all required services:
- **PostgreSQL** - Primary database
- **Redis** - Cache and task queue
- **Elasticsearch** - Document search
- **MinIO** - S3-compatible object storage
- **Backend API** - FastAPI application
- **Frontend** - Next.js dashboard
- **Celery Workers** - Background task processing

### 4. Verify Installation

Check that all services are running:

```bash
docker compose ps
```

You should see all services with status `Up`:

```
NAME                    STATUS
complianceagent-api     Up (healthy)
complianceagent-web     Up
complianceagent-worker  Up
complianceagent-beat    Up
complianceagent-db      Up (healthy)
complianceagent-redis   Up (healthy)
complianceagent-es      Up (healthy)
complianceagent-minio   Up
```

### 5. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost:3000 | Web interface |
| API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/api/docs | Swagger UI |
| MinIO Console | http://localhost:9001 | Object storage UI |

## Development Installation

For local development with hot reloading:

### 1. Start Infrastructure

```bash
cd docker
docker compose up -d postgres redis elasticsearch minio
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 3. Set Up Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Start Background Workers (Optional)

For background task processing:

```bash
cd backend
source .venv/bin/activate

# Start worker
celery -A app.workers worker --loglevel=info

# In another terminal, start scheduler
celery -A app.workers beat --loglevel=info
```

## Using Make Commands

The project includes a Makefile for common operations:

```bash
# Install all dependencies
make install

# Start development environment
make dev

# Run backend
make run-backend

# Run frontend
make run-frontend

# Run all tests
make test

# Format and lint code
make format
make lint
```

## Verifying Your Installation

After installation, verify everything works:

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Create Test User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'
```

### 3. Access Dashboard

Open http://localhost:3000 and log in with your test credentials.

## Troubleshooting Installation

### Port Conflicts

If you see "port already in use" errors:

```bash
# Check what's using port 8000
lsof -i :8000

# Use different ports by editing docker-compose.yml
# or setting environment variables
API_PORT=8001 docker compose up -d
```

### Database Connection Issues

If the backend can't connect to PostgreSQL:

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Verify the database is ready
docker compose exec postgres pg_isready
```

### Elasticsearch Memory Issues

Elasticsearch requires significant memory. If it fails to start:

```bash
# Increase Docker memory limit (macOS/Windows)
# Docker Desktop → Settings → Resources → Memory → 8GB+

# Or reduce ES memory in docker-compose.yml
ES_JAVA_OPTS: "-Xms512m -Xmx512m"
```

## Next Steps

Now that ComplianceAgent is installed:

1. **[Quick Start](./quick-start)** - Get productive in 5 minutes
2. **[Configuration](./configuration)** - Customize your deployment
