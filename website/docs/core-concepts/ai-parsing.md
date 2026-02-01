---
sidebar_position: 3
title: AI Parsing
description: How ComplianceAgent uses AI to extract requirements from legal text
---

# AI-Powered Parsing

ComplianceAgent uses GitHub Copilot SDK to transform dense legal documents into structured, actionable requirements.

## The Challenge

Legal text is notoriously difficult to parse:

```
"The controller shall implement appropriate technical and organisational 
measures to ensure a level of security appropriate to the risk, including 
inter alia as appropriate: (a) the pseudonymisation and encryption of 
personal data; (b) the ability to ensure the ongoing confidentiality, 
integrity, availability and resilience of processing systems..."
```

This paragraph contains multiple requirements, but they're buried in legalese.

## How Parsing Works

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Parsing Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Legal Text                                                  │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────┐               │
│  │         1. Document Chunking              │               │
│  │    Split into processable segments        │               │
│  └──────────────────────────────────────────┘               │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────┐               │
│  │         2. Obligation Extraction          │               │
│  │    Identify MUST/SHOULD/MAY statements    │               │
│  └──────────────────────────────────────────┘               │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────┐               │
│  │         3. Entity Recognition             │               │
│  │    Extract actors, data types, actions    │               │
│  └──────────────────────────────────────────┘               │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────┐               │
│  │         4. Categorization                 │               │
│  │    Assign compliance categories           │               │
│  └──────────────────────────────────────────┘               │
│      │                                                       │
│      ▼                                                       │
│  Structured Requirements                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: Document Chunking

Large documents are split into processable segments:

- **Section-aware splitting** - Respects document structure
- **Context preservation** - Maintains references and definitions
- **Overlap handling** - Ensures continuity between chunks

### Step 2: Obligation Extraction

The AI identifies obligation types:

| Keyword | Obligation Type | Enforcement |
|---------|-----------------|-------------|
| shall, must, required | **MUST** | Mandatory |
| should, recommended | **SHOULD** | Best practice |
| may, optional | **MAY** | Permitted |

Example extraction:

```
Input: "The controller shall implement appropriate technical measures"

Output:
{
  "text": "implement appropriate technical measures",
  "obligation_type": "MUST",
  "actor": "controller",
  "action": "implement",
  "object": "technical measures"
}
```

### Step 3: Entity Recognition

Key entities are extracted:

| Entity Type | Examples |
|-------------|----------|
| **Actors** | controller, processor, data subject, supervisory authority |
| **Data Types** | personal data, sensitive data, health data, biometric data |
| **Actions** | process, store, transfer, delete, encrypt |
| **Timeframes** | 72 hours, 30 days, without undue delay |
| **Conditions** | upon request, where applicable, unless |

### Step 4: Categorization

Requirements are categorized for easier management:

```python
REQUIREMENT_CATEGORIES = [
    "data_collection",
    "data_processing",
    "data_storage",
    "data_transfer",
    "data_deletion",
    "consent_management",
    "data_subject_rights",
    "security_measures",
    "breach_notification",
    "documentation",
    "dpo_appointment",
    "impact_assessment",
]
```

## Structured Output

The parsing pipeline produces structured requirements:

```json
{
  "requirement_id": "gdpr-art-32-1-a",
  "source": {
    "regulation": "GDPR",
    "article": "Article 32(1)(a)",
    "full_citation": "Regulation (EU) 2016/679, Article 32(1)(a)"
  },
  "text": {
    "original": "the pseudonymisation and encryption of personal data",
    "simplified": "Encrypt and pseudonymize personal data"
  },
  "obligation": {
    "type": "MUST",
    "actor": "controller",
    "action": "implement",
    "object": "pseudonymisation and encryption",
    "target": "personal data"
  },
  "entities": {
    "data_types": ["personal_data"],
    "technical_measures": ["pseudonymisation", "encryption"],
    "actors": ["controller"]
  },
  "category": "security_measures",
  "subcategory": "encryption",
  "metadata": {
    "parsed_at": "2024-01-15T10:30:00Z",
    "confidence": 0.94,
    "model_version": "copilot-2024-01"
  }
}
```

## Confidence Scoring

Every extracted requirement includes a confidence score:

| Score Range | Meaning | Action |
|-------------|---------|--------|
| 0.90 - 1.00 | High confidence | Auto-approve |
| 0.75 - 0.89 | Medium confidence | Quick review |
| 0.50 - 0.74 | Low confidence | Manual review |
| Below 0.50 | Uncertain | Expert review |

Factors affecting confidence:

- **Language clarity** - Clear obligations score higher
- **Context availability** - More context improves accuracy
- **Pattern matching** - Known patterns boost confidence
- **Cross-reference** - Verified against other requirements

## GitHub Copilot SDK Integration

ComplianceAgent uses GitHub Copilot SDK for AI operations:

```python
from copilot_sdk import CopilotClient

client = CopilotClient(api_key=settings.COPILOT_API_KEY)

# Parse legal text
result = client.complete(
    prompt=f"""
    Extract compliance requirements from this legal text.
    Return structured JSON with obligation type, actors, and actions.
    
    Text: {legal_text}
    """,
    max_tokens=2000,
    temperature=0.1,  # Low temperature for consistency
)

requirements = parse_copilot_response(result)
```

### Prompt Engineering

Effective prompts for legal parsing:

```python
EXTRACTION_PROMPT = """
You are a legal compliance expert. Analyze the following regulatory text 
and extract structured compliance requirements.

For each requirement, identify:
1. Obligation type (MUST/SHOULD/MAY)
2. Actor (who must comply)
3. Action (what must be done)
4. Object (what is affected)
5. Conditions (when/where applicable)
6. Timeframe (if specified)

Return JSON array of requirements.

Regulatory text:
{text}

Article reference: {article}
Regulation: {regulation}
"""
```

## Handling Complex Structures

### Cross-References

Legal documents often reference other sections:

```
"Subject to the derogations in Article 89(2), data subjects shall have 
the right to obtain from the controller..."
```

The parser:
1. Identifies the cross-reference (Article 89(2))
2. Fetches the referenced text
3. Includes the derogation in the requirement context

### Nested Conditions

Complex conditional structures are unwound:

```
Input: "Where processing is based on consent, the controller shall be 
able to demonstrate that the data subject has consented..."

Output:
{
  "condition": "processing based on consent",
  "requirement": "demonstrate data subject consent",
  "applies_when": ["consent_based_processing"]
}
```

### Lists and Enumerations

Bullet points and lists are parsed into individual requirements:

```
Input: "appropriate measures including: (a) encryption; (b) access controls..."

Output: [
  { "requirement": "implement encryption", "parent": "art-32-1" },
  { "requirement": "implement access controls", "parent": "art-32-1" }
]
```

## Multi-Language Support

ComplianceAgent handles regulations in multiple languages:

| Language | Support Level | Source Regulations |
|----------|--------------|-------------------|
| English | Full | GDPR, CCPA, HIPAA |
| German | Full | DSGVO, BDSG |
| French | Full | RGPD (FR) |
| Spanish | Partial | RGPD (ES), LOPDGDD |
| Other EU | Partial | Official translations |

For non-English documents:
1. Original text is preserved
2. AI-assisted translation for processing
3. Requirements linked to original citations

## Quality Assurance

### Validation Rules

Extracted requirements are validated:

```python
def validate_requirement(req):
    errors = []
    
    # Must have obligation type
    if req.obligation_type not in ["MUST", "SHOULD", "MAY"]:
        errors.append("Invalid obligation type")
    
    # Must have actor
    if not req.actor:
        errors.append("Missing actor")
    
    # Must have action
    if not req.action:
        errors.append("Missing action")
    
    # Must have source citation
    if not req.source_article:
        errors.append("Missing source citation")
    
    return len(errors) == 0, errors
```

### Human Review Queue

Low-confidence requirements enter a review queue:

1. **Compliance team** reviews flagged requirements
2. **Corrections** improve future parsing
3. **Feedback loop** enhances model accuracy

### Version Control

Requirements are versioned when regulations change:

```json
{
  "requirement_id": "gdpr-art-17-1",
  "version": 2,
  "effective_date": "2024-01-01",
  "previous_version": 1,
  "changes": ["Added exception for legal claims"],
  "changelog": "Updated per EDPB guidance 2023/12"
}
```

## Performance Metrics

Track parsing quality:

| Metric | Target | Description |
|--------|--------|-------------|
| Extraction accuracy | >95% | Correct obligation identification |
| Entity precision | >90% | Correct entity extraction |
| Category accuracy | >92% | Correct categorization |
| Processing time | &lt;5s/page | Speed of parsing |
| Confidence calibration | ±5% | Confidence matches accuracy |

View metrics in the dashboard under **Settings → AI Performance**.

---

Next: Learn how [Codebase Mapping](./codebase-mapping) connects requirements to your code.
