---
sidebar_position: 2
title: Regulatory Monitoring
description: How ComplianceAgent tracks regulatory changes worldwide
---

# Regulatory Monitoring

ComplianceAgent continuously monitors 100+ regulatory sources, detecting changes and alerting you before they impact your business.

## How Monitoring Works

### Source Crawling

ComplianceAgent uses intelligent web crawlers to monitor official regulatory sources:

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────┐ │
│  │  Crawler │───▶│ Content  │───▶│  Change  │───▶│ Alert │ │
│  │          │    │ Extract  │    │ Detect   │    │       │ │
│  └──────────┘    └──────────┘    └──────────┘    └───────┘ │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Regulatory Source Types                  │  │
│  │  • Government portals (EUR-Lex, Federal Register)    │  │
│  │  • Regulatory bodies (EDPB, FTC, ICO)                │  │
│  │  • Standards organizations (ISO, NIST)               │  │
│  │  • Industry groups (PCI SSC)                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Crawling Technologies

Different sources require different approaches:

| Source Type | Technology | Example |
|-------------|------------|---------|
| Static HTML | HTTPX | Simple government pages |
| JavaScript-heavy | Playwright | Modern portals, SPAs |
| PDF documents | PDF extraction | Official gazettes |
| RSS/Atom feeds | Feed parser | News and updates |
| APIs | REST client | Some regulatory APIs |

### Crawl Frequency

Sources are monitored at appropriate intervals:

| Category | Frequency | Examples |
|----------|-----------|----------|
| Critical | Every 6 hours | EUR-Lex, Federal Register |
| Important | Daily | National DPAs, sector regulators |
| Standard | Weekly | Standards bodies, guidance |
| Archive | Monthly | Historical references |

## Change Detection

### Content Hashing

Every page is hashed to detect changes:

```python
# Simplified change detection logic
def detect_changes(source_url):
    current_content = fetch_content(source_url)
    current_hash = hash_content(current_content)
    
    previous_hash = get_stored_hash(source_url)
    
    if current_hash != previous_hash:
        # Change detected
        diff = compute_diff(previous_content, current_content)
        trigger_alert(source_url, diff)
        store_new_version(source_url, current_content, current_hash)
```

### Semantic Change Analysis

Not all changes matter. ComplianceAgent filters out:

- **Style changes** - CSS updates, layout modifications
- **Navigation changes** - Menu restructuring
- **Boilerplate changes** - Cookie notices, footers

And highlights:

- **Substantive text changes** - New or modified requirements
- **New documents** - Added regulations or guidance
- **Effective date changes** - Compliance timeline updates

## Monitored Sources

### Privacy Regulations

| Region | Source | URL | Frameworks |
|--------|--------|-----|------------|
| EU | EUR-Lex | eur-lex.europa.eu | GDPR |
| EU | EDPB | edpb.europa.eu | GDPR guidance |
| US | FTC | ftc.gov | FTC Act, COPPA |
| US-CA | CA AG | oag.ca.gov | CCPA/CPRA |
| UK | ICO | ico.org.uk | UK GDPR |
| Singapore | PDPC | pdpc.gov.sg | PDPA |
| India | MeitY | meity.gov.in | DPDP |

### Security Standards

| Source | URL | Frameworks |
|--------|-----|------------|
| PCI SSC | pcisecuritystandards.org | PCI-DSS |
| ISO | iso.org | ISO 27001, ISO 42001 |
| NIST | nist.gov | NIST CSF, AI RMF |
| ENISA | enisa.europa.eu | NIS2 |
| SOC | aicpa.org | SOC 2 |

### AI Regulation

| Source | URL | Frameworks |
|--------|-----|------------|
| EU | digital-strategy.ec.europa.eu | EU AI Act |
| US | ai.gov | NIST AI RMF |
| OECD | oecd.ai | OECD AI Principles |

### ESG & Sustainability

| Source | URL | Frameworks |
|--------|-----|------------|
| EFRAG | efrag.org | CSRD/ESRS |
| SEC | sec.gov | Climate Disclosure |
| TCFD | fsb-tcfd.org | TCFD |

## Predictive Intelligence

Beyond tracking current changes, ComplianceAgent predicts upcoming regulations.

### Signal Sources

The prediction engine monitors:

- **Legislative pipelines** - Bills in progress
- **Consultation papers** - Proposed rules
- **Regulatory statements** - Forward guidance
- **Industry reports** - Expert analysis
- **International trends** - Cross-border patterns

### Prediction Model

```
┌─────────────────────────────────────────────────────────────┐
│                   Prediction Engine                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Inputs:                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Legislative │ │ Regulatory  │ │  Industry   │           │
│  │  Activity   │ │  Signals    │ │   Trends    │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │                   │
│         └───────────────┼───────────────┘                   │
│                         ▼                                    │
│              ┌─────────────────────┐                        │
│              │    ML Prediction    │                        │
│              │       Model         │                        │
│              └──────────┬──────────┘                        │
│                         │                                    │
│  Outputs:               ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Predicted regulation: AI liability rules          │   │
│  │ • Probability: 78%                                  │   │
│  │ • Estimated timeframe: 12-18 months                 │   │
│  │ • Likely requirements: Algorithmic audits           │   │
│  │ • Preparation recommendations: Start documentation  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Advance Warnings

Predictions are surfaced as advance warnings:

```json
{
  "prediction_id": "pred_2024_ai_liability",
  "title": "EU AI Liability Directive",
  "probability": 0.78,
  "timeframe": {
    "earliest": "2025-06",
    "latest": "2026-03"
  },
  "key_requirements": [
    "Algorithmic impact assessments",
    "AI system documentation",
    "Human oversight mechanisms"
  ],
  "affected_industries": ["technology", "finance", "healthcare"],
  "preparation_steps": [
    "Document AI systems in use",
    "Establish AI governance framework",
    "Create algorithmic audit procedures"
  ]
}
```

## Alert Configuration

### Alert Types

| Type | Description | Example |
|------|-------------|---------|
| New Regulation | New regulatory document published | New GDPR guidance |
| Amendment | Existing regulation modified | CCPA amendment |
| Effective Date | Compliance deadline approaching | 6 months to EU AI Act |
| Prediction | New regulatory prediction | Expected AI rules |

### Notification Channels

Configure alerts via:

- **Email** - Daily digest or immediate
- **Slack** - Channel or DM notifications
- **Webhook** - Custom integrations
- **Dashboard** - In-app notifications

### Alert Rules

Create custom alert rules:

```yaml
# Example alert configuration
alerts:
  - name: "GDPR Critical Changes"
    frameworks: ["gdpr"]
    severity: ["high", "critical"]
    channels: ["slack", "email"]
    immediate: true
    
  - name: "Weekly Digest"
    frameworks: ["*"]
    severity: ["*"]
    channels: ["email"]
    schedule: "weekly"
    day: "monday"
```

## Working with Monitored Data

### Dashboard View

The Regulations dashboard shows:

- **Recent changes** - Chronological change feed
- **Framework status** - Per-framework update summary
- **Predictions** - Upcoming regulatory predictions
- **Source health** - Monitoring status for each source

### API Access

Access monitoring data programmatically:

```bash
# Get recent changes
curl -X GET "http://localhost:8000/api/v1/monitoring/changes?days=7" \
  -H "Authorization: Bearer $TOKEN"

# Get predictions
curl -X GET "http://localhost:8000/api/v1/predictions" \
  -H "Authorization: Bearer $TOKEN"
```

### Webhooks

Receive real-time notifications:

```bash
# Configure webhook
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "https://your-app.com/compliance-webhook",
    "events": ["regulation.changed", "prediction.new"],
    "secret": "webhook-secret"
  }'
```

## Custom Sources

Add custom regulatory sources for industry-specific monitoring:

```bash
# Add custom source
curl -X POST "http://localhost:8000/api/v1/monitoring/sources" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Industry Regulator",
    "url": "https://regulator.example.com/guidance",
    "crawl_frequency": "daily",
    "content_selector": ".guidance-content",
    "frameworks": ["custom-framework"]
  }'
```

## Source Health Monitoring

ComplianceAgent monitors the health of each source:

| Status | Description | Action |
|--------|-------------|--------|
| 🟢 Healthy | Source accessible, content fresh | None |
| 🟡 Degraded | Intermittent issues | Automatic retry |
| 🔴 Down | Source unreachable | Alert + manual check |
| ⚪ Stale | No updates in expected timeframe | Review source |

View source health:

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/health" \
  -H "Authorization: Bearer $TOKEN"
```

---

Next: Learn how [AI Parsing](./ai-parsing) transforms legal text into actionable requirements.
