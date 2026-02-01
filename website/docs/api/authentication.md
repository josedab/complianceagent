---
sidebar_position: 2
title: Authentication
description: API authentication and authorization
---

# Authentication

ComplianceAgent uses API keys for authentication. All API requests must include a valid API key.

## API Keys

### Creating an API Key

```bash
# Via API (requires existing authentication)
POST /api/v1/auth/api-keys
{
  "name": "Production API Key",
  "scopes": ["read:compliance", "write:compliance", "read:audit"],
  "expires_at": "2025-01-01T00:00:00Z"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "key_abc123",
    "name": "Production API Key",
    "key": "ca_live_sk_abc123...",
    "scopes": ["read:compliance", "write:compliance", "read:audit"],
    "created_at": "2024-01-15T10:00:00Z",
    "expires_at": "2025-01-01T00:00:00Z"
  }
}
```

:::warning Store Your Key Securely
The full API key is only shown once. Store it securely—you cannot retrieve it later.
:::

### Using an API Key

Include the key in the `Authorization` header:

```bash
curl -X GET "https://api.complianceagent.io/v1/compliance/status" \
  -H "Authorization: Bearer ca_live_sk_abc123..."
```

Or using the SDK:

```python
from complianceagent import Client

client = Client(api_key="ca_live_sk_abc123...")
```

### Key Prefixes

| Prefix | Environment | Usage |
|--------|-------------|-------|
| `ca_live_sk_` | Production | Live API calls |
| `ca_test_sk_` | Sandbox | Testing and development |

## Scopes

API keys are scoped to limit access:

| Scope | Description |
|-------|-------------|
| `read:regulations` | Read regulatory frameworks |
| `read:repositories` | Read repository information |
| `write:repositories` | Connect/disconnect repositories |
| `read:compliance` | Read compliance status and issues |
| `write:compliance` | Apply fixes, acknowledge issues |
| `read:audit` | Read audit logs |
| `write:audit` | Export evidence packages |
| `admin` | Full administrative access |

Request only the scopes you need:

```bash
POST /api/v1/auth/api-keys
{
  "name": "CI/CD Key",
  "scopes": ["read:compliance", "write:compliance"]
}
```

## Key Management

### List API Keys

```bash
GET /api/v1/auth/api-keys
```

Response:

```json
{
  "data": [
    {
      "id": "key_abc123",
      "name": "Production API Key",
      "prefix": "ca_live_sk_abc1...",
      "scopes": ["read:compliance", "write:compliance"],
      "last_used_at": "2024-01-15T09:30:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "expires_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### Revoke an API Key

```bash
DELETE /api/v1/auth/api-keys/{key_id}
```

### Rotate an API Key

```bash
POST /api/v1/auth/api-keys/{key_id}/rotate
```

Response:

```json
{
  "data": {
    "id": "key_abc123",
    "key": "ca_live_sk_xyz789...",
    "previous_key_valid_until": "2024-01-15T11:00:00Z"
  }
}
```

The previous key remains valid for 1 hour to allow graceful rotation.

## OAuth 2.0

For user-facing integrations, use OAuth 2.0:

### Authorization Code Flow

1. Redirect user to authorization:

```
https://auth.complianceagent.io/oauth/authorize?
  client_id=your_client_id&
  redirect_uri=https://your-app.com/callback&
  response_type=code&
  scope=read:compliance+write:compliance&
  state=random_state_value
```

2. Exchange code for token:

```bash
POST https://auth.complianceagent.io/oauth/token
{
  "grant_type": "authorization_code",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "code": "authorization_code",
  "redirect_uri": "https://your-app.com/callback"
}
```

3. Use the access token:

```bash
curl -X GET "https://api.complianceagent.io/v1/compliance/status" \
  -H "Authorization: Bearer access_token_here"
```

### Refresh Tokens

```bash
POST https://auth.complianceagent.io/oauth/token
{
  "grant_type": "refresh_token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "refresh_token": "refresh_token_here"
}
```

## Service Accounts

For server-to-server communication:

```bash
POST /api/v1/auth/service-accounts
{
  "name": "CI/CD Service Account",
  "scopes": ["read:compliance", "write:compliance"]
}
```

Response:

```json
{
  "data": {
    "id": "sa_abc123",
    "name": "CI/CD Service Account",
    "client_id": "sa_abc123",
    "client_secret": "secret_xyz789..."
  }
}
```

Authenticate using client credentials:

```bash
POST https://auth.complianceagent.io/oauth/token
{
  "grant_type": "client_credentials",
  "client_id": "sa_abc123",
  "client_secret": "secret_xyz789..."
}
```

## Security Best Practices

### Environment Variables

Never hardcode API keys:

```bash
# Set in environment
export COMPLIANCEAGENT_API_KEY="ca_live_sk_abc123..."
```

```python
import os
from complianceagent import Client

client = Client(api_key=os.environ["COMPLIANCEAGENT_API_KEY"])
```

### Key Rotation

Rotate keys periodically:

```python
# Automated rotation script
import schedule
from complianceagent import Client

def rotate_api_key():
    client = Client(api_key=os.environ["COMPLIANCEAGENT_API_KEY"])
    
    new_key = client.auth.rotate_key(
        key_id=os.environ["COMPLIANCEAGENT_KEY_ID"]
    )
    
    # Update secret manager
    update_secret("COMPLIANCEAGENT_API_KEY", new_key.key)

schedule.every(30).days.do(rotate_api_key)
```

### Audit Key Usage

Monitor key usage for anomalies:

```bash
GET /api/v1/auth/api-keys/{key_id}/usage
```

Response:

```json
{
  "data": {
    "requests_last_24h": 1523,
    "requests_last_7d": 8234,
    "endpoints_accessed": [
      "/compliance/status",
      "/compliance/issues",
      "/repositories"
    ],
    "ip_addresses": [
      "203.0.113.1",
      "203.0.113.2"
    ]
  }
}
```

## Error Responses

### Invalid API Key

```json
{
  "success": false,
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Invalid or expired API key"
  }
}
```

### Insufficient Scopes

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "API key lacks required scope: write:compliance",
    "details": {
      "required_scope": "write:compliance",
      "key_scopes": ["read:compliance"]
    }
  }
}
```

### Rate Limited

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 300,
      "reset_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

---

See also: [API Overview](./overview) | [Webhooks](./overview#webhooks)
