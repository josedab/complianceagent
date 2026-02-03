---
sidebar_position: 1.5
title: API Quick Start
description: Get started with the ComplianceAgent API in minutes
---

# API Quick Start

Get up and running with the ComplianceAgent API in 5 minutes.

## Prerequisites

1. ComplianceAgent account ([sign up free](https://app.complianceagent.io/signup))
2. API key from Settings → API Keys
3. At least one connected repository

## Installation

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs groupId="language">
<TabItem value="python" label="Python">

```bash
pip install complianceagent
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```bash
npm install @complianceagent/sdk
```

</TabItem>
<TabItem value="go" label="Go">

```bash
go get github.com/complianceagent/go-sdk
```

</TabItem>
<TabItem value="curl" label="cURL">

No installation required - use your terminal.

</TabItem>
</Tabs>

## Initialize the Client

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
import os
from complianceagent import Client

client = Client(api_key=os.environ["COMPLIANCEAGENT_API_KEY"])
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```typescript
import { ComplianceAgentClient } from '@complianceagent/sdk';

const client = new ComplianceAgentClient({
  apiKey: process.env.COMPLIANCEAGENT_API_KEY!,
});
```

</TabItem>
<TabItem value="go" label="Go">

```go
package main

import (
    "os"
    complianceagent "github.com/complianceagent/go-sdk"
)

func main() {
    client := complianceagent.NewClient(os.Getenv("COMPLIANCEAGENT_API_KEY"))
}
```

</TabItem>
<TabItem value="curl" label="cURL">

```bash
# Set your API key
export COMPLIANCEAGENT_API_KEY="ca_live_sk_..."
```

</TabItem>
</Tabs>

---

## Common Use Cases

### 1. Get Compliance Status

Check your organization's overall compliance score.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# Get overall compliance status
status = client.compliance.get_dashboard()

print(f"Overall Score: {status.overall_score}%")
print(f"Critical Issues: {status.issues.critical}")
print(f"Repositories at Risk: {status.repositories.at_risk}")

# Check specific framework
for framework in status.frameworks:
    print(f"  {framework.name}: {framework.score}%")
```

**Output:**
```
Overall Score: 85%
Critical Issues: 3
Repositories at Risk: 2
  GDPR: 82%
  SOC 2: 91%
  HIPAA: 78%
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```typescript
// Get overall compliance status
const status = await client.compliance.getDashboard();

console.log(`Overall Score: ${status.overallScore}%`);
console.log(`Critical Issues: ${status.issues.critical}`);
console.log(`Repositories at Risk: ${status.repositories.atRisk}`);

// Check specific framework
for (const framework of status.frameworks) {
  console.log(`  ${framework.name}: ${framework.score}%`);
}
```

</TabItem>
<TabItem value="go" label="Go">

```go
// Get overall compliance status
status, err := client.Compliance.GetDashboard(ctx)
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Overall Score: %d%%\n", status.OverallScore)
fmt.Printf("Critical Issues: %d\n", status.Issues.Critical)

for _, fw := range status.Frameworks {
    fmt.Printf("  %s: %d%%\n", fw.Name, fw.Score)
}
```

</TabItem>
<TabItem value="curl" label="cURL">

```bash
curl -X GET "https://api.complianceagent.io/v1/compliance/dashboard" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY" | jq
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_score": 85,
    "issues": { "critical": 3, "high": 12, "medium": 22 },
    "repositories": { "total": 5, "at_risk": 2 },
    "frameworks": [
      { "id": "gdpr", "name": "GDPR", "score": 82 },
      { "id": "soc2", "name": "SOC 2", "score": 91 }
    ]
  }
}
```

</TabItem>
</Tabs>

---

### 2. List Compliance Issues

Find issues that need attention.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# Get critical and high severity issues
issues = client.compliance.list_issues(
    severity=["critical", "high"],
    status="open",
    limit=10
)

for issue in issues:
    print(f"[{issue.severity.upper()}] {issue.title}")
    print(f"  Repository: {issue.repository.name}")
    print(f"  File: {issue.location.file_path}:{issue.location.line_start}")
    print(f"  Framework: {issue.framework}")
    print(f"  Fix available: {'Yes' if issue.fix_available else 'No'}")
    print()
```

**Output:**
```
[CRITICAL] Missing encryption for PII at rest
  Repository: acme/web-app
  File: src/models/user.py:45
  Framework: GDPR
  Fix available: Yes

[HIGH] Insufficient access logging
  Repository: acme/api
  File: src/middleware/auth.py:23
  Framework: SOC 2
  Fix available: Yes
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```typescript
// Get critical and high severity issues
const issues = await client.compliance.listIssues({
  severity: ['critical', 'high'],
  status: 'open',
  limit: 10,
});

for (const issue of issues.data) {
  console.log(`[${issue.severity.toUpperCase()}] ${issue.title}`);
  console.log(`  Repository: ${issue.repository.name}`);
  console.log(`  File: ${issue.location.filePath}:${issue.location.lineStart}`);
  console.log(`  Framework: ${issue.framework}`);
  console.log(`  Fix available: ${issue.fixAvailable ? 'Yes' : 'No'}`);
  console.log();
}
```

</TabItem>
<TabItem value="go" label="Go">

```go
// Get critical and high severity issues
issues, err := client.Compliance.ListIssues(ctx, &complianceagent.IssuesFilter{
    Severity: []string{"critical", "high"},
    Status:   "open",
    Limit:    10,
})
if err != nil {
    log.Fatal(err)
}

for _, issue := range issues.Data {
    fmt.Printf("[%s] %s\n", strings.ToUpper(issue.Severity), issue.Title)
    fmt.Printf("  Repository: %s\n", issue.Repository.Name)
    fmt.Printf("  File: %s:%d\n", issue.Location.FilePath, issue.Location.LineStart)
}
```

</TabItem>
<TabItem value="curl" label="cURL">

```bash
curl -X GET "https://api.complianceagent.io/v1/compliance/issues?severity=critical,high&status=open&limit=10" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY" | jq '.data[] | "\(.severity): \(.title)"'
```

</TabItem>
</Tabs>

---

### 3. Generate and Apply a Fix

Automatically generate compliant code and create a PR.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# Generate a fix for an issue
fix = client.compliance.generate_fix(
    issue_id="issue_abc123",
    strategy="automatic"
)

print(f"Fix generated with confidence: {fix.confidence_score}")
print(f"Files to modify: {len(fix.changes)}")

# Preview the changes
for change in fix.changes:
    print(f"\n--- {change.file_path} ---")
    print(change.diff)

# Apply the fix and create a PR
if fix.confidence_score > 0.8:
    result = client.compliance.apply_fix(
        issue_id="issue_abc123",
        fix_id=fix.id,
        create_pull_request=True,
        pr_options={
            "title": f"fix: {fix.title}",
            "reviewers": ["security-team"],
            "labels": ["compliance", "auto-generated"]
        }
    )
    print(f"\n✅ PR created: {result.pull_request.url}")
```

**Output:**
```
Fix generated with confidence: 0.95
Files to modify: 2

--- src/models/user.py ---
@@ -45,8 +45,12 @@
-    email = Column(String)
-    ssn = Column(String)
+    email = Column(EncryptedString(key_id='user_pii'))
+    ssn = Column(EncryptedString(key_id='user_pii'))

✅ PR created: https://github.com/acme/web-app/pull/456
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```typescript
// Generate a fix for an issue
const fix = await client.compliance.generateFix({
  issueId: 'issue_abc123',
  strategy: 'automatic',
});

console.log(`Fix generated with confidence: ${fix.confidenceScore}`);
console.log(`Files to modify: ${fix.changes.length}`);

// Preview the changes
for (const change of fix.changes) {
  console.log(`\n--- ${change.filePath} ---`);
  console.log(change.diff);
}

// Apply the fix and create a PR
if (fix.confidenceScore > 0.8) {
  const result = await client.compliance.applyFix({
    issueId: 'issue_abc123',
    fixId: fix.id,
    createPullRequest: true,
    prOptions: {
      title: `fix: ${fix.title}`,
      reviewers: ['security-team'],
      labels: ['compliance', 'auto-generated'],
    },
  });
  console.log(`\n✅ PR created: ${result.pullRequest.url}`);
}
```

</TabItem>
<TabItem value="go" label="Go">

```go
// Generate a fix
fix, err := client.Compliance.GenerateFix(ctx, "issue_abc123", &complianceagent.FixOptions{
    Strategy: "automatic",
})
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Fix generated with confidence: %.2f\n", fix.ConfidenceScore)

// Apply if confident
if fix.ConfidenceScore > 0.8 {
    result, err := client.Compliance.ApplyFix(ctx, "issue_abc123", fix.ID, &complianceagent.PROptions{
        Title:     fmt.Sprintf("fix: %s", fix.Title),
        Reviewers: []string{"security-team"},
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("PR created: %s\n", result.PullRequest.URL)
}
```

</TabItem>
<TabItem value="curl" label="cURL">

```bash
# Generate fix
FIX_RESPONSE=$(curl -X POST "https://api.complianceagent.io/v1/compliance/issues/issue_abc123/generate-fix" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"strategy": "automatic"}')

FIX_ID=$(echo $FIX_RESPONSE | jq -r '.data.fix_id')

# Apply fix and create PR
curl -X POST "https://api.complianceagent.io/v1/compliance/issues/issue_abc123/apply-fix" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"fix_id\": \"$FIX_ID\",
    \"create_pull_request\": true,
    \"pr_options\": {
      \"title\": \"fix: Compliance issue\",
      \"reviewers\": [\"security-team\"]
    }
  }" | jq '.data.pull_request.url'
```

</TabItem>
</Tabs>

---

### 4. Export Audit Evidence

Generate an evidence package for auditors.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# Export audit evidence for SOC 2 review
export_job = client.audit.export_evidence(
    frameworks=["soc2"],
    date_range={
        "from": "2024-01-01",
        "to": "2024-03-31"
    },
    include_sections=[
        "executive_summary",
        "control_matrix",
        "evidence_artifacts",
        "remediation_timeline"
    ],
    format="pdf"
)

print(f"Export job started: {export_job.id}")

# Wait for completion
import time
while export_job.status == "processing":
    time.sleep(5)
    export_job = client.audit.get_export_status(export_job.id)

print(f"Download: {export_job.download_url}")
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```typescript
// Export audit evidence for SOC 2 review
const exportJob = await client.audit.exportEvidence({
  frameworks: ['soc2'],
  dateRange: {
    from: '2024-01-01',
    to: '2024-03-31',
  },
  includeSections: [
    'executive_summary',
    'control_matrix',
    'evidence_artifacts',
    'remediation_timeline',
  ],
  format: 'pdf',
});

console.log(`Export job started: ${exportJob.id}`);

// Poll for completion
let status = exportJob;
while (status.status === 'processing') {
  await new Promise((r) => setTimeout(r, 5000));
  status = await client.audit.getExportStatus(exportJob.id);
}

console.log(`Download: ${status.downloadUrl}`);
```

</TabItem>
<TabItem value="curl" label="cURL">

```bash
# Start export
curl -X POST "https://api.complianceagent.io/v1/audit/evidence/export" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "frameworks": ["soc2"],
    "date_range": {"from": "2024-01-01", "to": "2024-03-31"},
    "format": "pdf"
  }'
```

</TabItem>
</Tabs>

---

### 5. Set Up Webhooks for Real-Time Alerts

Get notified instantly when compliance issues are detected.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# Create a webhook for compliance events
webhook = client.webhooks.create(
    url="https://your-app.com/webhooks/complianceagent",
    events=[
        "compliance.issue_created",
        "compliance.status_changed",
        "regulation.updated",
        "scan.completed"
    ],
    secret="your_webhook_secret_123"
)

print(f"Webhook created: {webhook.id}")
print(f"Events: {', '.join(webhook.events)}")
```

**Handling webhooks in your app (Flask example):**

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret_123"

@app.route("/webhooks/complianceagent", methods=["POST"])
def handle_webhook():
    # Verify signature
    signature = request.headers.get("X-ComplianceAgent-Signature")
    expected = f"sha256={hmac.new(WEBHOOK_SECRET.encode(), request.data, hashlib.sha256).hexdigest()}"
    
    if not hmac.compare_digest(expected, signature):
        return "Invalid signature", 401
    
    event = request.json
    
    if event["event"] == "compliance.issue_created":
        issue = event["data"]
        # Send Slack alert for critical issues
        if issue["severity"] == "critical":
            send_slack_alert(
                f"🚨 Critical compliance issue: {issue['title']}\n"
                f"Repository: {issue['repository']}\n"
                f"Framework: {issue['framework']}"
            )
    
    return "OK", 200
```

</TabItem>
<TabItem value="typescript" label="TypeScript">

```typescript
// Create a webhook for compliance events
const webhook = await client.webhooks.create({
  url: 'https://your-app.com/webhooks/complianceagent',
  events: [
    'compliance.issue_created',
    'compliance.status_changed',
    'regulation.updated',
    'scan.completed',
  ],
  secret: 'your_webhook_secret_123',
});

console.log(`Webhook created: ${webhook.id}`);
```

**Handling webhooks (Express example):**

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
const WEBHOOK_SECRET = 'your_webhook_secret_123';

app.post('/webhooks/complianceagent', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-complianceagent-signature'] as string;
  const expected = `sha256=${crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(req.body)
    .digest('hex')}`;

  if (!crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signature))) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(req.body.toString());

  if (event.event === 'compliance.issue_created') {
    const issue = event.data;
    if (issue.severity === 'critical') {
      sendSlackAlert(`🚨 Critical: ${issue.title}`);
    }
  }

  res.status(200).send('OK');
});
```

</TabItem>
</Tabs>

---

## Next Steps

- **[API Reference](/docs/api/overview)** - Complete endpoint documentation
- **[Authentication](/docs/api/authentication)** - API keys and OAuth
- **[Connecting Repositories](/docs/guides/connecting-repositories)** - Integration guides
- **[Webhooks](/docs/api/overview#webhooks)** - Real-time notifications

## Need Help?

- 📚 [Full API Documentation](/docs/api/overview)
- 💬 [Discord Community](https://discord.gg/complianceagent)
- 📧 [Email Support](mailto:support@complianceagent.io)
