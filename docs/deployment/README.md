# Deployment Guide

This guide covers deploying ComplianceAgent to various environments, from local Docker to production AWS infrastructure.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Compose Deployment](#docker-compose-deployment)
- [AWS Deployment](#aws-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Management](#database-management)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

---

## Deployment Options

| Option | Best For | Complexity | Cost |
|--------|----------|------------|------|
| Docker Compose | Development, small teams | Low | $ |
| AWS (Terraform) | Production, enterprise | Medium | $$-$$$ |
| Kubernetes | Large scale, multi-region | High | $$$ |

---

## Docker Compose Deployment

### Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space

### Quick Deployment

```bash
# Clone repository
git clone https://github.com/josedab/complianceagent.git
cd complianceagent

# Configure environment
cp .env.example .env
# Edit .env with production values

# Start all services
cd docker
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Production Docker Compose

```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: complianceagent-backend:latest
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - COPILOT_API_KEY=${COPILOT_API_KEY}
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  frontend:
    image: complianceagent-frontend:latest
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    depends_on:
      - backend
    restart: unless-stopped

  celery-worker:
    image: complianceagent-backend:latest
    command: celery -A app.workers worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    image: complianceagent-backend:latest
    command: celery -A app.workers beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Nginx Configuration

```nginx
# docker/nginx.conf
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # API requests
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## AWS Deployment

### Architecture Overview

```mermaid
graph TB
    subgraph "Internet"
        Users[Users]
    end

    subgraph "AWS Cloud"
        subgraph "Public Subnet"
            ALB[Application Load Balancer]
        end

        subgraph "Private Subnet - Compute"
            ECS[ECS Fargate<br/>Backend + Frontend]
            Workers[ECS Fargate<br/>Celery Workers]
        end

        subgraph "Private Subnet - Data"
            Aurora[(Aurora Serverless v2<br/>PostgreSQL)]
            ElastiCache[(ElastiCache<br/>Redis)]
            OpenSearch[(OpenSearch<br/>Elasticsearch)]
        end

        subgraph "Storage"
            S3[(S3<br/>Documents)]
            Secrets[Secrets Manager]
        end
    end

    Users --> ALB
    ALB --> ECS
    ECS --> Aurora
    ECS --> ElastiCache
    ECS --> OpenSearch
    Workers --> Aurora
    Workers --> ElastiCache
    ECS --> S3
    ECS --> Secrets
```

### Prerequisites

- AWS CLI configured
- Terraform 1.5+
- Valid AWS account with permissions

### Deployment Steps

```bash
# Navigate to infrastructure
cd infrastructure/aws

# Initialize Terraform
terraform init

# Review plan
terraform plan -var-file="production.tfvars"

# Apply (creates ~15 minutes)
terraform apply -var-file="production.tfvars"
```

### Terraform Variables

```hcl
# infrastructure/aws/production.tfvars

# General
environment     = "production"
aws_region      = "us-east-1"
project_name    = "complianceagent"

# Networking
vpc_cidr        = "10.0.0.0/16"
azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Database
db_instance_class     = "db.serverless"
db_min_capacity       = 0.5
db_max_capacity       = 16
db_backup_retention   = 7

# ECS
backend_cpu           = 512
backend_memory        = 1024
backend_desired_count = 2
frontend_cpu          = 256
frontend_memory       = 512
frontend_desired_count = 2

# Redis
redis_node_type       = "cache.t4g.micro"

# Domain
domain_name           = "complianceagent.ai"
certificate_arn       = "arn:aws:acm:us-east-1:..."

# Secrets (stored in Secrets Manager)
# Set via AWS Console or CLI, not in tfvars
```

### AWS Resources Created

| Resource | Service | Purpose |
|----------|---------|---------|
| VPC | VPC | Network isolation |
| Subnets | VPC | Public/private network separation |
| ALB | Elastic Load Balancing | HTTPS termination, routing |
| ECS Cluster | ECS | Container orchestration |
| ECS Services | ECS Fargate | Run backend, frontend, workers |
| Aurora Serverless | RDS | PostgreSQL database |
| ElastiCache | ElastiCache | Redis cache/queue |
| OpenSearch | OpenSearch | Full-text search |
| S3 Bucket | S3 | Document storage |
| Secrets Manager | Secrets Manager | API keys, credentials |
| CloudWatch | CloudWatch | Logs and metrics |
| Route 53 | Route 53 | DNS management |
| ACM | Certificate Manager | SSL certificates |

### Post-Deployment

```bash
# Get outputs
terraform output

# Update DNS (if not using Route 53)
# Point your domain to the ALB DNS name

# Run database migrations
aws ecs run-task \
  --cluster complianceagent-production \
  --task-definition complianceagent-migrate \
  --launch-type FARGATE

# Verify health
curl https://your-domain.com/health
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-managed)
- kubectl configured
- Helm 3+

### Helm Chart Installation

```bash
# Add helm repo (if published)
helm repo add complianceagent https://charts.complianceagent.ai
helm repo update

# Install with custom values
helm install complianceagent complianceagent/complianceagent \
  -f values-production.yaml \
  --namespace complianceagent \
  --create-namespace
```

### Example values.yaml

```yaml
# values-production.yaml
replicaCount:
  backend: 3
  frontend: 2
  celeryWorker: 2

image:
  backend:
    repository: your-registry/complianceagent-backend
    tag: "1.0.0"
  frontend:
    repository: your-registry/complianceagent-frontend
    tag: "1.0.0"

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: complianceagent.your-domain.com
      paths:
        - path: /api
          pathType: Prefix
          backend: backend
        - path: /
          pathType: Prefix
          backend: frontend
  tls:
    - secretName: complianceagent-tls
      hosts:
        - complianceagent.your-domain.com

postgresql:
  enabled: true  # Or use external database
  auth:
    postgresPassword: changeme
    database: complianceagent

redis:
  enabled: true
  auth:
    enabled: true
    password: changeme

resources:
  backend:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 2Gi
  frontend:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

---

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `SECRET_KEY` | JWT signing key (32+ chars) | `your-super-secret-key-here` |
| `COPILOT_API_KEY` | GitHub Copilot SDK key | `ghp_xxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `S3_ENDPOINT_URL` | S3-compatible endpoint | AWS S3 |
| `S3_BUCKET_NAME` | Document storage bucket | `complianceagent` |
| `ENVIRONMENT` | Environment name | `production` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `CORS_ORIGINS` | Allowed origins | `["*"]` |
| `GITHUB_APP_ID` | GitHub App ID | - |
| `STRIPE_API_KEY` | Stripe API key | - |

### Secrets Management

**AWS Secrets Manager:**
```bash
# Create secret
aws secretsmanager create-secret \
  --name complianceagent/production \
  --secret-string '{"SECRET_KEY":"...", "COPILOT_API_KEY":"..."}'

# Reference in ECS task definition
{
  "secrets": [
    {
      "name": "SECRET_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:complianceagent/production:SECRET_KEY::"
    }
  ]
}
```

**Kubernetes Secrets:**
```bash
kubectl create secret generic complianceagent-secrets \
  --from-literal=SECRET_KEY=your-key \
  --from-literal=COPILOT_API_KEY=your-key \
  -n complianceagent
```

---

## Database Management

### Running Migrations

```bash
# Docker Compose
docker-compose exec backend alembic upgrade head

# AWS ECS
aws ecs run-task --cluster cluster-name --task-definition migrate-task

# Kubernetes
kubectl exec -it deploy/complianceagent-backend -n complianceagent -- \
  alembic upgrade head
```

### Backup Strategy

**AWS Aurora:**
- Automated backups enabled by default
- Point-in-time recovery up to 35 days
- Manual snapshots for long-term retention

**Docker/Self-hosted:**
```bash
# Backup
docker exec postgres pg_dump -U complianceagent complianceagent > backup.sql

# Restore
docker exec -i postgres psql -U complianceagent complianceagent < backup.sql
```

---

## SSL/TLS Configuration

### Let's Encrypt (Certbot)

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d complianceagent.your-domain.com

# Auto-renewal (cron)
0 0 1 * * certbot renew --quiet
```

### AWS Certificate Manager

```bash
# Request certificate
aws acm request-certificate \
  --domain-name complianceagent.your-domain.com \
  --validation-method DNS

# Certificate ARN is used in ALB configuration
```

---

## Monitoring & Logging

### Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Basic health check | `{"status": "healthy"}` |
| `/metrics` | Prometheus metrics | Prometheus text format |

### CloudWatch (AWS)

```hcl
# Terraform: CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "backend_cpu" {
  alarm_name          = "complianceagent-backend-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

### Prometheus + Grafana

```yaml
# Docker Compose addition
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## Scaling

### Horizontal Scaling

**ECS Auto Scaling:**
```hcl
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "backend-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

### Database Scaling

**Aurora Serverless v2:**
- Automatically scales from 0.5 to 128 ACUs
- Scales based on CPU and memory pressure
- Configure min/max capacity in Terraform

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check connectivity
docker exec backend python -c "from app.core.database import engine; print('OK')"

# Verify DATABASE_URL
echo $DATABASE_URL
```

**2. Celery Workers Not Processing**
```bash
# Check worker status
docker-compose logs celery-worker

# Verify Redis connection
redis-cli -h localhost ping
```

**3. Copilot API Errors**
```bash
# Check API key
curl -H "Authorization: Bearer $COPILOT_API_KEY" \
  https://api.githubcopilot.com/v1/models

# Check backend logs for rate limiting
docker-compose logs backend | grep -i copilot
```

**4. High Memory Usage**
```bash
# Check container stats
docker stats

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

### Log Locations

| Deployment | Location |
|------------|----------|
| Docker Compose | `docker-compose logs <service>` |
| AWS ECS | CloudWatch Logs `/ecs/complianceagent/*` |
| Kubernetes | `kubectl logs -f deploy/complianceagent-backend` |

---

## Next Steps

- Configure [CI/CD Integration](../guides/cicd-integration.md)
- Set up [Monitoring Dashboards](monitoring.md)
- Review [Security Hardening](security.md)
