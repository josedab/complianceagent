# Operations Runbook

This runbook provides procedures for operating ComplianceAgent in production.

## Quick Reference

| Action | Command |
|--------|---------|
| Check health | `curl https://api.complianceagent.ai/health` |
| View logs | `kubectl logs -f deployment/backend` |
| Restart backend | `kubectl rollout restart deployment/backend` |
| Scale workers | `kubectl scale deployment/celery-workers --replicas=N` |
| Database backup | `make backup-prod` |

---

## System Health

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Basic health | `{"status": "healthy"}` |
| `/health/ready` | Readiness probe | `{"status": "ready"}` |
| `/health/live` | Liveness probe | `{"status": "alive"}` |
| `/health/db` | Database connectivity | `{"status": "connected"}` |
| `/health/redis` | Redis connectivity | `{"status": "connected"}` |

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

API_URL="${API_URL:-https://api.complianceagent.ai}"

echo "Checking ComplianceAgent health..."

# Basic health
if curl -sf "$API_URL/health" > /dev/null; then
    echo "✅ API: Healthy"
else
    echo "❌ API: Unhealthy"
    exit 1
fi

# Database
if curl -sf "$API_URL/health/db" > /dev/null; then
    echo "✅ Database: Connected"
else
    echo "❌ Database: Disconnected"
    exit 1
fi

# Redis
if curl -sf "$API_URL/health/redis" > /dev/null; then
    echo "✅ Redis: Connected"
else
    echo "❌ Redis: Disconnected"
    exit 1
fi

echo "All systems healthy!"
```

---

## Common Operations

### Deployment

#### Deploy New Version

```bash
# 1. Build and push Docker images
make build-prod
make push-prod

# 2. Update Kubernetes
kubectl set image deployment/backend backend=complianceagent/backend:${VERSION}
kubectl set image deployment/frontend frontend=complianceagent/frontend:${VERSION}

# 3. Monitor rollout
kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend
```

#### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/backend

# Rollback to previous version
kubectl rollout undo deployment/backend

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=3
```

### Scaling

#### Manual Scaling

```bash
# Scale backend API
kubectl scale deployment/backend --replicas=5

# Scale Celery workers
kubectl scale deployment/celery-workers --replicas=10

# Scale frontend
kubectl scale deployment/frontend --replicas=3
```

#### Autoscaling Configuration

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Database Operations

#### Run Migrations

```bash
# Connect to backend pod
kubectl exec -it deployment/backend -- /bin/bash

# Run migrations
cd /app
alembic upgrade head

# Check current version
alembic current
```

#### Database Backup

```bash
# Manual backup
kubectl exec -it statefulset/postgres -- pg_dump -U complianceagent complianceagent > backup.sql

# Automated backup (via CronJob)
kubectl create -f infrastructure/k8s/backup-cronjob.yaml
```

#### Database Restore

```bash
# Stop backend to prevent writes
kubectl scale deployment/backend --replicas=0

# Restore backup
kubectl exec -i statefulset/postgres -- psql -U complianceagent complianceagent < backup.sql

# Restart backend
kubectl scale deployment/backend --replicas=3
```

### Log Management

#### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend --tail=100

# Worker logs
kubectl logs -f deployment/celery-workers --tail=100

# All backend pods
kubectl logs -l app=backend --tail=100

# With timestamps
kubectl logs -f deployment/backend --timestamps
```

#### Search Logs (Elasticsearch/Kibana)

```
# Find errors in last hour
level:error AND @timestamp:[now-1h TO now]

# Find specific user activity
user_id:"user123" AND action:*

# Find slow queries
duration_ms:>1000
```

---

## Incident Response

### Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| **P1 - Critical** | Service down, data breach | 15 minutes | API completely unavailable |
| **P2 - High** | Major feature broken | 1 hour | Authentication failing |
| **P3 - Medium** | Degraded performance | 4 hours | Slow response times |
| **P4 - Low** | Minor issue | 24 hours | UI glitch |

### Incident Workflow

```
1. DETECT
   └─> Alert triggered or user report

2. TRIAGE
   └─> Assign severity level
   └─> Notify on-call engineer
   └─> Create incident ticket

3. INVESTIGATE
   └─> Check monitoring dashboards
   └─> Review logs
   └─> Identify root cause

4. MITIGATE
   └─> Apply temporary fix
   └─> Communicate status

5. RESOLVE
   └─> Implement permanent fix
   └─> Verify resolution
   └─> Update status page

6. POST-MORTEM
   └─> Document timeline
   └─> Identify improvements
   └─> Update runbooks
```

### Common Issues

#### High API Latency

**Symptoms:** Response times > 500ms

**Investigation:**
```bash
# Check API metrics
curl https://api.complianceagent.ai/metrics | grep http_request_duration

# Check database connections
kubectl exec -it statefulset/postgres -- psql -U complianceagent -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
kubectl exec -it statefulset/postgres -- psql -U complianceagent -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Resolution:**
1. Scale backend pods if CPU > 80%
2. Check for missing database indexes
3. Review recent deployments for regressions

#### Database Connection Pool Exhaustion

**Symptoms:** "too many connections" errors

**Investigation:**
```bash
# Check active connections
kubectl exec -it statefulset/postgres -- psql -U complianceagent -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"
```

**Resolution:**
1. Kill idle connections:
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';
   ```
2. Increase `max_connections` in PostgreSQL config
3. Review connection pool settings in backend

#### Redis Memory Full

**Symptoms:** Redis OOM errors, cache misses

**Investigation:**
```bash
kubectl exec -it statefulset/redis -- redis-cli INFO memory
```

**Resolution:**
1. Clear expired keys: `redis-cli FLUSHDB` (caution: clears cache)
2. Increase Redis memory limit
3. Review TTL settings for cached data

#### Worker Queue Backlog

**Symptoms:** Tasks not processing, queue growing

**Investigation:**
```bash
# Check queue length
kubectl exec -it deployment/celery-workers -- celery -A app.workers inspect active

# Check for stuck tasks
kubectl exec -it deployment/celery-workers -- celery -A app.workers inspect reserved
```

**Resolution:**
1. Scale workers: `kubectl scale deployment/celery-workers --replicas=10`
2. Check for failing tasks in logs
3. Clear stuck tasks if necessary

---

## Maintenance Procedures

### Planned Maintenance Window

```bash
# 1. Notify users (update status page)
# 2. Enable maintenance mode
kubectl set env deployment/backend MAINTENANCE_MODE=true

# 3. Wait for active requests to complete
sleep 60

# 4. Perform maintenance
# ...

# 5. Disable maintenance mode
kubectl set env deployment/backend MAINTENANCE_MODE=false

# 6. Verify health
./health-check.sh

# 7. Update status page
```

### Certificate Renewal

```bash
# Check certificate expiry
kubectl get certificate -o wide

# Force renewal (cert-manager)
kubectl delete secret tls-secret
kubectl annotate certificate complianceagent-tls cert-manager.io/issue-temporary-certificate="true"
```

### Secret Rotation

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update in secret manager
aws secretsmanager update-secret --secret-id complianceagent/api-key --secret-string "$NEW_SECRET"

# 3. Restart deployments to pick up new secret
kubectl rollout restart deployment/backend
kubectl rollout restart deployment/celery-workers

# 4. Verify application health
./health-check.sh
```

---

## Monitoring

### Key Metrics

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API Response Time (p99) | > 500ms | > 2s | Scale or investigate |
| Error Rate | > 1% | > 5% | Investigate logs |
| CPU Usage | > 70% | > 90% | Scale pods |
| Memory Usage | > 80% | > 95% | Scale or investigate leaks |
| Database Connections | > 80% pool | > 95% pool | Scale or optimize |
| Queue Depth | > 1000 | > 10000 | Scale workers |

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: complianceagent
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency detected"
```

### Dashboards

| Dashboard | Purpose | URL |
|-----------|---------|-----|
| Overview | System health summary | `/grafana/d/overview` |
| API Performance | Request latency, throughput | `/grafana/d/api` |
| Database | Query performance, connections | `/grafana/d/database` |
| Workers | Queue depth, task processing | `/grafana/d/workers` |
| Business | Compliance scans, users | `/grafana/d/business` |

---

## Contacts

### On-Call Rotation

| Role | Primary | Secondary |
|------|---------|-----------|
| Backend | [Name/PagerDuty] | [Name/PagerDuty] |
| Infrastructure | [Name/PagerDuty] | [Name/PagerDuty] |
| Database | [Name/PagerDuty] | [Name/PagerDuty] |

### Escalation Path

1. On-call engineer (15 min)
2. Team lead (30 min)
3. Engineering manager (1 hour)
4. VP Engineering (P1 only)

### External Contacts

| Service | Contact | Purpose |
|---------|---------|---------|
| AWS Support | [Support case] | Infrastructure issues |
| GitHub Support | [Support ticket] | Copilot API issues |
| PagerDuty | [Admin portal] | Alerting issues |

---

## Related Documentation

- [Deployment Guide](../deployment/README.md)
- [Troubleshooting](troubleshooting.md)
- [Security Best Practices](security.md)
- [Architecture Overview](../architecture/overview.md)
