---
sidebar_position: 1
title: Docker Deployment
description: Deploy ComplianceAgent with Docker Compose
---

# Docker Deployment

The fastest way to deploy ComplianceAgent for development and small-scale production.

## Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- 8GB RAM minimum
- 50GB disk space

## Quick Start

```bash
# Clone repository
git clone https://github.com/complianceagent/complianceagent.git
cd complianceagent

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Start all services
docker compose up -d
```

Access the dashboard at `http://localhost:3000`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │        │
│  │   (Next.js)  │     │   (FastAPI)  │     │              │        │
│  │   :3000      │     │   :8000      │     │   :5432      │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                              │                                       │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │    Redis     │◀────│    Worker    │────▶│Elasticsearch │        │
│  │   (Cache)    │     │   (Celery)   │     │   (Search)   │        │
│  │   :6379      │     │              │     │   :9200      │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Configuration

### Required Environment Variables

```bash
# .env file
# Application
SECRET_KEY=your-secret-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/complianceagent
POSTGRES_USER=complianceagent
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=complianceagent

# Redis
REDIS_URL=redis://redis:6379/0

# GitHub Copilot SDK
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Optional: Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200
```

### Full docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - ELASTICSEARCH_URL=${ELASTICSEARCH_URL}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker worker -l info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    depends_on:
      - backend
      - redis
    restart: unless-stopped

  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker beat -l info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - worker
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
```

## Operations

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Service Management

```bash
# Stop all services
docker compose down

# Stop and remove volumes (data loss!)
docker compose down -v

# Restart single service
docker compose restart backend

# Scale workers
docker compose up -d --scale worker=3
```

### Database Operations

```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Create database backup
docker compose exec postgres pg_dump -U complianceagent complianceagent > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U complianceagent complianceagent

# Access psql shell
docker compose exec postgres psql -U complianceagent
```

### Health Checks

```bash
# Check service status
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Check all endpoints
curl http://localhost:8000/health/ready
```

## Production Considerations

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Secrets Management

Use Docker secrets instead of environment variables:

```yaml
services:
  backend:
    secrets:
      - db_password
      - github_token
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password

secrets:
  db_password:
    external: true
  github_token:
    external: true
```

### TLS/SSL

Use a reverse proxy like Traefik or nginx:

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - letsencrypt:/letsencrypt

  frontend:
    labels:
      - "traefik.http.routers.frontend.rule=Host(`compliance.example.com`)"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

### Logging

Configure structured logging:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Or ship to external service:

```yaml
services:
  backend:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "localhost:24224"
        tag: "complianceagent.backend"
```

## Upgrades

### Standard Upgrade

```bash
# Pull latest images
docker compose pull

# Recreate containers
docker compose up -d

# Run migrations
docker compose exec backend alembic upgrade head
```

### Zero-Downtime Upgrade

```bash
# Scale up new version
docker compose up -d --scale backend=2 --no-recreate

# Wait for health check
sleep 30

# Remove old container
docker compose up -d --scale backend=1
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs backend

# Check configuration
docker compose config

# Validate compose file
docker compose config --quiet
```

### Database Connection Failed

```bash
# Verify postgres is running
docker compose ps postgres

# Test connection
docker compose exec postgres pg_isready

# Check credentials
docker compose exec backend env | grep DATABASE
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase limits or add swap
sudo sysctl vm.swappiness=10
```

---

See also: [AWS Deployment](./aws) | [Kubernetes Deployment](./kubernetes) | [Environment Variables](./environment-variables)
