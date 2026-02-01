---
sidebar_position: 2
title: Tracking Regulations
description: Enable and monitor regulatory frameworks for your organization
---

# Tracking Regulations

This guide shows you how to enable, configure, and monitor regulatory frameworks in ComplianceAgent.

## Understanding Frameworks

ComplianceAgent supports 100+ regulatory frameworks organized by category:

| Category | Examples |
|----------|----------|
| **Privacy** | GDPR, CCPA, HIPAA, PDPA, LGPD |
| **Security** | PCI-DSS, SOC 2, ISO 27001, NIS2 |
| **AI/ML** | EU AI Act, NIST AI RMF, ISO 42001 |
| **ESG** | CSRD, TCFD, SEC Climate |
| **Industry** | HIPAA (Healthcare), GLBA (Finance) |

## Enabling a Framework

### Step 1: Navigate to Regulations

1. Go to **Regulations** in the sidebar
2. Browse frameworks by category or search

### Step 2: Review Framework Details

Before enabling, review what the framework includes:

```
┌─────────────────────────────────────────────────────────────────┐
│                           GDPR                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  General Data Protection Regulation                              │
│  Jurisdiction: European Union                                    │
│  Effective: May 25, 2018                                        │
│                                                                  │
│  Requirements: 127                                               │
│  Categories:                                                     │
│  ├── Data Subject Rights (32)                                   │
│  ├── Consent (18)                                               │
│  ├── Security Measures (24)                                     │
│  ├── Data Processing (28)                                       │
│  └── Breach Notification (25)                                   │
│                                                                  │
│  Monitored Sources:                                              │
│  • EUR-Lex (primary source)                                     │
│  • EDPB (guidance)                                              │
│  • National DPAs (local interpretation)                         │
│                                                                  │
│  [Enable Framework]                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Enable for Your Organization

1. Click **Enable Framework**
2. Configure framework-specific settings:

```yaml
# GDPR Configuration Example
gdpr:
  # Which repositories to apply to
  repositories:
    - acme/backend
    - acme/web-app
  
  # Specific requirement categories to enable
  categories:
    - data_subject_rights
    - consent
    - security_measures
    - breach_notification
  
  # Jurisdiction specifics
  jurisdiction:
    primary: EU
    include_national:
      - DE   # German BDSG
      - FR   # French CNIL guidance
```

3. Click **Save Configuration**

## Framework Configuration

### Selecting Applicable Requirements

Not all requirements apply to every organization. Customize what's relevant:

#### By Business Type

```yaml
# E-commerce company
gdpr:
  applicable_requirements:
    include:
      - consent
      - data_processing
      - marketing
      - international_transfers
    exclude:
      - employee_data  # Handled separately
      - dpo_mandatory  # Under threshold
```

#### By Data Types

```yaml
# Healthcare application
hipaa:
  data_types:
    - protected_health_information
    - patient_identifiers
    - medical_records
  
  excluded_data:
    - administrative_only
    - de_identified
```

### Setting Compliance Thresholds

Configure when to alert:

```yaml
thresholds:
  compliance_score:
    critical: 70    # Below this = critical alert
    warning: 85     # Below this = warning
    target: 95      # Goal to achieve
  
  gap_severity:
    critical_max: 0      # No critical gaps allowed
    high_max: 3          # Max 3 high gaps
    medium_max: 10       # Max 10 medium gaps
```

## Monitoring Changes

### Real-Time Monitoring

ComplianceAgent continuously monitors regulatory sources:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Regulatory Feed                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔔 Today                                                        │
│  ├── EDPB releases AI Act guidance integration             2h   │
│  └── California AG updates CCPA FAQ                        6h   │
│                                                                  │
│  📅 This Week                                                    │
│  ├── PCI SSC releases v4.0.1 clarifications               2d   │
│  ├── ICO updates international transfer guidance           3d   │
│  └── NIST updates AI RMF profiles                         5d   │
│                                                                  │
│  [View All Changes]                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Change Notifications

Configure how you're notified:

```yaml
notifications:
  channels:
    - type: email
      recipients:
        - compliance@acme.com
        - legal@acme.com
      frequency: immediate  # or daily_digest
    
    - type: slack
      webhook: https://hooks.slack.com/...
      channel: "#compliance-alerts"
      frequency: immediate
      
    - type: webhook
      url: https://your-system.com/compliance-webhook
      events:
        - regulation.changed
        - requirement.added
        - deadline.approaching
```

### Change Impact Analysis

When regulations change, see how it affects you:

```
┌─────────────────────────────────────────────────────────────────┐
│              Change Impact: GDPR Art. 22 Update                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Change: New EDPB guidance on automated decision-making          │
│  Date: January 15, 2024                                          │
│  Source: EDPB Guidelines 03/2024                                 │
│                                                                  │
│  Impact on Your Organization:                                    │
│  ─────────────────────────────                                   │
│  Affected Repositories: 2                                        │
│  ├── acme/ml-service (HIGH)                                     │
│  │   └── Automated credit scoring requires review               │
│  └── acme/backend (MEDIUM)                                      │
│      └── Recommendation engine needs disclosure                 │
│                                                                  │
│  New Requirements:                                               │
│  • Meaningful information about decision logic                   │
│  • Right to human intervention                                   │
│  • Regular algorithm audits                                      │
│                                                                  │
│  Recommended Actions:                                            │
│  ├── Review automated decision systems                          │
│  ├── Add explainability to ML models                            │
│  └── Implement human review process                             │
│                                                                  │
│  [Generate Compliance Tasks] [Dismiss]                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Compliance Dashboard

### Organization Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Compliance Overview                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Overall Score: 87%                                              │
│                                                                  │
│  By Framework:                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ GDPR      ████████████████████████░░░░░  89%  ⚠ 3 gaps     │ │
│  │ CCPA      █████████████████████████░░░░  92%  ✓ compliant  │ │
│  │ HIPAA     ██████████████████████░░░░░░░  84%  ⚠ 5 gaps     │ │
│  │ PCI-DSS   ███████████████████░░░░░░░░░░  78%  ⚠ 8 gaps     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Critical Gaps: 2       High: 7       Medium: 12                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Framework Detail View

Drill into specific frameworks:

```
┌─────────────────────────────────────────────────────────────────┐
│                        GDPR Status                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Score: 89% (+2% from last week)                                │
│                                                                  │
│  By Category:                                                    │
│  ├── Data Subject Rights    92%  ✓                              │
│  ├── Consent               95%  ✓                              │
│  ├── Security              88%  ⚠                              │
│  ├── Data Processing       91%  ✓                              │
│  └── Breach Notification   78%  ⚠                              │
│                                                                  │
│  Gaps by Severity:                                              │
│  ├── 🔴 Critical: 0                                             │
│  ├── 🟠 High: 1 (Art. 33 - breach notification)                 │
│  ├── 🟡 Medium: 2                                               │
│  └── 🔵 Low: 4                                                  │
│                                                                  │
│  [View All Requirements] [Export Report] [Generate Fixes]        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Requirement Management

### Viewing Requirements

Browse all requirements for a framework:

```bash
# API: List requirements
curl -X GET "http://localhost:8000/api/v1/regulations/gdpr/requirements" \
  -H "Authorization: Bearer $TOKEN"
```

Response:

```json
{
  "framework": "gdpr",
  "total": 127,
  "requirements": [
    {
      "id": "gdpr-art-7-1",
      "article": "Article 7(1)",
      "text": "Controller shall be able to demonstrate consent",
      "category": "consent",
      "obligation_type": "MUST",
      "status": "met",
      "mapped_files": 3
    }
  ]
}
```

### Filtering Requirements

Filter by various criteria:

```bash
# Get unmet requirements
curl -X GET "http://localhost:8000/api/v1/regulations/gdpr/requirements?status=gap" \
  -H "Authorization: Bearer $TOKEN"

# Get by category
curl -X GET "http://localhost:8000/api/v1/regulations/gdpr/requirements?category=consent" \
  -H "Authorization: Bearer $TOKEN"

# Get by severity
curl -X GET "http://localhost:8000/api/v1/regulations/gdpr/requirements?severity=high" \
  -H "Authorization: Bearer $TOKEN"
```

### Manual Status Override

Mark requirements manually when automated detection isn't possible:

```bash
curl -X PATCH "http://localhost:8000/api/v1/requirements/{req_id}/status" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "status": "met",
    "evidence": "Implemented via external DPO service - contract attached",
    "evidence_url": "https://confluence.acme.com/dpo-contract"
  }'
```

## Scheduled Reports

### Configure Automated Reports

```yaml
reports:
  weekly_summary:
    schedule: "0 9 * * MON"  # Every Monday at 9am
    recipients:
      - compliance@acme.com
    include:
      - compliance_scores
      - new_gaps
      - resolved_gaps
      - regulatory_changes
  
  monthly_executive:
    schedule: "0 9 1 * *"  # First of month
    recipients:
      - cto@acme.com
      - legal@acme.com
    format: pdf
    include:
      - executive_summary
      - trend_analysis
      - upcoming_deadlines
```

### Generate On-Demand Reports

```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "type": "compliance_summary",
    "frameworks": ["gdpr", "ccpa"],
    "format": "pdf",
    "include_evidence": true
  }'
```

## Best Practices

### 1. Start with Applicable Frameworks

Don't enable everything. Start with frameworks that legally apply to you.

### 2. Configure Thresholds Appropriately

Set realistic thresholds based on your risk tolerance and resources.

### 3. Assign Ownership

Designate framework owners responsible for monitoring and remediation.

### 4. Review Changes Weekly

Even with automated monitoring, review the change feed regularly.

### 5. Keep Evidence Updated

When manually marking requirements as met, attach current evidence.

---

Next: Learn how to [Generate Compliance Code](./generating-compliance-code) to fix identified gaps.
