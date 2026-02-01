---
sidebar_position: 4
title: Environment Variables
description: Complete reference for all environment variables
---

# Environment Variables

Complete reference for all ComplianceAgent configuration options.

## Required Variables

These variables must be set for the application to start:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key (min 32 chars) | `your-secret-key-min-32-characters` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `GITHUB_TOKEN` | GitHub token for Copilot SDK | `ghp_xxxxxxxxxxxx` |

## Application Settings

### General

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format: `json` or `text` | `json` |
| `WORKERS` | Number of worker processes | `4` |
| `TIMEOUT` | Request timeout in seconds | `30` |

### Server

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |
| `TRUSTED_HOSTS` | Allowed hosts (comma-separated) | `*` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |
| `NEXT_PUBLIC_ENV` | Environment indicator | `development` |

## Database

### PostgreSQL

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full connection string | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `complianceagent` |
| `DB_USER` | Database user | `complianceagent` |
| `DB_PASSWORD` | Database password | - |
| `DB_POOL_SIZE` | Connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `20` |
| `DB_SSL_MODE` | SSL mode | `prefer` |

### Redis

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Full connection string | - |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_PASSWORD` | Redis password | - |
| `REDIS_DB` | Redis database number | `0` |
| `REDIS_SSL` | Enable SSL | `false` |

### Elasticsearch

| Variable | Description | Default |
|----------|-------------|---------|
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `ELASTICSEARCH_USER` | Elasticsearch user | - |
| `ELASTICSEARCH_PASSWORD` | Elasticsearch password | - |
| `ELASTICSEARCH_INDEX_PREFIX` | Index prefix | `complianceagent` |

## AI & Integrations

### GitHub Copilot SDK

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | - |
| `COPILOT_MODEL` | AI model to use | `gpt-4` |
| `COPILOT_MAX_TOKENS` | Max tokens per request | `4096` |
| `COPILOT_TEMPERATURE` | Model temperature | `0.3` |
| `COPILOT_TIMEOUT` | Request timeout | `60` |

### GitHub Integration

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_APP_ID` | GitHub App ID | - |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App private key | - |
| `GITHUB_WEBHOOK_SECRET` | Webhook secret | - |
| `GITHUB_API_URL` | GitHub API URL | `https://api.github.com` |

### Slack Integration

| Variable | Description | Default |
|----------|-------------|---------|
| `SLACK_WEBHOOK_URL` | Slack webhook URL | - |
| `SLACK_BOT_TOKEN` | Slack bot token | - |
| `SLACK_SIGNING_SECRET` | Slack signing secret | - |

## Security

### Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | JWT signing secret | Uses `SECRET_KEY` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRATION` | Token expiration (seconds) | `3600` |
| `JWT_REFRESH_EXPIRATION` | Refresh token expiration | `604800` |
| `SESSION_LIFETIME` | Session lifetime (seconds) | `86400` |

### OAuth / SSO

| Variable | Description | Default |
|----------|-------------|---------|
| `OAUTH_ENABLED` | Enable OAuth | `false` |
| `OAUTH_PROVIDER` | OAuth provider | - |
| `OAUTH_CLIENT_ID` | OAuth client ID | - |
| `OAUTH_CLIENT_SECRET` | OAuth client secret | - |
| `SAML_ENABLED` | Enable SAML SSO | `false` |
| `SAML_IDP_METADATA_URL` | SAML IdP metadata URL | - |

### Encryption

| Variable | Description | Default |
|----------|-------------|---------|
| `ENCRYPTION_KEY` | Data encryption key | - |
| `ENCRYPTION_ALGORITHM` | Encryption algorithm | `AES-256-GCM` |

## Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `FEATURE_AI_FIXES` | Enable AI-generated fixes | `true` |
| `FEATURE_AUTO_SCAN` | Enable automatic scanning | `true` |
| `FEATURE_WEBHOOKS` | Enable webhooks | `true` |
| `FEATURE_AUDIT_LOGS` | Enable audit logging | `true` |
| `FEATURE_MULTI_TENANT` | Enable multi-tenancy | `false` |

## Scanning Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SCAN_CONCURRENCY` | Concurrent scans | `5` |
| `SCAN_TIMEOUT` | Scan timeout (seconds) | `3600` |
| `SCAN_MAX_FILE_SIZE` | Max file size (bytes) | `10485760` |
| `SCAN_IGNORE_PATTERNS` | Files to ignore (comma-separated) | `node_modules,vendor,.git` |
| `SCAN_SCHEDULE` | Default scan schedule | `0 0 * * *` |

## Rate Limiting

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_REQUESTS` | Requests per window | `100` |
| `RATE_LIMIT_WINDOW` | Window size (seconds) | `60` |
| `RATE_LIMIT_BURST` | Burst limit | `20` |

## Monitoring

### Metrics

| Variable | Description | Default |
|----------|-------------|---------|
| `METRICS_ENABLED` | Enable metrics endpoint | `true` |
| `METRICS_PORT` | Metrics port | `9090` |
| `METRICS_PATH` | Metrics path | `/metrics` |

### Tracing

| Variable | Description | Default |
|----------|-------------|---------|
| `TRACING_ENABLED` | Enable distributed tracing | `false` |
| `TRACING_EXPORTER` | Tracing exporter | `jaeger` |
| `JAEGER_ENDPOINT` | Jaeger endpoint | `http://localhost:14268/api/traces` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP endpoint | - |

### Sentry

| Variable | Description | Default |
|----------|-------------|---------|
| `SENTRY_DSN` | Sentry DSN | - |
| `SENTRY_ENVIRONMENT` | Sentry environment | Uses `ENVIRONMENT` |
| `SENTRY_TRACES_SAMPLE_RATE` | Trace sample rate | `0.1` |

## Storage

### S3 / Object Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `S3_BUCKET` | S3 bucket name | - |
| `S3_REGION` | S3 region | `us-east-1` |
| `S3_ENDPOINT` | S3 endpoint (for MinIO) | - |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |

## Email

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP host | - |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `SMTP_FROM` | From email address | - |
| `SMTP_TLS` | Enable TLS | `true` |

## Development

| Variable | Description | Default |
|----------|-------------|---------|
| `RELOAD` | Enable auto-reload | `false` |
| `PROFILING` | Enable profiling | `false` |
| `SQL_ECHO` | Log SQL queries | `false` |
| `MOCK_GITHUB` | Mock GitHub API | `false` |

## Example .env File

```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-secret-key-min-32-characters-long
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4

# Database
DATABASE_URL=postgresql://complianceagent:password@localhost:5432/complianceagent

# Redis
REDIS_URL=redis://localhost:6379/0

# GitHub Copilot SDK
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
COPILOT_MODEL=gpt-4

# Security
JWT_EXPIRATION=3600
CORS_ORIGINS=https://compliance.example.com

# Features
FEATURE_AI_FIXES=true
FEATURE_AUTO_SCAN=true

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
METRICS_ENABLED=true
```

## Loading Environment Variables

### Docker Compose

```yaml
services:
  backend:
    env_file:
      - .env
      - .env.local
```

### Kubernetes

```yaml
envFrom:
  - configMapRef:
      name: complianceagent-config
  - secretRef:
      name: complianceagent-secrets
```

### Systemd

```ini
[Service]
EnvironmentFile=/etc/complianceagent/env
```

---

See also: [Configuration Guide](../getting-started/configuration) | [Docker Deployment](./docker)
