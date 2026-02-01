---
sidebar_position: 3
title: Configuration
description: Configure ComplianceAgent for your environment
---

# Configuration

ComplianceAgent is configured through environment variables. This page covers all available options.

## Configuration Methods

### Environment Variables

Set variables directly in your environment:

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/complianceagent"
export SECRET_KEY="your-secret-key"
```

### `.env` File

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/complianceagent
SECRET_KEY=your-secret-key
```

### Docker Compose

Configure in `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/complianceagent
      - SECRET_KEY=your-secret-key
```

## Required Configuration

These settings must be configured for ComplianceAgent to run:

### `SECRET_KEY`

**Required** | String | Min 32 characters

Used for JWT token signing and encryption.

```bash
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
```

Generate a secure key:
```bash
openssl rand -hex 32
```

:::danger Security Warning
Never commit your `SECRET_KEY` to version control. Use environment variables or secrets management in production.
:::

### `DATABASE_URL`

**Required** | Connection String

PostgreSQL connection URL.

```bash
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/complianceagent

# Production (with SSL)
DATABASE_URL=postgresql+asyncpg://user:pass@db.example.com:5432/complianceagent?sslmode=require
```

### `COPILOT_API_KEY`

**Required** for AI features | String

GitHub Copilot SDK API key for AI-powered parsing and code generation.

```bash
COPILOT_API_KEY=ghu_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Database Configuration

### `DATABASE_URL`

PostgreSQL connection string with async driver.

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
```

### `DATABASE_POOL_SIZE`

**Default:** `5` | Integer

Number of connections in the connection pool.

```bash
DATABASE_POOL_SIZE=10
```

### `DATABASE_MAX_OVERFLOW`

**Default:** `10` | Integer

Maximum overflow connections beyond pool size.

```bash
DATABASE_MAX_OVERFLOW=20
```

## Redis Configuration

### `REDIS_URL`

**Default:** `redis://localhost:6379/0` | Connection String

Redis connection URL for caching and Celery broker.

```bash
REDIS_URL=redis://localhost:6379/0

# With authentication
REDIS_URL=redis://:password@redis.example.com:6379/0
```

### `REDIS_CACHE_TTL`

**Default:** `3600` | Integer (seconds)

Default cache time-to-live.

```bash
REDIS_CACHE_TTL=7200  # 2 hours
```

## Elasticsearch Configuration

### `ELASTICSEARCH_URL`

**Default:** `http://localhost:9200` | URL

Elasticsearch endpoint for document search.

```bash
ELASTICSEARCH_URL=http://localhost:9200

# With authentication
ELASTICSEARCH_URL=https://user:pass@es.example.com:9243
```

### `ELASTICSEARCH_INDEX_PREFIX`

**Default:** `complianceagent` | String

Prefix for Elasticsearch indices.

```bash
ELASTICSEARCH_INDEX_PREFIX=prod_complianceagent
```

## Object Storage Configuration

### `S3_ENDPOINT_URL`

**Default:** `http://localhost:9000` | URL

S3-compatible storage endpoint.

```bash
# MinIO (local)
S3_ENDPOINT_URL=http://localhost:9000

# AWS S3 (leave empty to use default)
S3_ENDPOINT_URL=

# Other S3-compatible (DigitalOcean, Backblaze)
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
```

### `S3_ACCESS_KEY` / `S3_SECRET_KEY`

**Default:** `minioadmin` | String

S3 credentials.

```bash
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### `S3_BUCKET_NAME`

**Default:** `complianceagent` | String

Bucket for document storage.

```bash
S3_BUCKET_NAME=complianceagent-documents
```

## Authentication Configuration

### `JWT_ALGORITHM`

**Default:** `HS256` | String

JWT signing algorithm.

```bash
JWT_ALGORITHM=HS256
```

### `ACCESS_TOKEN_EXPIRE_MINUTES`

**Default:** `30` | Integer

Access token expiration time.

```bash
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### `REFRESH_TOKEN_EXPIRE_DAYS`

**Default:** `7` | Integer

Refresh token expiration time.

```bash
REFRESH_TOKEN_EXPIRE_DAYS=30
```

## GitHub Integration

### `GITHUB_APP_ID`

**Optional** | String

GitHub App ID for repository access.

```bash
GITHUB_APP_ID=123456
```

### `GITHUB_APP_PRIVATE_KEY`

**Optional** | String (PEM)

GitHub App private key (can be base64 encoded).

```bash
# Direct PEM content
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."

# Or base64 encoded
GITHUB_APP_PRIVATE_KEY_BASE64=LS0tLS1CRUdJTi...
```

### `GITHUB_WEBHOOK_SECRET`

**Optional** | String

Secret for validating GitHub webhooks.

```bash
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

## Enterprise Features

### SSO/SAML Configuration

#### `SAML_ENABLED`

**Default:** `false` | Boolean

Enable SAML SSO authentication.

```bash
SAML_ENABLED=true
```

#### `SAML_IDP_METADATA_URL`

**Required if SAML enabled** | URL

Identity Provider metadata URL.

```bash
SAML_IDP_METADATA_URL=https://idp.example.com/metadata.xml
```

#### `SAML_SP_ENTITY_ID`

**Required if SAML enabled** | String

Service Provider entity ID.

```bash
SAML_SP_ENTITY_ID=https://complianceagent.example.com/saml
```

### Billing (Stripe)

#### `STRIPE_API_KEY`

**Optional** | String

Stripe API key for billing features.

```bash
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
```

#### `STRIPE_WEBHOOK_SECRET`

**Optional** | String

Stripe webhook signing secret.

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx
```

## Monitoring & Observability

### `LOG_LEVEL`

**Default:** `INFO` | String

Application log level.

```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### `LOG_FORMAT`

**Default:** `json` | String

Log output format.

```bash
LOG_FORMAT=json  # json, text
```

### `SENTRY_DSN`

**Optional** | URL

Sentry error tracking DSN.

```bash
SENTRY_DSN=https://key@sentry.io/project
```

### `OTEL_EXPORTER_OTLP_ENDPOINT`

**Optional** | URL

OpenTelemetry collector endpoint.

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Environment-Specific Settings

### `ENVIRONMENT`

**Default:** `development` | String

Current environment.

```bash
ENVIRONMENT=production  # development, staging, production
```

### `DEBUG`

**Default:** `false` | Boolean

Enable debug mode (never in production).

```bash
DEBUG=false
```

### `CORS_ORIGINS`

**Default:** `["http://localhost:3000"]` | JSON Array

Allowed CORS origins.

```bash
CORS_ORIGINS=["https://app.complianceagent.com","https://staging.complianceagent.com"]
```

## Example Configurations

### Development

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/complianceagent
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200
S3_ENDPOINT_URL=http://localhost:9000

SECRET_KEY=dev-secret-key-not-for-production
COPILOT_API_KEY=your-dev-api-key
```

### Production

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

DATABASE_URL=postgresql+asyncpg://prod_user:${DB_PASSWORD}@db.internal:5432/complianceagent?sslmode=require
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

REDIS_URL=rediss://:${REDIS_PASSWORD}@redis.internal:6379/0
ELASTICSEARCH_URL=https://${ES_USER}:${ES_PASSWORD}@es.internal:9243

S3_BUCKET_NAME=complianceagent-prod
# Uses IAM roles, no explicit credentials needed

SECRET_KEY=${SECRET_KEY}
COPILOT_API_KEY=${COPILOT_API_KEY}

CORS_ORIGINS=["https://app.complianceagent.com"]

SENTRY_DSN=${SENTRY_DSN}
```

## Configuration Validation

ComplianceAgent validates configuration on startup. If required settings are missing or invalid, the application will fail to start with a clear error message:

```
Configuration Error: SECRET_KEY must be at least 32 characters
Configuration Error: DATABASE_URL is required
```

Check your configuration with:

```bash
# Backend
cd backend
python -c "from app.core.config import settings; print(settings)"

# Or via API
curl http://localhost:8000/health
```

---

Next: Learn about [Core Concepts](../core-concepts/overview) to understand how ComplianceAgent works.
