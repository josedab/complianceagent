---
sidebar_position: 1
title: Frameworks Overview
description: Supported regulatory frameworks and compliance standards
---

# Frameworks Overview

ComplianceAgent supports 100+ regulatory frameworks across privacy, security, AI, and ESG domains.

## Framework Categories

### Privacy & Data Protection

Regulations governing personal data handling:

| Framework | Jurisdiction | Key Focus |
|-----------|--------------|-----------|
| [GDPR](./gdpr) | European Union | Comprehensive data protection |
| [CCPA/CPRA](./ccpa) | California, USA | Consumer privacy rights |
| [HIPAA](./hipaa) | USA (Healthcare) | Protected health information |
| PDPA | Singapore | Personal data protection |
| LGPD | Brazil | Data protection law |
| PIPA | South Korea | Personal information protection |
| APPI | Japan | Personal information protection |
| PIPL | China | Personal information protection |

### Security Standards

Standards for information security and controls:

| Framework | Scope | Key Focus |
|-----------|-------|-----------|
| [PCI-DSS v4.0](./pci-dss) | Payment Card Industry | Cardholder data security |
| [SOC 2](./soc2) | Service Organizations | Trust services criteria |
| ISO 27001:2022 | Global | Information security management |
| NIS2 | European Union | Network and information security |
| NIST CSF | USA | Cybersecurity framework |

### AI & Machine Learning

Emerging regulations for AI systems:

| Framework | Jurisdiction | Key Focus |
|-----------|--------------|-----------|
| [EU AI Act](./eu-ai-act) | European Union | AI system regulation |
| NIST AI RMF | USA | AI risk management |
| ISO 42001 | Global | AI management system |

### ESG & Sustainability

Environmental, social, and governance reporting:

| Framework | Jurisdiction | Key Focus |
|-----------|--------------|-----------|
| CSRD/ESRS | European Union | Corporate sustainability reporting |
| SEC Climate | USA | Climate-related disclosures |
| TCFD | Global | Climate financial disclosures |

## Enabling Frameworks

### Via Dashboard

1. Navigate to **Regulations**
2. Browse or search for frameworks
3. Click **Enable** on desired framework
4. Configure framework-specific settings

### Via Configuration

```yaml
# .complianceagent/config.yml
frameworks:
  enabled:
    - gdpr
    - ccpa
    - hipaa
    - pci-dss
    - soc2
```

## Framework Status

Each framework has a status indicating ComplianceAgent support:

| Status | Meaning |
|--------|---------|
| ✅ Full Support | All requirements mapped, AI parsing, code generation |
| 🟡 Partial | Core requirements mapped, limited code generation |
| 🔜 Coming Soon | In development |

## Common Patterns

### Overlap Between Frameworks

Many frameworks share common requirements:

```
┌──────────────────────────────────────────────────────────────────┐
│                   Framework Overlap                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│                GDPR ◄─────┐                                       │
│                  │        │                                       │
│    Consent ──────┼────────┼──────── CCPA                         │
│    Data Access ──┼────────┼────────   │                          │
│    Deletion ─────┼────────┼────────   │                          │
│                  │        │           │                          │
│                  │   ┌────┴─────┐     │                          │
│                  │   │ Shared   │     │                          │
│                  │   │ Controls │     │                          │
│                  │   └────┬─────┘     │                          │
│                  │        │           │                          │
│    Encryption ───┼────────┼────────   │                          │
│    Audit Logs ───┼────────┼──────── HIPAA                        │
│    Access Ctrl ──┼────────┼────────   │                          │
│                  │        │           │                          │
│                  ▼        │           ▼                          │
│              PCI-DSS ◄────┴────── SOC 2                          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

When you implement a control for one framework, it often satisfies others.

### Multi-Framework Compliance

Configure how overlapping requirements are handled:

```yaml
frameworks:
  overlap_handling:
    # Apply the strictest requirement when frameworks conflict
    strategy: strictest
    
    # Or map explicitly
    mappings:
      encryption_at_rest:
        - gdpr.art_32
        - hipaa.security_rule
        - pci_dss.req_3
```

## Framework-Specific Documentation

Each framework has dedicated documentation covering:

1. **Overview** - What the framework covers
2. **Key Requirements** - Most important obligations
3. **Code Patterns** - How to implement compliance
4. **Templates** - Pre-built compliant code
5. **Common Gaps** - Frequently missed requirements

## Requesting New Frameworks

Need support for a framework not listed?

1. Go to **Settings → Feature Requests**
2. Select "New Framework"
3. Provide framework details
4. We prioritize based on demand

---

Explore framework-specific guides:

- [GDPR](./gdpr) - EU data protection
- [CCPA](./ccpa) - California privacy
- [HIPAA](./hipaa) - Healthcare data
- [EU AI Act](./eu-ai-act) - AI regulation
- [PCI-DSS](./pci-dss) - Payment security
- [SOC 2](./soc2) - Service organization controls
