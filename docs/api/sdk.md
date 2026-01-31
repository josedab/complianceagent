# SDK Reference

ComplianceAgent provides official SDKs for Python and TypeScript/Node.js to interact with the API programmatically.

## Table of Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Python SDK](#python-sdk)
- [TypeScript SDK](#typescript-sdk)
- [Common Operations](#common-operations)
- [Error Handling](#error-handling)
- [Webhooks](#webhooks)
- [Rate Limiting](#rate-limiting)

---

## Installation

### Python

```bash
pip install complianceagent
```

Requirements: Python 3.10+

### TypeScript / Node.js

```bash
npm install @complianceagent/sdk
# or
yarn add @complianceagent/sdk
```

Requirements: Node.js 18+

---

## Authentication

Both SDKs require authentication via API tokens. Generate tokens from the dashboard or via the auth API.

### Python

```python
from complianceagent import ComplianceAgent

# Using API token (recommended for production)
client = ComplianceAgent(api_token="your-api-token")

# Or using email/password (creates a session)
client = ComplianceAgent(
    email="user@example.com",
    password="your-password",
    base_url="https://api.complianceagent.ai"  # Optional, defaults to production
)
```

### TypeScript

```typescript
import { ComplianceAgent } from '@complianceagent/sdk';

// Using API token
const client = new ComplianceAgent({
  apiToken: 'your-api-token',
});

// Or using email/password
const client = new ComplianceAgent({
  email: 'user@example.com',
  password: 'your-password',
  baseUrl: 'https://api.complianceagent.ai',
});

// Initialize (required for email/password auth)
await client.authenticate();
```

---

## Python SDK

### Organizations

```python
from complianceagent import ComplianceAgent

client = ComplianceAgent(api_token="...")

# List organizations
orgs = client.organizations.list()
for org in orgs:
    print(f"{org.name} - {org.plan}")

# Get specific organization
org = client.organizations.get("org-uuid")

# Create organization
new_org = client.organizations.create(
    name="Acme Corp",
    industry="technology",
    size="50-200"
)
```

### Regulations

```python
# List regulations
regulations = client.regulations.list(
    framework="gdpr",
    jurisdiction="eu",
    status="active"
)

# Get regulation details
regulation = client.regulations.get("reg-uuid")

# Get requirements for a regulation
requirements = client.regulations.get_requirements(
    regulation_id="reg-uuid",
    category="data_processing",
    obligation_type="must"
)
```

### Repositories

```python
# List repositories
repos = client.repositories.list()

# Add a repository
repo = client.repositories.add(
    full_name="myorg/myrepo",
    provider="github"
)

# Trigger analysis
analysis = client.repositories.analyze(
    repository_id="repo-uuid",
    frameworks=["gdpr", "ccpa"],
    full_scan=True
)

# Check analysis status
status = client.repositories.get_analysis_status(analysis.analysis_id)
print(f"Status: {status.status}, Progress: {status.progress}%")
```

### Compliance

```python
# Get compliance status
status = client.compliance.get_status(
    repository_id="repo-uuid",  # Optional
    framework="gdpr"  # Optional
)
print(f"Overall score: {status.overall_score}")
print(f"GDPR score: {status.by_framework['gdpr'].score}")

# Assess a mapping
assessment = client.compliance.assess_mapping("mapping-uuid")
for gap in assessment.gaps:
    print(f"[{gap.severity}] {gap.description}")
    print(f"  File: {gap.file_path}")
    print(f"  Suggestion: {gap.suggestion}")

# Generate compliant code
fix = client.compliance.generate_code(
    mapping_id="mapping-uuid",
    auto_create_pr=False
)
for file in fix.files:
    print(f"{file.operation.upper()}: {file.path}")
    print(file.content)

# Create PR with generated code
pr = client.compliance.create_pr(
    mapping_id="mapping-uuid",
    title=fix.pr_title,
    body=fix.pr_body,
    files=fix.files
)
print(f"PR created: {pr.url}")
```

### Audit

```python
# List audit entries
entries = client.audit.list(
    event_type="requirement_extracted",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
for entry in entries:
    print(f"{entry.timestamp}: {entry.event_description}")

# Verify audit chain integrity
verification = client.audit.verify_chain()
print(f"Chain valid: {verification.valid}")
print(f"Entries verified: {verification.entries_verified}")

# Export audit report
report = client.audit.export(
    format="pdf",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
with open("audit-report.pdf", "wb") as f:
    f.write(report.content)
```

### Async Support

The Python SDK supports async operations:

```python
import asyncio
from complianceagent import AsyncComplianceAgent

async def main():
    client = AsyncComplianceAgent(api_token="...")
    
    # All methods are async
    regulations = await client.regulations.list()
    
    # Concurrent operations
    tasks = [
        client.repositories.analyze(repo_id, frameworks=["gdpr"])
        for repo_id in repo_ids
    ]
    results = await asyncio.gather(*tasks)

asyncio.run(main())
```

---

## TypeScript SDK

### Organizations

```typescript
import { ComplianceAgent } from '@complianceagent/sdk';

const client = new ComplianceAgent({ apiToken: '...' });

// List organizations
const orgs = await client.organizations.list();
orgs.forEach(org => console.log(`${org.name} - ${org.plan}`));

// Get specific organization
const org = await client.organizations.get('org-uuid');

// Create organization
const newOrg = await client.organizations.create({
  name: 'Acme Corp',
  industry: 'technology',
  size: '50-200',
});
```

### Regulations

```typescript
// List regulations
const regulations = await client.regulations.list({
  framework: 'gdpr',
  jurisdiction: 'eu',
  status: 'active',
});

// Get regulation details
const regulation = await client.regulations.get('reg-uuid');

// Get requirements
const requirements = await client.regulations.getRequirements('reg-uuid', {
  category: 'data_processing',
  obligationType: 'must',
});
```

### Repositories

```typescript
// List repositories
const repos = await client.repositories.list();

// Add a repository
const repo = await client.repositories.add({
  fullName: 'myorg/myrepo',
  provider: 'github',
});

// Trigger analysis
const analysis = await client.repositories.analyze('repo-uuid', {
  frameworks: ['gdpr', 'ccpa'],
  fullScan: true,
});

// Wait for completion with polling
const result = await client.repositories.waitForAnalysis(analysis.analysisId, {
  pollInterval: 5000, // 5 seconds
  timeout: 300000, // 5 minutes
});
```

### Compliance

```typescript
// Get compliance status
const status = await client.compliance.getStatus({
  repositoryId: 'repo-uuid',
  framework: 'gdpr',
});
console.log(`Overall score: ${status.overallScore}`);

// Assess a mapping
const assessment = await client.compliance.assessMapping('mapping-uuid');
for (const gap of assessment.gaps) {
  console.log(`[${gap.severity}] ${gap.description}`);
}

// Generate compliant code
const fix = await client.compliance.generateCode('mapping-uuid', {
  autoCreatePr: false,
});

// Create PR
const pr = await client.compliance.createPr('mapping-uuid', {
  title: fix.prTitle,
  body: fix.prBody,
  files: fix.files,
});
console.log(`PR created: ${pr.url}`);
```

### Audit

```typescript
// List audit entries
const entries = await client.audit.list({
  eventType: 'requirement_extracted',
  startDate: '2024-01-01',
  endDate: '2024-01-31',
});

// Verify chain
const verification = await client.audit.verifyChain();
console.log(`Chain valid: ${verification.valid}`);

// Export report
const report = await client.audit.export({
  format: 'pdf',
  startDate: '2024-01-01',
  endDate: '2024-01-31',
});
fs.writeFileSync('audit-report.pdf', report.content);
```

### Type Definitions

The TypeScript SDK includes full type definitions:

```typescript
import type {
  Organization,
  Regulation,
  Requirement,
  Repository,
  ComplianceStatus,
  CodebaseMapping,
  ComplianceGap,
  AuditEntry,
  GeneratedCode,
} from '@complianceagent/sdk';

// All responses are typed
const regulation: Regulation = await client.regulations.get('uuid');
console.log(regulation.framework); // Fully typed
```

---

## Common Operations

### Batch Processing

**Python:**
```python
from complianceagent import ComplianceAgent
from concurrent.futures import ThreadPoolExecutor

client = ComplianceAgent(api_token="...")

# Batch analyze multiple repositories
repo_ids = ["uuid1", "uuid2", "uuid3"]

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(
            client.repositories.analyze,
            repo_id,
            frameworks=["gdpr"]
        )
        for repo_id in repo_ids
    ]
    results = [f.result() for f in futures]
```

**TypeScript:**
```typescript
const repoIds = ['uuid1', 'uuid2', 'uuid3'];

// Batch analyze
const results = await Promise.all(
  repoIds.map(id => 
    client.repositories.analyze(id, { frameworks: ['gdpr'] })
  )
);
```

### Pagination

**Python:**
```python
# Manual pagination
page = 1
all_regulations = []
while True:
    result = client.regulations.list(page=page, per_page=50)
    all_regulations.extend(result.items)
    if page >= result.total_pages:
        break
    page += 1

# Or use iterator
for regulation in client.regulations.iter_all():
    print(regulation.name)
```

**TypeScript:**
```typescript
// Manual pagination
let page = 1;
let allRegulations: Regulation[] = [];
while (true) {
  const result = await client.regulations.list({ page, perPage: 50 });
  allRegulations.push(...result.items);
  if (page >= result.totalPages) break;
  page++;
}

// Or use async iterator
for await (const regulation of client.regulations.iterAll()) {
  console.log(regulation.name);
}
```

---

## Error Handling

### Python

```python
from complianceagent import (
    ComplianceAgent,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
    APIError,
)

client = ComplianceAgent(api_token="...")

try:
    regulation = client.regulations.get("invalid-uuid")
except ResourceNotFoundError as e:
    print(f"Regulation not found: {e}")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation error: {e.errors}")
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

### TypeScript

```typescript
import {
  ComplianceAgent,
  AuthenticationError,
  RateLimitError,
  ResourceNotFoundError,
  ValidationError,
  APIError,
} from '@complianceagent/sdk';

const client = new ComplianceAgent({ apiToken: '...' });

try {
  const regulation = await client.regulations.get('invalid-uuid');
} catch (error) {
  if (error instanceof ResourceNotFoundError) {
    console.error(`Not found: ${error.message}`);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after: ${error.retryAfter}s`);
  } else if (error instanceof ValidationError) {
    console.error(`Validation: ${error.errors}`);
  } else if (error instanceof APIError) {
    console.error(`API error: ${error.statusCode} - ${error.message}`);
  } else {
    throw error;
  }
}
```

---

## Webhooks

Configure webhooks to receive real-time notifications:

### Webhook Events

| Event | Description |
|-------|-------------|
| `regulation.updated` | Regulatory source changed |
| `requirement.extracted` | New requirements extracted |
| `compliance.gap_detected` | Compliance gap found |
| `compliance.pr_created` | PR created for fix |
| `analysis.completed` | Repository analysis finished |

### Webhook Payload

```json
{
  "event": "compliance.gap_detected",
  "timestamp": "2024-01-15T10:30:00Z",
  "organization_id": "uuid",
  "data": {
    "repository": "acme/backend-api",
    "requirement_id": "uuid",
    "severity": "critical",
    "description": "Missing GDPR consent mechanism"
  }
}
```

### Signature Verification

**Python:**
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

# In your webhook handler
@app.post("/webhooks/complianceagent")
async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-ComplianceAgent-Signature")
    
    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(401, "Invalid signature")
    
    event = json.loads(payload)
    # Process event...
```

**TypeScript:**
```typescript
import crypto from 'crypto';

function verifyWebhook(
  payload: Buffer,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(`sha256=${expected}`),
    Buffer.from(signature)
  );
}

// Express handler
app.post('/webhooks/complianceagent', (req, res) => {
  const signature = req.headers['x-complianceagent-signature'] as string;
  
  if (!verifyWebhook(req.body, signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }
  
  const event = JSON.parse(req.body);
  // Process event...
});
```

---

## Rate Limiting

The API enforces rate limits based on your subscription plan:

| Plan | Requests/Minute | Burst |
|------|-----------------|-------|
| Starter | 60 | 100 |
| Professional | 300 | 500 |
| Enterprise | 1000 | 2000 |

### Handling Rate Limits

**Python:**
```python
from complianceagent import ComplianceAgent, RateLimitError
import time

client = ComplianceAgent(api_token="...")

def with_retry(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = e.retry_after or (2 ** attempt)
            time.sleep(wait_time)

# Use with retry
result = with_retry(client.regulations.list)
```

**TypeScript:**
```typescript
import { ComplianceAgent, RateLimitError } from '@complianceagent/sdk';

const client = new ComplianceAgent({ apiToken: '...' });

async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error instanceof RateLimitError && attempt < maxRetries - 1) {
        const waitTime = error.retryAfter || Math.pow(2, attempt);
        await new Promise(r => setTimeout(r, waitTime * 1000));
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}

// Use with retry
const result = await withRetry(() => client.regulations.list());
```

---

## Next Steps

- View the [API Reference](reference.md) for complete endpoint documentation
- Check [Examples](../examples/) for more code samples
- Read the [Architecture Overview](../architecture/overview.md) to understand the system
