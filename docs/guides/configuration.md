# Configuration Reference

This guide covers all configuration options for ComplianceAgent, including environment variables, application settings, and service-specific configuration.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Application Settings](#application-settings)
- [Database Configuration](#database-configuration)
- [Redis Configuration](#redis-configuration)
- [Elasticsearch Configuration](#elasticsearch-configuration)
- [AI/Copilot Configuration](#aicopilot-configuration)
- [Authentication Configuration](#authentication-configuration)
- [GitHub Integration](#github-integration)
- [Billing Configuration](#billing-configuration)
- [Logging Configuration](#logging-configuration)
- [Feature Flags](#feature-flags)

---

## Environment Variables

### Quick Reference

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Core Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | Environment name (`development`, `staging`, `production`) |
| `DEBUG` | No | `false` | Enable debug mode (never in production) |
| `SECRET_KEY` | **Yes** | - | JWT signing key (32+ random characters) |
| `APP_NAME` | No | `ComplianceAgent` | Application name |
| `APP_VERSION` | No | `1.0.0` | Application version |
| `API_PREFIX` | No | `/api/v1` | API URL prefix |

### Generate a Secret Key

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

---

## Application Settings

### Backend Configuration

```python
# backend/app/core/config.py (settings overview)

class Settings:
    # Application
    app_name: str = "ComplianceAgent"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    rate_limit_calls: int = 100
    rate_limit_period: int = 60  # seconds
```

### Frontend Configuration

```typescript
// frontend/next.config.js
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'ComplianceAgent',
  },
};
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | **Yes** | `http://localhost:8000/api/v1` | Backend API URL |
| `NEXT_PUBLIC_APP_NAME` | No | `ComplianceAgent` | Application display name |

---

## Database Configuration

### PostgreSQL

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | **Yes** | - | Full connection string |
| `DB_POOL_SIZE` | No | `5` | Connection pool size |
| `DB_MAX_OVERFLOW` | No | `10` | Max overflow connections |
| `DB_POOL_TIMEOUT` | No | `30` | Pool timeout (seconds) |
| `DB_ECHO` | No | `false` | Log SQL queries (debug only) |

### Connection String Format

```bash
# Standard format
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Examples
# Local development
DATABASE_URL=postgresql+asyncpg://complianceagent:complianceagent@localhost:5432/complianceagent

# AWS RDS
DATABASE_URL=postgresql+asyncpg://admin:password@mydb.cluster-xxx.us-east-1.rds.amazonaws.com:5432/complianceagent

# With SSL (production)
DATABASE_URL=postgresql+asyncpg://admin:password@host:5432/db?ssl=require
```

### Connection Pooling

```python
# For high-traffic production environments
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=60
```

---

## Redis Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | **Yes** | - | Redis connection string |
| `REDIS_MAX_CONNECTIONS` | No | `10` | Max pool connections |
| `REDIS_SOCKET_TIMEOUT` | No | `5` | Socket timeout (seconds) |

### Connection String Format

```bash
# Standard
REDIS_URL=redis://host:port/db

# With password
REDIS_URL=redis://:password@host:port/db

# AWS ElastiCache (TLS)
REDIS_URL=rediss://:password@cluster.xxx.cache.amazonaws.com:6379/0

# Examples
REDIS_URL=redis://localhost:6379/0
REDIS_URL=redis://:mypassword@redis.example.com:6379/0
```

### Redis Usage in ComplianceAgent

- **Cache**: API response caching, session data
- **Queue**: Celery task broker
- **Rate Limiting**: Request rate tracking

---

## Elasticsearch Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ELASTICSEARCH_URL` | No | `http://localhost:9200` | Elasticsearch URL |
| `ELASTICSEARCH_INDEX_PREFIX` | No | `complianceagent` | Index name prefix |
| `ELASTICSEARCH_TIMEOUT` | No | `30` | Request timeout (seconds) |

### Connection Examples

```bash
# Local
ELASTICSEARCH_URL=http://localhost:9200

# AWS OpenSearch
ELASTICSEARCH_URL=https://search-xxx.us-east-1.es.amazonaws.com

# With authentication
ELASTICSEARCH_URL=https://user:password@elasticsearch.example.com:9200
```

### Indices Created

| Index | Purpose |
|-------|---------|
| `complianceagent-regulations` | Regulatory document search |
| `complianceagent-requirements` | Requirement full-text search |
| `complianceagent-audit` | Audit log search |

---

## AI/Copilot Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COPILOT_API_KEY` | **Yes*** | - | GitHub Copilot SDK API key |
| `COPILOT_BASE_URL` | No | `https://api.githubcopilot.com` | Copilot API base URL |
| `COPILOT_DEFAULT_MODEL` | No | `gpt-4` | Default model for requests |
| `COPILOT_TIMEOUT_SECONDS` | No | `120` | Request timeout |
| `COPILOT_MAX_RETRIES` | No | `3` | Max retry attempts |
| `COPILOT_RETRY_MIN_WAIT` | No | `1` | Min retry wait (seconds) |
| `COPILOT_RETRY_MAX_WAIT` | No | `60` | Max retry wait (seconds) |

*Required for AI features; system works without but AI parsing/generation disabled.

### Retry Configuration

```bash
# For unreliable networks or high load
COPILOT_MAX_RETRIES=5
COPILOT_RETRY_MIN_WAIT=2
COPILOT_RETRY_MAX_WAIT=120
COPILOT_TIMEOUT_SECONDS=180
```

### Rate Limit Handling

The Copilot client automatically handles rate limits with exponential backoff. Configure limits based on your Copilot API tier:

```bash
# Conservative settings for lower-tier API access
COPILOT_MAX_RETRIES=5
COPILOT_RETRY_MAX_WAIT=120
```

---

## Authentication Configuration

### JWT Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | - | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `ALGORITHM` | No | `HS256` | JWT algorithm |

### Password Policy

| Variable | Default | Description |
|----------|---------|-------------|
| `PASSWORD_MIN_LENGTH` | `8` | Minimum password length |
| `PASSWORD_REQUIRE_UPPERCASE` | `true` | Require uppercase letter |
| `PASSWORD_REQUIRE_LOWERCASE` | `true` | Require lowercase letter |
| `PASSWORD_REQUIRE_DIGIT` | `true` | Require number |
| `PASSWORD_REQUIRE_SPECIAL` | `false` | Require special character |

### SAML/SSO Configuration (Enterprise)

| Variable | Required | Description |
|----------|----------|-------------|
| `SAML_ENABLED` | No | Enable SAML SSO |
| `SAML_IDP_METADATA_URL` | If SAML | IdP metadata URL |
| `SAML_SP_ENTITY_ID` | If SAML | Service provider entity ID |
| `SAML_ACS_URL` | If SAML | Assertion consumer service URL |

```bash
# Example SAML configuration
SAML_ENABLED=true
SAML_IDP_METADATA_URL=https://idp.example.com/metadata
SAML_SP_ENTITY_ID=https://complianceagent.example.com
SAML_ACS_URL=https://complianceagent.example.com/api/v1/auth/saml/acs
```

---

## GitHub Integration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_APP_ID` | For GitHub | - | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY` | For GitHub | - | App private key (PEM) |
| `GITHUB_WEBHOOK_SECRET` | For webhooks | - | Webhook signature secret |
| `GITHUB_API_BASE_URL` | No | `https://api.github.com` | GitHub API URL |

### Setting Up GitHub App

1. Create a GitHub App at https://github.com/settings/apps
2. Configure permissions:
   - **Contents**: Read
   - **Pull requests**: Read & Write
   - **Metadata**: Read
3. Generate and download private key
4. Set environment variables:

```bash
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

### For GitHub Enterprise

```bash
GITHUB_API_BASE_URL=https://github.mycompany.com/api/v3
```

---

## Billing Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STRIPE_API_KEY` | For billing | - | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | For billing | - | Stripe webhook secret |
| `STRIPE_PUBLISHABLE_KEY` | For billing | - | Stripe public key |

### Stripe Product IDs

```bash
STRIPE_PRICE_STARTER=price_xxx
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_xxx
STRIPE_PRICE_PROFESSIONAL_YEARLY=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx
```

---

## Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`) |
| `LOG_OUTPUT` | `stdout` | Output destination |

### Log Levels by Environment

```bash
# Development
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Production
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Structured Logging Fields

All logs include:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level
- `message`: Log message
- `service`: Service name
- `environment`: Environment name
- `trace_id`: Request trace ID (if applicable)

---

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `FEATURE_AI_GENERATION` | `true` | Enable AI code generation |
| `FEATURE_REGULATORY_MONITORING` | `true` | Enable auto-monitoring |
| `FEATURE_BILLING` | `false` | Enable billing features |
| `FEATURE_SSO` | `false` | Enable SSO/SAML |
| `FEATURE_WEBHOOKS` | `true` | Enable webhook delivery |

### Disabling Features

```bash
# Disable AI features (for testing without Copilot key)
FEATURE_AI_GENERATION=false

# Enable enterprise features
FEATURE_SSO=true
FEATURE_BILLING=true
```

---

## Environment-Specific Examples

### Development (.env)

```bash
# Core
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-not-for-production

# Database
DATABASE_URL=postgresql+asyncpg://complianceagent:complianceagent@localhost:5432/complianceagent

# Redis
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# AI (optional for dev)
COPILOT_API_KEY=your-dev-key

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Features
FEATURE_BILLING=false
FEATURE_SSO=false
```

### Production (.env)

```bash
# Core
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=${SECRET_KEY}  # From secrets manager

# Database
DATABASE_URL=${DATABASE_URL}  # From secrets manager

# Redis
REDIS_URL=${REDIS_URL}

# Elasticsearch
ELASTICSEARCH_URL=${ELASTICSEARCH_URL}

# AI
COPILOT_API_KEY=${COPILOT_API_KEY}
COPILOT_TIMEOUT_SECONDS=180
COPILOT_MAX_RETRIES=5

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Features
FEATURE_BILLING=true
FEATURE_SSO=true
```

---

## Secrets Management

### AWS Secrets Manager

```bash
# Store secrets
aws secretsmanager create-secret \
  --name complianceagent/production \
  --secret-string '{
    "SECRET_KEY": "...",
    "DATABASE_URL": "...",
    "COPILOT_API_KEY": "...",
    "STRIPE_API_KEY": "..."
  }'

# Reference in ECS task definition
# Secrets are injected as environment variables
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: complianceagent-secrets
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  DATABASE_URL: "postgresql+asyncpg://..."
  COPILOT_API_KEY: "..."
```

---

## Validation

The application validates configuration at startup. Missing required variables will prevent startup with a clear error message:

```
ConfigurationError: Missing required environment variable: SECRET_KEY
```

To validate your configuration without starting the server:

```bash
cd backend
python -c "from app.core.config import settings; print('Configuration valid!')"
```

---

## Next Steps

- [Getting Started Guide](getting-started.md) - Set up your development environment
- [Deployment Guide](../deployment/README.md) - Deploy to production
- [CI/CD Integration](cicd-integration.md) - Configure automated pipelines
