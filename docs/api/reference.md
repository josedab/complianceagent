# ComplianceAgent API Reference

This document provides a comprehensive reference for the ComplianceAgent REST API.

## Base URL

```
Production: https://api.complianceagent.ai/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

All API endpoints (except `/auth/register` and `/auth/login`) require authentication via JWT tokens.

### Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Token Lifecycle

- **Access Token**: Valid for 30 minutes (configurable)
- **Refresh Token**: Valid for 7 days (configurable)

When an access token expires, use the refresh endpoint to obtain a new one without re-authenticating.

---

## Endpoints

### Authentication

#### Register User

```http
POST /auth/register
```

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Login

```http
POST /auth/login
```

Authenticate and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Refresh Token

```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Get Current User

```http
GET /auth/me
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "organizations": [
    {
      "id": "uuid",
      "name": "Acme Corp",
      "role": "admin"
    }
  ]
}
```

---

### Organizations

#### List Organizations

```http
GET /organizations
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (default: 20, max: 100) |
| `offset` | int | Pagination offset |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "plan": "professional",
      "created_at": "2024-01-10T00:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Create Organization

```http
POST /organizations
```

**Request Body:**
```json
{
  "name": "Acme Corp",
  "industry": "technology",
  "size": "50-200"
}
```

#### Get Organization

```http
GET /organizations/{organization_id}
```

---

### Regulations

#### List Regulations

```http
GET /regulations
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `framework` | string | Filter by framework (gdpr, ccpa, hipaa, etc.) |
| `jurisdiction` | string | Filter by jurisdiction (eu, us-ca, us-federal, etc.) |
| `status` | string | Filter by status (active, draft, superseded) |
| `limit` | int | Max results |
| `offset` | int | Pagination offset |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "General Data Protection Regulation",
      "short_name": "GDPR",
      "framework": "gdpr",
      "jurisdiction": "eu",
      "effective_date": "2018-05-25",
      "status": "active",
      "requirements_count": 147
    }
  ],
  "total": 25,
  "limit": 20,
  "offset": 0
}
```

#### Get Regulation

```http
GET /regulations/{regulation_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "General Data Protection Regulation",
  "short_name": "GDPR",
  "framework": "gdpr",
  "jurisdiction": "eu",
  "effective_date": "2018-05-25",
  "status": "active",
  "description": "EU regulation on data protection and privacy...",
  "source_url": "https://eur-lex.europa.eu/...",
  "requirements_count": 147,
  "last_updated": "2024-01-15T10:00:00Z"
}
```

#### Get Regulation Requirements

```http
GET /regulations/{regulation_id}/requirements
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category |
| `obligation_type` | string | Filter by obligation (must, should, may) |
| `limit` | int | Max results |
| `offset` | int | Pagination offset |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "reference_id": "REQ-GDPR-001",
      "title": "Lawful Basis for Processing",
      "description": "Personal data shall be processed lawfully...",
      "obligation_type": "must",
      "category": "data_processing",
      "subject": "data controller",
      "action": "establish lawful basis",
      "citations": [
        {"article": "6", "section": "1"}
      ],
      "confidence": 0.95
    }
  ],
  "total": 147
}
```

---

### Repositories

#### List Repositories

```http
GET /repositories
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "full_name": "acme/backend-api",
      "provider": "github",
      "default_branch": "main",
      "primary_language": "Python",
      "languages": ["Python", "TypeScript"],
      "compliance_score": 78,
      "last_analyzed": "2024-01-15T12:00:00Z"
    }
  ]
}
```

#### Add Repository

```http
POST /repositories
```

**Request Body:**
```json
{
  "full_name": "acme/backend-api",
  "provider": "github"
}
```

#### Trigger Analysis

```http
POST /repositories/{repository_id}/analyze
```

Trigger a compliance analysis for the repository.

**Request Body:**
```json
{
  "frameworks": ["gdpr", "ccpa"],
  "full_scan": false
}
```

**Response:** `202 Accepted`
```json
{
  "analysis_id": "uuid",
  "status": "queued",
  "estimated_duration_minutes": 5
}
```

---

### Compliance

#### Get Compliance Status

```http
GET /compliance/status
```

Get overall compliance status for the organization.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | uuid | Filter by repository |
| `framework` | string | Filter by framework |

**Response:** `200 OK`
```json
{
  "overall_score": 82,
  "by_framework": {
    "gdpr": {
      "score": 85,
      "requirements_met": 125,
      "requirements_total": 147,
      "critical_gaps": 2
    },
    "ccpa": {
      "score": 78,
      "requirements_met": 45,
      "requirements_total": 58,
      "critical_gaps": 1
    }
  },
  "by_repository": [
    {
      "repository": "acme/backend-api",
      "score": 80,
      "last_analyzed": "2024-01-15T12:00:00Z"
    }
  ]
}
```

#### Assess Mapping Impact

```http
POST /compliance/assess/{mapping_id}
```

Assess the compliance impact of a specific code-to-requirement mapping.

**Response:** `200 OK`
```json
{
  "mapping_id": "uuid",
  "requirement": {
    "reference_id": "REQ-GDPR-015",
    "title": "Data Subject Access Rights"
  },
  "status": "partial",
  "gaps": [
    {
      "severity": "major",
      "description": "Missing automated data export functionality",
      "file_path": "src/api/users.py",
      "suggestion": "Implement data portability endpoint"
    }
  ],
  "existing_implementations": [
    {
      "path": "src/api/users.py",
      "description": "User data retrieval endpoint exists",
      "coverage": 0.6
    }
  ],
  "estimated_effort_hours": 16
}
```

#### Generate Compliant Code

```http
POST /compliance/generate
```

Generate code to address compliance gaps.

**Request Body:**
```json
{
  "mapping_id": "uuid",
  "auto_create_pr": false
}
```

**Response:** `200 OK`
```json
{
  "files": [
    {
      "path": "src/api/data_export.py",
      "operation": "create",
      "content": "...",
      "language": "python"
    }
  ],
  "tests": [
    {
      "path": "tests/test_data_export.py",
      "test_type": "unit",
      "content": "..."
    }
  ],
  "pr_title": "feat(compliance): Add GDPR data portability endpoint",
  "pr_body": "## Summary\n\nThis PR addresses REQ-GDPR-015...",
  "confidence": 0.85
}
```

#### List Compliance Actions

```http
GET /compliance/actions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (pending, in_progress, completed, failed) |
| `priority` | string | Filter by priority (critical, high, medium, low) |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "code_fix",
      "status": "pending",
      "priority": "high",
      "requirement": {
        "reference_id": "REQ-GDPR-015",
        "title": "Data Subject Access Rights"
      },
      "repository": "acme/backend-api",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

### Audit

#### List Audit Entries

```http
GET /audit/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | string | Filter by event type |
| `actor_type` | string | Filter by actor (user, system, ai) |
| `start_date` | datetime | Filter from date |
| `end_date` | datetime | Filter to date |
| `limit` | int | Max results |
| `offset` | int | Pagination offset |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "uuid",
      "event_type": "requirement_extracted",
      "event_description": "Extracted 45 requirements from GDPR",
      "actor_type": "ai",
      "ai_model": "copilot",
      "ai_confidence": 0.92,
      "timestamp": "2024-01-15T10:30:00Z",
      "hash": "sha256:abc123..."
    }
  ],
  "total": 1250
}
```

#### Verify Hash Chain

```http
GET /audit/verify-chain
```

Verify the integrity of the audit trail hash chain.

**Response:** `200 OK`
```json
{
  "valid": true,
  "entries_verified": 1250,
  "first_entry": "2024-01-01T00:00:00Z",
  "last_entry": "2024-01-15T10:30:00Z"
}
```

#### Export Audit Report

```http
GET /audit/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Export format (json, csv, pdf) |
| `start_date` | datetime | Start date |
| `end_date` | datetime | End date |

**Response:** `200 OK` (file download)

---

### Billing

#### List Plans

```http
GET /billing/plans
```

**Response:** `200 OK`
```json
{
  "plans": [
    {
      "id": "starter",
      "name": "Starter",
      "price_monthly": 0,
      "price_yearly": 0,
      "features": ["3 repositories", "2 frameworks", "Basic compliance reports"]
    },
    {
      "id": "professional",
      "name": "Professional",
      "price_monthly": 99,
      "price_yearly": 990,
      "features": ["Unlimited repositories", "All frameworks", "AI code generation"]
    },
    {
      "id": "enterprise",
      "name": "Enterprise",
      "price_monthly": null,
      "price_yearly": null,
      "features": ["Everything in Professional", "SSO/SAML", "Dedicated support"]
    }
  ]
}
```

#### Get Subscription

```http
GET /billing/subscription
```

#### Create Checkout Session

```http
POST /billing/checkout
```

**Request Body:**
```json
{
  "plan_id": "professional",
  "billing_cycle": "yearly"
}
```

**Response:** `200 OK`
```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation queued) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (resource already exists) |
| 422 | Unprocessable Entity |
| 429 | Rate Limited |
| 500 | Internal Server Error |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `TOKEN_EXPIRED` | JWT token has expired |
| `PERMISSION_DENIED` | User lacks required permission |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RATE_LIMITED` | Too many requests |
| `EXTERNAL_SERVICE_ERROR` | GitHub/Copilot API error |

---

## Rate Limiting

API requests are rate limited per organization:

| Plan | Requests/Minute | Burst |
|------|-----------------|-------|
| Starter | 60 | 100 |
| Professional | 300 | 500 |
| Enterprise | 1000 | 2000 |

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1705323600
```

---

## Webhooks

ComplianceAgent can send webhooks for key events. Configure webhook endpoints in the dashboard.

### Events

| Event | Description |
|-------|-------------|
| `regulation.updated` | Regulatory source changed |
| `requirement.extracted` | New requirements extracted |
| `compliance.gap_detected` | Compliance gap found |
| `compliance.pr_created` | PR created for fix |
| `analysis.completed` | Repository analysis finished |

### Payload Format

```json
{
  "event": "compliance.gap_detected",
  "timestamp": "2024-01-15T10:30:00Z",
  "organization_id": "uuid",
  "data": {
    "repository": "acme/backend-api",
    "requirement_id": "uuid",
    "severity": "critical"
  }
}
```

### Signature Verification

Webhooks include an `X-ComplianceAgent-Signature` header for verification:

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## SDKs

Official SDKs are available:

- **Python**: `pip install complianceagent`
- **TypeScript/Node**: `npm install @complianceagent/sdk`

See the [SDK documentation](./sdk.md) for usage examples.
