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

## 🚀 Features

### Core Capabilities
- **Regulatory Monitoring**: Continuously track 100+ regulatory sources (GDPR, CCPA, EU AI Act, HIPAA, etc.)
- **AI-Powered Parsing**: Extract actionable requirements from legal text using GitHub Copilot SDK
- **Codebase Mapping**: Identify exactly which code is affected by each requirement
- **Code Generation**: Generate compliant code modifications with full audit trails
- **Multi-Jurisdiction**: Handle conflicting requirements across regions with configurable resolution strategies
- **Compliance Dashboard**: Real-time status, alerts, and progress tracking

### Developer Tools
- **IDE Compliance Copilot**: Real-time compliance suggestions in VS Code/JetBrains with quick-fixes
- **CI/CD Compliance Gates**: GitHub Action and GitLab CI with SARIF output to block non-compliant PRs
- **Compliance-as-Code Templates**: Pre-built templates for GDPR consent, HIPAA PHI, PCI tokenization
- **Multi-Cloud Compliance**: Analyze Terraform, CloudFormation, and Kubernetes for compliance

### Intelligence & Analytics
- **Regulatory Prediction Engine**: ML-powered 6-12 month advance warnings on upcoming regulations
- **Compliance Knowledge Graph**: Natural language queries and visualization of compliance relationships
- **Compliance Simulation Sandbox**: What-if analysis for code, architecture, and vendor changes
- **Automated Evidence Collection**: SOC 2, ISO 27001, HIPAA, PCI-DSS control mapping

### AI-Powered Assistance
- **Vendor/Third-Party Risk**: Dependency scanning and vendor compliance assessment
- **Regulatory Chatbot**: Conversational compliance assistant with codebase context

### Enterprise Features
- **SSO/SAML Authentication**: Enterprise identity provider integration
- **SCIM User Provisioning**: Automatic user management
- **Audit Trail**: Tamper-proof hash chain verification
- **Multi-tenant Architecture**: Organization-based isolation
- **API Access**: Full REST API for automation
- **Custom Workflows**: Configurable approval processes

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
- **State**: React Query + Zustand
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
git clone https://github.com/yourorg/complianceagent.git
cd complianceagent

# Copy environment template
cp .env.example .env

# Start all services
cd docker
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Development Setup

1. **Start infrastructure services**
```bash
cd docker
docker-compose up -d postgres redis elasticsearch minio
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

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `S3_ENDPOINT_URL` | S3/MinIO endpoint | `http://localhost:9000` |
| `S3_BUCKET_NAME` | Document storage bucket | `complianceagent` |
| `SECRET_KEY` | JWT signing key | (required) |
| `COPILOT_API_KEY` | GitHub Copilot SDK key | (required) |
| `GITHUB_APP_ID` | GitHub App ID | (optional) |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App private key | (optional) |
| `STRIPE_API_KEY` | Stripe API key | (optional) |
| `ENVIRONMENT` | `development` / `production` | `development` |

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
cd frontend
npm run test:e2e
```

## 🚢 Deployment

### Docker Swarm / Compose
```bash
cd docker
docker-compose -f docker-compose.prod.yml up -d
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

Proprietary - All rights reserved.

## 📧 Contact

- **Author**: Jose David Baena
- **Email**: contact@complianceagent.ai
- **Website**: https://complianceagent.ai
