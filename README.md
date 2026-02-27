# ComplianceAgent

[![CI](https://github.com/josedab/complianceagent/actions/workflows/ci.yml/badge.svg)](https://github.com/josedab/complianceagent/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/josedab/complianceagent/branch/main/graph/badge.svg)](https://codecov.io/gh/josedab/complianceagent)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/josedab/complianceagent/badge)](https://securityscorecards.dev/viewer/?uri=github.com/josedab/complianceagent)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Autonomous Regulatory Monitoring and Adaptation Platform**

ComplianceAgent is an AI-powered platform that automatically monitors regulatory changes, maps them to your codebase, and generates compliant code modifications—transforming compliance from a reactive burden into a proactive, automated workflow.

> **Status**: v0.1.0 (Alpha) — Core features are production-ready. See [Service Status](backend/app/services/STATUS.md) for implementation details.

## 🚀 Features

### Core Platform (Implemented)
- **Regulatory Monitoring**: Continuously crawl 20+ regulatory sources across GDPR, CCPA, EU AI Act, HIPAA, PCI-DSS, SOX, NIS2, and more — with automatic change detection and backpressure
- **AI-Powered Parsing**: Extract actionable requirements from legal text using GitHub Copilot SDK with circuit breaker and retry logic
- **Codebase Mapping**: Identify exactly which code is affected by each requirement
- **Code Generation**: Generate compliant code modifications with full audit trails
- **Tamper-Proof Audit Trail**: SHA-256 hash chain verification for all compliance events
- **Multi-Jurisdiction**: Handle conflicting requirements across 20+ jurisdictions with configurable resolution strategies

### Developer Tools (Implemented)
- **IDE Compliance Linting**: 25+ pre-built compliance patterns for GDPR, HIPAA, PCI-DSS, SOC 2, EU AI Act with AI-powered quick fixes via Copilot SDK
- **CI/CD Compliance Gates**: GitHub Action with SARIF output to block non-compliant PRs
- **PR Bot**: Automated compliance analysis on PR open/sync with GitHub Checks, inline comments, and smart labeling
- **Compliance-as-Code Templates**: Pre-built templates for GDPR consent, HIPAA PHI, PCI tokenization

### Intelligence & Analytics (Implemented)
- **Compliance Dashboard**: Real-time status, scoring, alerts, and progress tracking
- **Posture Scoring**: 7-dimension compliance scoring with industry benchmarking
- **Health Monitoring**: Service health with Prometheus metrics and Grafana dashboards

### Enterprise Features (Implemented)
- **SSO/SAML Authentication**: Enterprise identity provider integration
- **Multi-tenant Architecture**: Organization-based isolation with RBAC
- **API Access**: Full REST API with OpenAPI documentation
- **Audit Trail**: Tamper-proof hash chain with export and verification

### 🗺️ Roadmap (In Development)

The following features are in active development and available behind the `ENABLE_EXPERIMENTAL=true` flag:

| Feature | Status | Description |
|---------|--------|-------------|
| Compliance Copilot Chat | Beta | RAG-enhanced conversational assistant with pgvector semantic search |
| Regulatory Prediction Engine | Planned | ML-powered advance warnings on upcoming regulations |
| Compliance Knowledge Graph | Planned | Natural language queries and relationship visualization |
| Compliance Simulation Sandbox | Planned | What-if analysis for code and architecture changes |
| Multi-Cloud Compliance | Planned | Terraform, CloudFormation, and Kubernetes analysis |
| Vendor/Third-Party Risk | Planned | Dependency scanning and vendor compliance assessment |
| VS Code Extension | Beta | Real-time compliance linting (pattern-matching mode) |
| GitHub Marketplace App | Planned | One-click compliance scanning for any repository |

> See the full [Changelog](CHANGELOG.md) and [Architecture Decision Records](docs/architecture/) for technical details.

## 📋 Tech Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0
- **Cache/Queue**: Redis 7 with Celery
- **Search**: Elasticsearch 8
- **Crawling**: Playwright for JavaScript-heavy sites, HTTPX for simple pages
- **AI**: GitHub Copilot SDK for legal parsing and code generation

### Frontend
- **Framework**: Next.js 14 with App Router
- **UI Library**: React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: React Query
- **Components**: Radix UI primitives

### Infrastructure
- **Containers**: Docker & Docker Compose
- **Database**: PostgreSQL 16 (Aurora Serverless in production)
- **Cache**: Redis 7 (ElastiCache in production)
- **Search**: Elasticsearch 8 (OpenSearch in production)
- **Storage**: MinIO (S3 in production)
- **CI/CD**: GitHub Actions
- **Cloud**: AWS (ECS, RDS, ElastiCache, S3)

## 🏁 Quick Start

### Prerequisites

- Docker and Docker Compose v2+
- Python 3.12+ (for local development)
- Node.js 20+ (for local development)
- uv (Python package manager) or pip

### Option 1: Full Docker Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/josedab/complianceagent.git
cd complianceagent

# Copy environment template
cp .env.example .env

# Start all services
cd docker
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Development Setup

1. **Start infrastructure services**
```bash
cd docker
docker compose up -d postgres redis elasticsearch minio
```

2. **Set up backend**
```bash
cd backend

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Run database migrations
source .venv/bin/activate
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

3. **Set up frontend**
```bash
cd frontend
npm install
npm run dev
```

4. **Start Celery workers (optional, for background tasks)**
```bash
cd backend
celery -A app.workers worker --loglevel=info
celery -A app.workers beat --loglevel=info  # For scheduled tasks
```

## 📁 Project Structure

```
complianceagent/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST API endpoints
│   │   │   ├── auth.py       # Authentication
│   │   │   ├── regulations.py # Regulation management
│   │   │   ├── repositories.py # Repository management
│   │   │   ├── compliance.py  # Compliance operations
│   │   │   ├── audit.py       # Audit trail
│   │   │   ├── billing.py     # Stripe billing
│   │   │   └── sso.py         # SAML SSO
│   │   ├── core/             # Configuration, security
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Business logic
│   │   │   ├── monitoring/   # Regulatory source monitoring
│   │   │   ├── parsing/      # Legal text parsing
│   │   │   ├── mapping/      # Codebase mapping
│   │   │   ├── generation/   # Code generation
│   │   │   ├── audit/        # Audit trail
│   │   │   ├── github/       # GitHub integration
│   │   │   ├── enterprise/   # SSO/SAML
│   │   │   └── billing/      # Stripe integration
│   │   ├── agents/           # AI agent orchestration
│   │   │   ├── copilot.py    # Copilot SDK client
│   │   │   └── orchestrator.py # Compliance pipeline
│   │   └── workers/          # Celery background tasks
│   ├── alembic/              # Database migrations
│   └── tests/                # Pytest test suite
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   │   ├── (auth)/       # Auth pages (login, signup)
│   │   │   └── dashboard/    # Dashboard pages
│   │   ├── components/       # React components
│   │   ├── lib/              # API client, utilities
│   │   └── __tests__/        # Jest test suite
│   └── package.json
├── docker/
│   ├── docker-compose.yml    # Development
│   ├── docker-compose.prod.yml # Production
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── infrastructure/
│   └── aws/
│       └── main.tf           # Terraform AWS setup
├── .github/
│   └── workflows/
│       ├── ci.yml            # CI/CD pipeline
│       └── compliance-check.yml # PR compliance checks
└── docs/
```

## 🔌 API Reference

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login (returns JWT tokens) |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Get current user |

### Organizations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/organizations` | GET | List organizations |
| `/api/v1/organizations` | POST | Create organization |
| `/api/v1/organizations/{id}` | GET | Get organization |

### Regulations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/regulations` | GET | List regulations |
| `/api/v1/regulations/{id}` | GET | Get regulation details |
| `/api/v1/regulations/{id}/requirements` | GET | Get requirements |

### Repositories
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/repositories` | GET | List repositories |
| `/api/v1/repositories` | POST | Add repository |
| `/api/v1/repositories/{id}/analyze` | POST | Trigger analysis |

### Compliance
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/compliance/status` | GET | Get compliance status |
| `/api/v1/compliance/assess/{mapping_id}` | POST | Assess impact |
| `/api/v1/compliance/generate` | POST | Generate compliant code |
| `/api/v1/compliance/actions` | GET | List compliance actions |

### Audit
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/audit/` | GET | List audit entries |
| `/api/v1/audit/verify-chain` | GET | Verify hash chain |
| `/api/v1/audit/export` | GET | Export audit report |

### Billing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/billing/plans` | GET | List subscription plans |
| `/api/v1/billing/subscription` | GET | Get current subscription |
| `/api/v1/billing/checkout` | POST | Create checkout session |

### PR Bot
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pr-bot/analyze` | POST | Trigger PR analysis |
| `/api/v1/pr-bot/analyze/batch` | POST | Batch analyze multiple PRs |
| `/api/v1/pr-bot/task/{id}` | GET | Get task status |
| `/api/v1/pr-bot/config` | GET | Get PR bot configuration |
| `/api/v1/pr-bot/config` | PUT | Update PR bot configuration |
| `/api/v1/pr-bot/stats` | GET | Get analysis statistics |
| `/api/v1/pr-bot/history` | GET | Get analysis history |

### Compliance Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat/message` | POST | Send chat message |
| `/api/v1/chat/message/stream` | POST | Stream chat response (SSE) |
| `/api/v1/chat/conversations` | GET | List conversations |
| `/api/v1/chat/conversation/{id}` | DELETE | Delete conversation |
| `/api/v1/chat/analyze-code` | POST | Analyze code for compliance |
| `/api/v1/chat/explain-regulation` | POST | Explain regulation article |
| `/api/v1/chat/quick-actions` | GET | Get quick action suggestions |

### IDE Integration
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ide/analyze` | POST | Analyze document |
| `/api/v1/ide/quickfix` | POST | Get AI quick fix suggestion |
| `/api/v1/ide/deep-analyze` | POST | Deep AI analysis |
| `/api/v1/ide/suppressions` | GET | List team suppressions |
| `/api/v1/ide/suppressions` | POST | Request team suppression |
| `/api/v1/ide/suppressions/{id}` | DELETE | Delete suppression |
| `/api/v1/ide/feedback` | POST | Submit detection feedback |
| `/api/v1/ide/stats/rules` | GET | Get rule statistics |

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | PostgreSQL user | `complianceagent` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `complianceagent` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `ELASTICSEARCH_HOST` | Elasticsearch host | `localhost` |
| `ELASTICSEARCH_PORT` | Elasticsearch port | `9200` |
| `S3_ENDPOINT_URL` | S3/MinIO endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY` | S3/MinIO access key | `minioadmin` |
| `S3_SECRET_KEY` | S3/MinIO secret key | `minioadmin` |
| `SECRET_KEY` | JWT signing key | (required) |
| `COPILOT_API_KEY` | GitHub Copilot SDK key | (optional) |
| `ENVIRONMENT` | `development` / `staging` / `production` | `development` |

> **Note:** `DATABASE_URL`, `REDIS_URL`, and `ELASTICSEARCH_URL` are computed automatically
> from component variables above. See `backend/app/core/config.py` for full reference.

### Environment Variable Priority

1. **Shell environment variables** (highest priority)
2. **`.env` file** in project root
3. **`backend/app/core/config.py` defaults** (lowest priority)

> **Docker vs Local**: When running services in Docker, use container service names
> (`postgres`, `redis`, `elasticsearch`). For local development, use `localhost`.

### Without a Copilot API Key

Most features work without `COPILOT_API_KEY`. These features **require** it:

| Feature | Without API Key | With API Key |
|---------|----------------|--------------|
| Auth, orgs, users | ✅ Full functionality | ✅ Full functionality |
| Dashboards & scoring | ✅ Full functionality | ✅ Full functionality |
| Regulation management | ✅ CRUD operations | ✅ + AI-powered parsing |
| Codebase mapping | ✅ Pattern-based detection | ✅ + AI-powered analysis |
| Code generation | ❌ Not available | ✅ AI-generated code changes |
| Compliance chat | ❌ Not available | ✅ RAG-powered conversations |
| IDE linting | ⚠️ Pattern matching only | ✅ + AI quick-fix suggestions |
| PR review bot | ⚠️ Rule-based checks only | ✅ + AI-powered review |

## 📜 Supported Regulatory Frameworks

### Privacy & Data Protection

| Framework | Jurisdiction | Status |
|-----------|--------------|--------|
| **GDPR** | EU | ✅ Full support |
| **CCPA/CPRA** | US-CA | ✅ Full support |
| **HIPAA** | US-Federal | ✅ Full support |
| **Singapore PDPA** | Singapore | ✅ Full support |
| **India DPDP** | India | ✅ Full support |
| **Japan APPI** | Japan | ✅ Full support |
| **South Korea PIPA** | South Korea | ✅ Full support |
| **China PIPL** | China | ✅ Full support |

### Security & Compliance

| Framework | Jurisdiction | Status |
|-----------|--------------|--------|
| **PCI-DSS v4.0** | Global | ✅ Full support |
| **SOX** | US-Federal | ✅ Full support |
| **NIS2** | EU | ✅ Full support |
| **SOC 2** | Global | ✅ Full support |
| **ISO 27001:2022** | Global | ✅ Full support |

### AI Regulation

| Framework | Jurisdiction | Status |
|-----------|--------------|--------|
| **EU AI Act** | EU | ✅ Full support |
| **NIST AI RMF** | US-Federal | ✅ Full support |
| **ISO 42001** | Global | ✅ Full support |

### ESG & Sustainability

| Framework | Jurisdiction | Status |
|-----------|--------------|--------|
| **CSRD** | EU | ✅ Full support |
| **SEC Climate Disclosure** | US-Federal | ✅ Full support |
| **TCFD** | Global | ✅ Full support |

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### End-to-End Tests

```bash
# Start all services first
make dev && make run-backend &
make run-frontend &

# Run E2E tests with Playwright
make test-e2e
```

## 🚢 Deployment

### Docker Swarm / Compose
```bash
cd docker
docker compose -f docker-compose.prod.yml up -d
```

### AWS (Terraform)
```bash
cd infrastructure/aws
terraform init
terraform plan
terraform apply
```

### CI/CD
The GitHub Actions workflow automatically:
1. Runs tests on all PRs
2. Builds Docker images on merge to main
3. Deploys to staging environment
4. Requires manual approval for production

## 📊 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│   PostgreSQL    │
│   (Next.js)     │     │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Celery Workers │
                        └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Redis       │     │  Elasticsearch  │     │    S3/MinIO     │
│   (Cache/Queue) │     │    (Search)     │     │   (Documents)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` and `npm test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 📧 Contact

- **Author**: Jose David Baena
- **Email**: contact@complianceagent.ai
- **Website**: https://complianceagent.ai
