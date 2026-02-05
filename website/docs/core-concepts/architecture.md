---
sidebar_position: 2
title: Architecture
description: Interactive visual diagram of ComplianceAgent's architecture
---

import ArchitectureDiagram from '@site/src/components/HomepageFeatures/ArchitectureDiagram';

# System Architecture

ComplianceAgent uses a modular, microservices-based architecture designed for scalability, security, and maintainability.

## Interactive Architecture Diagram

Click or hover over components to learn more about each system:

<ArchitectureDiagram />

## Component Overview

### Core Pipeline

The core pipeline processes regulatory data through four main stages:

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Monitor** | Crawls 100+ regulatory sources | Python, Scrapy, Celery |
| **Parser** | Extracts structured requirements | LLMs (GPT-4, Claude), spaCy |
| **Mapper** | Maps requirements to code | AST analysis, semantic search |
| **Generator** | Creates compliant code fixes | Code LLMs, tree-sitter |

### Supporting Services

| Service | Purpose | Technology |
|---------|---------|------------|
| **Audit Trail** | Tamper-proof logging | PostgreSQL, hash chains |
| **REST API** | External integrations | FastAPI, JWT auth |
| **Background Jobs** | Async processing | Celery, Redis |
| **Search** | Full-text search | Elasticsearch |

## Data Stores

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │Elasticsearch│  │    Redis    │         │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤         │
│  │• Regulations│  │• Full-text  │  │• Job queues │         │
│  │• Requirements│ │  search     │  │• Rate limits│         │
│  │• Mappings   │  │• Fuzzy      │  │• Sessions   │         │
│  │• Audit logs │  │  matching   │  │• Caching    │         │
│  │• Users/orgs │  │• Aggregation│  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Options

### Docker Compose (Development)

Quick local setup with all services:

```bash
docker compose up -d
```

### Kubernetes (Production)

Fully orchestrated with:
- Horizontal pod autoscaling
- Rolling deployments
- Health checks and self-healing
- Secrets management
- Ingress with TLS

See [Kubernetes Deployment Guide](/docs/deployment/kubernetes) for details.

### Cloud-Native (AWS)

Managed services for lower operational overhead:
- **ECS/Fargate** for containers
- **RDS** for PostgreSQL
- **OpenSearch** for search
- **ElastiCache** for Redis
- **CloudWatch** for monitoring

See [AWS Deployment Guide](/docs/deployment/aws) for details.

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Security Layers                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Network Security                       │   │
│  │  • WAF / DDoS protection                            │   │
│  │  • TLS 1.3 everywhere                               │   │
│  │  • VPC isolation                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Application Security                    │   │
│  │  • JWT authentication                               │   │
│  │  • Role-based access control (RBAC)                 │   │
│  │  • API rate limiting                                │   │
│  │  • Input validation                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Data Security                         │   │
│  │  • Encryption at rest (AES-256)                     │   │
│  │  • Multi-tenant isolation                           │   │
│  │  • Tamper-proof audit logs                          │   │
│  │  • Secrets in HashiCorp Vault / AWS Secrets Manager │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Scalability

ComplianceAgent scales horizontally at each layer:

| Component | Scaling Strategy |
|-----------|------------------|
| API servers | Horizontal scaling behind load balancer |
| Workers | Celery workers scale based on queue depth |
| Database | Read replicas, connection pooling |
| Search | Elasticsearch cluster with sharding |
| Cache | Redis cluster with replication |

### Typical Production Sizing

| Workload | API Pods | Workers | Database |
|----------|----------|---------|----------|
| Small (10 repos) | 2 | 2 | db.t3.medium |
| Medium (100 repos) | 4 | 8 | db.r5.large |
| Large (500+ repos) | 8+ | 16+ | db.r5.xlarge |

## Integration Points

```
                    ┌─────────────────────┐
                    │  ComplianceAgent    │
                    │       API           │
                    └─────────┬───────────┘
                              │
        ┌─────────┬───────────┼───────────┬─────────┐
        │         │           │           │         │
        ▼         ▼           ▼           ▼         ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ GitHub │ │ GitLab │ │ CI/CD  │ │  Slack │ │  IDE   │
   │        │ │        │ │(Actions│ │        │ │Extension│
   │        │ │        │ │Jenkins)│ │        │ │        │
   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

## Next Steps

- [Getting Started](/docs/getting-started/installation) - Set up ComplianceAgent
- [API Reference](/docs/api/overview) - Explore the API
- [Deployment](/docs/deployment/docker) - Deploy to production
