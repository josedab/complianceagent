---
slug: /
sidebar_position: 1
title: Introduction
description: ComplianceAgent - AI-powered regulatory monitoring and code generation platform
---

# ComplianceAgent

**Autonomous Regulatory Monitoring and Adaptation Platform**

ComplianceAgent transforms compliance from a reactive burden into a proactive, automated workflow. Monitor 100+ regulatory frameworks, automatically map requirements to your codebase, and generate compliant code modifications—all powered by AI.

## Why ComplianceAgent?

- **Save hundreds of hours** per compliance cycle
- **Reduce risk** with automated gap analysis
- **Stay ahead** with predictive regulatory intelligence  
- **Maintain audit readiness** with comprehensive trails

## Quick Start

```bash
# Clone the repository
git clone https://github.com/josedab/complianceagent.git
cd complianceagent

# Start with Docker (recommended)
cp .env.example .env
cd docker && docker-compose up -d
```

Access the dashboard at `http://localhost:3000`.

## Supported Frameworks

ComplianceAgent supports 100+ regulatory frameworks including:

- **Privacy**: GDPR, CCPA, HIPAA, Singapore PDPA, India DPDP
- **Security**: PCI-DSS v4.0, SOC 2, ISO 27001:2022, NIS2
- **AI Regulation**: EU AI Act, NIST AI RMF, ISO 42001
- **ESG**: CSRD, SEC Climate Disclosure, TCFD

## Architecture at a Glance

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dashboard     │────▶│   Backend API   │────▶│   PostgreSQL    │
│   (Next.js)     │     │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Celery Workers │
                        └─────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Redis       │     │  Elasticsearch  │     │    S3/MinIO     │
│   (Cache/Queue) │     │    (Search)     │     │   (Documents)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## License

ComplianceAgent is released under the MIT License.
