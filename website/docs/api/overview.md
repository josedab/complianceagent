---
sidebar_position: 1
title: API Overview
description: ComplianceAgent REST API reference
---

# API Reference

ComplianceAgent provides a comprehensive REST API for programmatic access to all features.

## Base URL

```
# Cloud
https://api.complianceagent.io/v1

# Self-hosted
http://localhost:8000/api/v1
```

## Authentication

All API requests require authentication via Bearer token:

```bash
curl -X GET "https://api.complianceagent.io/v1/regulations" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY"
```

See [Authentication](./authentication) for details on obtaining and managing API keys.

## Response Format

All responses use JSON format:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Repository not found",
    "details": {
      "repository_id": "invalid-id"
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Pagination

List endpoints support pagination:

```bash
GET /api/v1/regulations?page=1&limit=20
```

Response includes pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 127,
    "total_pages": 7,
    "has_next": true,
    "has_prev": false
  }
}
```

## Rate Limits

| Plan | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Pro | 300 | 50,000 |
| Enterprise | Unlimited | Unlimited |

Rate limit headers:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1705315800
```

## API Endpoints

### Core Resources

| Resource | Endpoint | Description |
|----------|----------|-------------|
| [Regulations](./regulations) | `/regulations` | Regulatory frameworks and requirements |
| [Repositories](./repositories) | `/repositories` | Connected code repositories |
| [Compliance](./compliance) | `/compliance` | Compliance status and issues |
| [Audit](./audit) | `/audit` | Audit logs and evidence |
| [Billing](./billing) | `/billing` | Subscription and usage |

### Quick Reference

#### Regulations

```bash
# List all regulations
GET /api/v1/regulations

# Get specific regulation
GET /api/v1/regulations/{id}

# Get regulation requirements
GET /api/v1/regulations/{id}/requirements

# Search regulations
GET /api/v1/regulations/search?q=privacy
```

#### Repositories

```bash
# List connected repositories
GET /api/v1/repositories

# Connect a repository
POST /api/v1/repositories

# Get repository compliance status
GET /api/v1/repositories/{id}/compliance

# Scan repository
POST /api/v1/repositories/{id}/scan
```

#### Compliance

```bash
# Get compliance dashboard
GET /api/v1/compliance/dashboard

# Get compliance issues
GET /api/v1/compliance/issues

# Generate fix for issue
POST /api/v1/compliance/issues/{id}/generate-fix

# Apply fix to repository
POST /api/v1/compliance/issues/{id}/apply-fix
```

#### Audit

```bash
# Get audit logs
GET /api/v1/audit/logs

# Export evidence package
GET /api/v1/audit/evidence/export

# Get compliance history
GET /api/v1/audit/history
```

## SDKs

Official SDKs available:

```bash
# Python
pip install complianceagent

# JavaScript/TypeScript  
npm install @complianceagent/sdk

# Go
go get github.com/complianceagent/go-sdk
```

Python SDK example:

```python
from complianceagent import Client

client = Client(api_key="your_api_key")

# Get compliance status
status = client.compliance.get_status(repository_id="repo_123")
print(f"Compliance score: {status.score}%")

# List issues
issues = client.compliance.list_issues(
    repository_id="repo_123",
    severity="critical"
)
for issue in issues:
    print(f"[{issue.framework}] {issue.title}")
```

TypeScript SDK example:

```typescript
import { ComplianceAgentClient } from '@complianceagent/sdk';

const client = new ComplianceAgentClient({
  apiKey: process.env.COMPLIANCEAGENT_API_KEY!
});

// Get compliance status
const status = await client.compliance.getStatus({
  repositoryId: 'repo_123'
});
console.log(`Compliance score: ${status.score}%`);

// Generate fix
const fix = await client.compliance.generateFix({
  issueId: 'issue_456'
});
console.log(fix.patch);
```

## Webhooks

Configure webhooks for real-time notifications:

```bash
POST /api/v1/webhooks
{
  "url": "https://your-app.com/webhooks/complianceagent",
  "events": [
    "regulation.updated",
    "compliance.issue_created",
    "compliance.status_changed",
    "scan.completed"
  ],
  "secret": "your_webhook_secret"
}
```

Webhook payload:

```json
{
  "event": "compliance.issue_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "issue_id": "issue_123",
    "repository_id": "repo_456",
    "framework": "gdpr",
    "requirement_id": "art_17",
    "severity": "high"
  }
}
```

Verify webhook signatures:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid API key |
| `INSUFFICIENT_PERMISSIONS` | 403 | API key lacks required scope |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request parameters |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Idempotency

For POST requests, include an idempotency key:

```bash
curl -X POST "https://api.complianceagent.io/v1/repositories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: unique-request-id-123" \
  -d '{"url": "https://github.com/acme/app"}'
```

Repeated requests with the same key return the same response.

---

Explore specific API endpoints:

- [Authentication](./authentication)
- [Regulations](./regulations)
- [Repositories](./repositories)
- [Compliance](./compliance)
- [Audit](./audit)
- [Billing](./billing)
