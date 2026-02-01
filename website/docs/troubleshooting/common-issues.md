---
sidebar_position: 1
title: Troubleshooting
description: Common issues and solutions
---

# Troubleshooting

Solutions to common issues when using ComplianceAgent.

## Installation Issues

### Docker Compose Fails to Start

**Symptom:** `docker compose up` fails with connection errors.

**Solution:**

```bash
# Check if Docker is running
docker info

# Check available resources
docker system df

# Clean up and retry
docker compose down -v
docker system prune -f
docker compose up -d
```

### Database Connection Refused

**Symptom:** `connection refused` or `ECONNREFUSED` errors.

**Solution:**

```bash
# Wait for database to be ready
docker compose exec postgres pg_isready -U complianceagent

# Check database logs
docker compose logs postgres

# Verify connection string
echo $DATABASE_URL
```

### Port Already in Use

**Symptom:** `port is already allocated` error.

**Solution:**

```bash
# Find process using the port
lsof -i :8000

# Kill the process or change port
# In docker-compose.yml:
ports:
  - "8001:8000"
```

## Authentication Issues

### Invalid API Key

**Symptom:** `401 Unauthorized` with "Invalid API key" message.

**Solutions:**

1. Verify key format starts with `ca_live_sk_` or `ca_test_sk_`
2. Check key hasn't expired
3. Regenerate key if compromised

```bash
# Test API key
curl -X GET "http://localhost:8000/api/v1/health" \
  -H "Authorization: Bearer $COMPLIANCEAGENT_API_KEY"
```

### Token Expired

**Symptom:** `401 Unauthorized` with "Token expired" message.

**Solution:**

```python
# Refresh token before expiry
from complianceagent import Client

client = Client(api_key="your_key")
# SDK handles token refresh automatically
```

### GitHub Token Invalid

**Symptom:** AI features fail with GitHub authentication errors.

**Solution:**

1. Verify token has required scopes: `repo`, `read:org`
2. Check token hasn't expired
3. Regenerate token if needed

```bash
# Test GitHub token
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user
```

## Scanning Issues

### Scan Timeout

**Symptom:** Scans fail with timeout errors.

**Solutions:**

1. Increase timeout:
```yaml
# config.yml
scanning:
  timeout: 7200  # 2 hours
```

2. Exclude large files:
```yaml
scanning:
  ignore_patterns:
    - "*.min.js"
    - "vendor/**"
    - "node_modules/**"
```

3. Enable incremental scanning:
```yaml
scanning:
  incremental: true
```

### Repository Not Found

**Symptom:** `404 Not Found` when connecting repository.

**Solutions:**

1. Verify repository URL is correct
2. Check GitHub App has access to the repository
3. For private repos, ensure token has `repo` scope

### No Issues Detected

**Symptom:** Scan completes but finds no issues.

**Possible causes:**

1. Frameworks not enabled:
```bash
# Check enabled frameworks
curl http://localhost:8000/api/v1/repositories/REPO_ID
```

2. Files excluded by ignore patterns
3. Repository language not supported

**Debug:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker compose restart backend
```

## Performance Issues

### Slow API Responses

**Symptom:** API takes >5 seconds to respond.

**Solutions:**

1. Check database queries:
```sql
-- Find slow queries
SELECT query, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

2. Add database indexes:
```sql
CREATE INDEX CONCURRENTLY idx_issues_repo_id 
ON issues(repository_id);
```

3. Increase worker count:
```bash
export WORKERS=8
```

### High Memory Usage

**Symptom:** Container OOM killed or swap usage high.

**Solutions:**

1. Increase container memory limits:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
```

2. Reduce worker count:
```bash
export WORKERS=2
```

3. Enable memory profiling:
```bash
export PROFILING=true
```

### Redis Connection Errors

**Symptom:** `Redis connection refused` or timeouts.

**Solutions:**

1. Check Redis is running:
```bash
docker compose exec redis redis-cli ping
```

2. Increase connection pool:
```bash
export REDIS_MAX_CONNECTIONS=20
```

3. Check Redis memory:
```bash
docker compose exec redis redis-cli info memory
```

## Fix Generation Issues

### Fix Not Generated

**Symptom:** "Fix generation failed" error.

**Solutions:**

1. Check GitHub token is valid
2. Verify Copilot SDK access
3. Check issue has enough context

```bash
# View issue details
curl http://localhost:8000/api/v1/compliance/issues/ISSUE_ID
```

### Fix Doesn't Compile

**Symptom:** Generated fix has syntax errors.

**Solutions:**

1. Report issue quality:
```bash
curl -X POST http://localhost:8000/api/v1/compliance/issues/ISSUE_ID/feedback \
  -d '{"quality": "poor", "reason": "syntax_error"}'
```

2. Regenerate with different strategy:
```bash
curl -X POST http://localhost:8000/api/v1/compliance/issues/ISSUE_ID/generate-fix \
  -d '{"strategy": "conservative"}'
```

### Pull Request Creation Fails

**Symptom:** Fix applied locally but PR not created.

**Solutions:**

1. Check GitHub App permissions include `pull_requests: write`
2. Verify branch protection allows the app
3. Check for branch conflicts

## Integration Issues

### Webhook Not Received

**Symptom:** Events not triggering webhooks.

**Solutions:**

1. Verify webhook URL is accessible:
```bash
curl -X POST https://your-webhook-url/test
```

2. Check webhook configuration:
```bash
curl http://localhost:8000/api/v1/webhooks
```

3. View webhook delivery history:
```bash
curl http://localhost:8000/api/v1/webhooks/WEBHOOK_ID/deliveries
```

### Slack Notifications Not Working

**Symptom:** No Slack messages received.

**Solutions:**

1. Verify webhook URL:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  $SLACK_WEBHOOK_URL
```

2. Check channel permissions
3. Verify notification settings in dashboard

## Data Issues

### Missing Audit Logs

**Symptom:** Audit logs incomplete or missing entries.

**Solutions:**

1. Check Elasticsearch is running:
```bash
curl http://localhost:9200/_cluster/health
```

2. Verify log retention settings:
```yaml
audit:
  retention_days: 2555
```

3. Check disk space:
```bash
df -h /var/lib/elasticsearch
```

### Compliance Score Incorrect

**Symptom:** Score doesn't reflect actual compliance state.

**Solutions:**

1. Force rescan:
```bash
curl -X POST http://localhost:8000/api/v1/repositories/REPO_ID/scan \
  -d '{"full_scan": true}'
```

2. Clear cache:
```bash
docker compose exec redis redis-cli FLUSHDB
```

## Getting Help

### Collect Debug Information

```bash
# Generate support bundle
./scripts/support-bundle.sh

# Contents:
# - Application logs (last 24h)
# - Configuration (secrets redacted)
# - System information
# - Database statistics
```

### Contact Support

1. **Community:** [GitHub Discussions](https://github.com/complianceagent/complianceagent/discussions)
2. **Bug Reports:** [GitHub Issues](https://github.com/complianceagent/complianceagent/issues)
3. **Enterprise:** support@complianceagent.io

Include:
- Support bundle
- Steps to reproduce
- Expected vs actual behavior
- Environment details

---

See also: [FAQ](./faq) | [Configuration](../getting-started/configuration)
