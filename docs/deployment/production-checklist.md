# Production Checklist & Runbook

> **Last updated:** 2026-07-27
>
> Complete every section before the first production deployment and review quarterly.

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Secrets & Credentials](#2-secrets--credentials)
3. [DNS & TLS](#3-dns--tls)
4. [Database Migrations](#4-database-migrations)
5. [Monitoring & Alerts](#5-monitoring--alerts)
6. [Backups & Restore Drill](#6-backups--restore-drill)
7. [Smoke Tests](#7-smoke-tests)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Incident Response](#9-incident-response)
10. [External Prerequisites](#10-external-prerequisites)

---

## 1. Pre-Deployment Checklist

### Infrastructure

- [ ] Terraform `plan` reviewed and `apply` completed for target environment
- [ ] VPC, subnets, NAT gateways provisioned
- [ ] ECS cluster running with Fargate capacity providers
- [ ] ALB provisioned with HTTPS listener and valid ACM certificate
- [ ] RDS Aurora Serverless v2 cluster running (backup retention ≥ 7 days)
- [ ] ElastiCache Redis cluster running (TLS enabled, auth token set)
- [ ] S3 buckets created with versioning, encryption, and public access blocked
- [ ] ECR repositories created (backend, frontend, crawler) with scan-on-push
- [ ] CloudWatch log groups exist for all ECS services
- [ ] WAF web ACL attached to ALB (recommended)

### Application

- [ ] `.env.production.example` copied to `.env` with all `CHANGE_ME` values replaced
- [ ] All `REQUIRED` environment variables set in Secrets Manager
- [ ] Docker images built, scanned (Trivy), and pushed to ECR/GHCR
- [ ] Database migrations run successfully (`alembic upgrade head`)
- [ ] Health endpoint returns 200: `curl https://api.complianceagent.ai/health`
- [ ] Frontend loads at `https://app.complianceagent.ai`

### CI/CD

- [ ] GitHub environments created: `staging`, `production`
- [ ] Production environment requires manual approval
- [ ] `AWS_DEPLOY_ROLE_ARN` secret set in GitHub repository settings
- [ ] `SMOKE_TEST_TOKEN` secret set for authenticated smoke tests
- [ ] Branch protection rules enabled on `main` requiring CI pass

---

## 2. Secrets & Credentials

### Secrets Manager Layout

All application secrets live in AWS Secrets Manager under the key:

```
complianceagent/<environment>/app-secrets
```

JSON keys required:

| Key | Description | Rotation |
|-----|-------------|----------|
| `SECRET_KEY` | JWT signing key (64-char hex) | Quarterly |
| `DATABASE_URL` | PostgreSQL connection string with `sslmode=require` | On password rotation |
| `REDIS_URL` | Redis connection string (`rediss://` for TLS) | On password rotation |
| `COPILOT_API_KEY` | GitHub Copilot SDK API key | As needed |
| `SENTRY_DSN` | Sentry error tracking DSN | Rarely |
| `GITHUB_APP_ID` | GitHub App identifier | Rarely |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App PEM (base64) | Annual |
| `GITHUB_WEBHOOK_SECRET` | GitHub webhook signing secret | On rotation |
| `STRIPE_API_KEY` | Stripe live API key | On rotation |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | On rotation |
| `SMTP_HOST` | SMTP/SES endpoint (may be empty when using email API) | Rarely |
| `SMTP_USER` | SMTP/SES username (may be empty when using email API) | On rotation |
| `SMTP_PASSWORD` | SES SMTP credentials | On rotation |
| `SMTP_FROM_EMAIL` | Verified transactional sender | Rarely |
| `EMAIL_API_ENDPOINT` | Transactional email provider endpoint (may be empty for SMTP) | Rarely |
| `EMAIL_API_KEY` | Transactional email provider key (may be empty for SMTP) | On rotation |

### Rotation Procedure

1. Generate new credential
2. Update Secrets Manager: `aws secretsmanager update-secret --secret-id complianceagent/production/app-secrets --secret-string '...'`
3. Force ECS service redeployment: `aws ecs update-service --cluster complianceagent-production --service complianceagent-api-production --force-new-deployment`
4. Verify health check passes after rolling update completes

---

## 3. DNS & TLS

### DNS Records

| Record | Type | Value |
|--------|------|-------|
| `api.complianceagent.ai` | CNAME / ALIAS | ALB DNS name |
| `app.complianceagent.ai` | CNAME / ALIAS | ALB DNS name |
| `complianceagent.ai` | A / ALIAS | ALB DNS name |

### TLS Certificate

- **Provider:** AWS Certificate Manager (ACM)
- **Domain:** `complianceagent.ai` + `*.complianceagent.ai`
- **Validation:** DNS (auto-renewing)
- **ALB Policy:** `ELBSecurityPolicy-TLS13-1-2-2021-06`

### Verification

```bash
# Check certificate validity
openssl s_client -connect api.complianceagent.ai:443 -servername api.complianceagent.ai </dev/null 2>/dev/null | openssl x509 -noout -dates

# Check HSTS header
curl -sI https://api.complianceagent.ai | grep -i strict-transport
```

---

## 4. Database Migrations

### Running Migrations

```bash
# Via ECS one-shot task (production)
aws ecs run-task \
  --cluster complianceagent-production \
  --task-definition complianceagent-migrate-production \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=DISABLED}"

# Via Docker Compose (self-hosted)
docker compose -f docker/docker-compose.prod.yml run --rm migrate
```

### Migration Rollback

```bash
# Roll back the last migration
cd backend && alembic downgrade -1

# Roll back to a specific revision
cd backend && alembic downgrade <revision_hash>

# View migration history
cd backend && alembic history --verbose
```

### Safety Rules

1. **Never run destructive migrations without a backup** — run `make backup` first
2. **Test migrations on staging before production**
3. **CI runs migrations before deploying new code** — if migration fails, deploy is blocked
4. **Schema changes should be backwards-compatible** — old code must work with new schema during rolling deploys

---

## 5. Monitoring & Alerts

### Health Endpoints

| Endpoint | Check | Expected |
|----------|-------|----------|
| `GET /health` | App + DB + Redis connectivity | `{"status": "healthy"}` |
| `GET /api/v1/status` | Authenticated service status | 200 with service details |

### CloudWatch Alarms (Recommended)

| Alarm | Metric | Threshold | Action |
|-------|--------|-----------|--------|
| API High CPU | ECS CPUUtilization | > 80% for 5 min | SNS → PagerDuty |
| API High Memory | ECS MemoryUtilization | > 85% for 5 min | SNS → PagerDuty |
| API 5xx Rate | ALB HTTPCode_Target_5XX_Count | > 10/min | SNS → PagerDuty |
| API Latency | ALB TargetResponseTime | p99 > 5s | SNS → Slack |
| DB High CPU | RDS CPUUtilization | > 80% for 10 min | SNS → PagerDuty |
| DB Connections | RDS DatabaseConnections | > 80% max | SNS → Slack |
| Redis Memory | ElastiCache DatabaseMemoryUsagePercentage | > 80% | SNS → Slack |
| Worker Queue Depth | Custom metric (Celery) | > 100 pending | SNS → Slack |

### Sentry Configuration

- **DSN:** Set via `SENTRY_DSN` in Secrets Manager
- **Traces sample rate:** 10% (`SENTRY_TRACES_SAMPLE_RATE=0.1`)
- **Alert rules:** Create Sentry alerts for new error types and error rate spikes

### Log Locations

| Service | CloudWatch Log Group |
|---------|---------------------|
| API | `/ecs/complianceagent-production/api` |
| Frontend | `/ecs/complianceagent-production/frontend` |
| Worker | `/ecs/complianceagent-production/worker` |
| Beat | `/ecs/complianceagent-production/beat` |
| Migrations | `/ecs/complianceagent-production/migrate` |

---

## 6. Backups & Restore Drill

### Automated Backups

- **RDS Aurora:** Automated backups with 7-day retention + continuous backup to S3
- **Application-level:** `make backup-auto` via cron (daily)
- **S3 buckets:** Versioning enabled — objects recoverable for 30 days

### Manual Backup

```bash
# Interactive backup with encryption
make backup

# Automated backup (cron-safe, uploads to S3)
make backup-auto

# Cron example (daily at 2 AM)
# 0 2 * * * cd /opt/complianceagent && make backup-auto >> /var/log/backup.log 2>&1
```

### Restore Drill (Run Quarterly)

```bash
# 1. List available backups
ls -la backups/ | head -20
# or: aws s3 ls s3://complianceagent-prod-backups/backups/

# 2. Restore to test database
POSTGRES_DB=complianceagent_restore_test make restore FILE=backups/latest.sql.gz.enc

# 3. Verify restored data
psql -h localhost -U complianceagent_app -d complianceagent_restore_test \
  -c "SELECT count(*) FROM alembic_version; SELECT count(*) FROM organizations;"

# 4. Cleanup
dropdb complianceagent_restore_test
```

### Restore Drill Log

| Date | Backup Source | Restore Time | Data Verified | Performed By |
|------|--------------|--------------|---------------|-------------|
| _YYYY-MM-DD_ | _backup file_ | _X min_ | _Yes/No_ | _Name_ |

---

## 7. Smoke Tests

### Post-Deployment Smoke Test

Run automatically by CI after deployment. Can also be run manually:

```bash
# Health check
curl -f https://api.complianceagent.ai/health

# Authenticated API check (requires valid token)
curl -H "Authorization: Bearer $TOKEN" https://api.complianceagent.ai/api/v1/status

# Frontend loads
curl -s -o /dev/null -w '%{http_code}' https://app.complianceagent.ai

# WebSocket connectivity (if applicable)
# wscat -c wss://api.complianceagent.ai/ws
```

### Smoke Test Checklist

- [ ] `/health` returns 200
- [ ] `/api/v1/status` returns 200 with valid token
- [ ] Frontend loads without JavaScript errors
- [ ] Login flow works end-to-end
- [ ] Background worker processes test job within 60s

---

## 8. Rollback Procedures

### ECS Service Rollback

ECS deployment circuit breakers are enabled. If a new deployment fails health checks,
ECS automatically rolls back to the previous stable task definition.

**Manual rollback:**

```bash
# 1. Find the previous stable task definition
aws ecs describe-services --cluster complianceagent-production \
  --services complianceagent-api-production \
  --query 'services[0].deployments[*].{status:status,taskDef:taskDefinition}'

# 2. Force rollback to previous revision
aws ecs update-service --cluster complianceagent-production \
  --service complianceagent-api-production \
  --task-definition <previous-task-def-arn> \
  --force-new-deployment

# 3. Wait for stabilization
aws ecs wait services-stable --cluster complianceagent-production \
  --services complianceagent-api-production
```

### Database Migration Rollback

```bash
# Roll back the last migration
cd backend && alembic downgrade -1

# Then redeploy the previous code version
```

### Docker Compose Rollback

```bash
# Roll back to a specific image version
VERSION=1.2.3 docker compose -f docker/docker-compose.prod.yml up -d

# Or use the previous image tag
VERSION=sha-abc123 docker compose -f docker/docker-compose.prod.yml up -d
```

### Swarm Rollback

```bash
# Docker Swarm auto-rollback is configured in the stack.
# Manual rollback:
docker service rollback complianceagent_backend
docker service rollback complianceagent_frontend
```

---

## 9. Incident Response

### Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| SEV1 | Service down, data loss | 15 min | API returns 5xx for all requests |
| SEV2 | Major feature broken | 1 hour | Login/auth broken, workers stuck |
| SEV3 | Minor feature degraded | 4 hours | Slow queries, partial data issue |
| SEV4 | Cosmetic/minor | Next business day | UI glitch, non-critical log errors |

### Incident Response Checklist

1. **Acknowledge** — Post in `#incidents` channel with severity
2. **Assess** — Check health endpoints, logs, metrics dashboards
3. **Communicate** — Update status page if SEV1/SEV2
4. **Mitigate** — Rollback if deployment-related, scale up if load-related
5. **Resolve** — Fix root cause, deploy fix through normal CI/CD
6. **Post-mortem** — Write and share within 48 hours for SEV1/SEV2

### Quick Diagnostics

```bash
# Check all ECS services
aws ecs describe-services --cluster complianceagent-production \
  --services complianceagent-api-production complianceagent-frontend-production \
  --query 'services[*].{name:serviceName,running:runningCount,desired:desiredCount,status:status}'

# Check recent errors in logs
aws logs filter-log-events \
  --log-group-name /ecs/complianceagent-production/api \
  --start-time $(date -d '1 hour ago' +%s000) \
  --filter-pattern "ERROR"

# Check RDS status
aws rds describe-db-clusters --db-cluster-identifier complianceagent-production \
  --query 'DBClusters[0].{status:Status,connections:Endpoint}'

# Check Redis status
aws elasticache describe-replication-groups --replication-group-id complianceagent-production \
  --query 'ReplicationGroups[0].Status'
```

---

## 10. External Prerequisites

### Accounts & Services Required

| Service | Purpose | Setup |
|---------|---------|-------|
| AWS Account | Infrastructure hosting | Console/CLI access with appropriate IAM |
| GitHub | Source code, CI/CD, container registry | Repository with Actions enabled |
| Sentry | Error tracking | Create project, get DSN |
| Codecov | Coverage tracking | Connect GitHub repo |
| Domain registrar | DNS management | Register `complianceagent.ai` |

### Optional Services

| Service | Purpose | When Needed |
|---------|---------|-------------|
| Stripe | Billing/subscriptions | When `FEATURE_STRIPE_BILLING=true` |
| SendGrid/SES | Email notifications | When `FEATURE_EMAIL_NOTIFICATIONS=true` |
| GitHub App | PR compliance checks | When `FEATURE_GITHUB_APP=true` |
| PagerDuty/Opsgenie | On-call alerting | Production SEV1/SEV2 response |
| Datadog | Advanced APM/monitoring | For enterprise observability |

### GitHub Repository Settings

- [ ] Branch protection on `main`: require CI pass, require PR review
- [ ] Environments: `staging` (auto-deploy), `production` (manual approval)
- [ ] Secrets: `AWS_DEPLOY_ROLE_ARN`, `SMOKE_TEST_TOKEN`
- [ ] Variables: `AWS_REGION`, `STAGING_URL`, `PROD_URL`, `PRIVATE_SUBNETS`, `ECS_SECURITY_GROUP`
- [ ] Dependabot: enabled for pip, npm, GitHub Actions, Terraform

---

## Appendix: Quick Reference Commands

```bash
# Build all images
make docker-build

# Start production stack
make prod-up

# Run migrations
make prod-migrate

# View logs
make prod-logs

# Create backup
make backup

# Restore from backup
make restore FILE=backups/complianceagent_20260727_020000.sql.gz.enc

# Check status
make prod-status

# Deploy via CI (push to main triggers staging → production pipeline)
git push origin main
```
