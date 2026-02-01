---
sidebar_position: 3
title: Regulations API
description: API endpoints for regulatory frameworks and requirements
---

# Regulations API

Access regulatory frameworks, requirements, and updates.

## List Regulations

```bash
GET /api/v1/regulations
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category: `privacy`, `security`, `ai`, `esg` |
| `jurisdiction` | string | Filter by jurisdiction: `eu`, `us`, `global` |
| `enabled` | boolean | Filter by enabled status |
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 20, max: 100) |

### Example Request

```bash
curl -X GET "https://api.complianceagent.io/v1/regulations?category=privacy&jurisdiction=eu" \
  -H "Authorization: Bearer $TOKEN"
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "gdpr",
      "name": "General Data Protection Regulation",
      "short_name": "GDPR",
      "category": "privacy",
      "jurisdiction": "eu",
      "effective_date": "2018-05-25",
      "requirements_count": 127,
      "enabled": true,
      "last_updated": "2024-01-10T15:30:00Z"
    },
    {
      "id": "eu_ai_act",
      "name": "EU Artificial Intelligence Act",
      "short_name": "EU AI Act",
      "category": "ai",
      "jurisdiction": "eu",
      "effective_date": "2024-08-01",
      "requirements_count": 94,
      "enabled": true,
      "last_updated": "2024-01-12T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 127,
    "total_pages": 7
  }
}
```

## Get Regulation

```bash
GET /api/v1/regulations/{regulation_id}
```

### Example Request

```bash
curl -X GET "https://api.complianceagent.io/v1/regulations/gdpr" \
  -H "Authorization: Bearer $TOKEN"
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "gdpr",
    "name": "General Data Protection Regulation",
    "short_name": "GDPR",
    "description": "The EU's comprehensive data protection law governing personal data processing",
    "category": "privacy",
    "jurisdiction": "eu",
    "effective_date": "2018-05-25",
    "enforcement_authority": "National Data Protection Authorities",
    "penalties": {
      "maximum": "€20M or 4% global revenue",
      "penalty_type": "whichever_is_higher"
    },
    "requirements_count": 127,
    "official_sources": [
      {
        "name": "EUR-Lex",
        "url": "https://eur-lex.europa.eu/eli/reg/2016/679"
      },
      {
        "name": "EDPB Guidelines",
        "url": "https://edpb.europa.eu/our-work-tools/general-guidance"
      }
    ],
    "enabled": true,
    "last_updated": "2024-01-10T15:30:00Z"
  }
}
```

## Get Requirements

```bash
GET /api/v1/regulations/{regulation_id}/requirements
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category |
| `priority` | string | Filter by priority: `critical`, `high`, `medium`, `low` |
| `search` | string | Search in title and description |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

### Example Request

```bash
curl -X GET "https://api.complianceagent.io/v1/regulations/gdpr/requirements?category=data_subject_rights" \
  -H "Authorization: Bearer $TOKEN"
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "gdpr_art_15",
      "regulation_id": "gdpr",
      "article": "Article 15",
      "title": "Right of access by the data subject",
      "description": "The data subject shall have the right to obtain from the controller confirmation as to whether or not personal data concerning them is being processed...",
      "category": "data_subject_rights",
      "priority": "high",
      "implementation_guidance": [
        "Implement data export functionality",
        "Provide processing activity details",
        "Include third-party sharing information"
      ],
      "code_patterns": [
        "data_access_handler",
        "export_personal_data"
      ],
      "related_requirements": [
        "gdpr_art_12",
        "gdpr_art_20"
      ]
    },
    {
      "id": "gdpr_art_17",
      "regulation_id": "gdpr",
      "article": "Article 17",
      "title": "Right to erasure ('right to be forgotten')",
      "description": "The data subject shall have the right to obtain from the controller the erasure of personal data concerning them without undue delay...",
      "category": "data_subject_rights",
      "priority": "high",
      "implementation_guidance": [
        "Implement deletion across all systems",
        "Handle exceptions (legal obligations)",
        "Notify third parties of deletion"
      ],
      "code_patterns": [
        "deletion_handler",
        "cascade_delete"
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 8
  }
}
```

## Get Single Requirement

```bash
GET /api/v1/regulations/{regulation_id}/requirements/{requirement_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "gdpr_art_17",
    "regulation_id": "gdpr",
    "article": "Article 17",
    "title": "Right to erasure ('right to be forgotten')",
    "full_text": "1. The data subject shall have the right to obtain from the controller the erasure of personal data concerning them without undue delay and the controller shall have the obligation to erase personal data without undue delay where one of the following grounds applies...",
    "category": "data_subject_rights",
    "priority": "high",
    "implementation_guidance": [...],
    "exceptions": [
      {
        "id": "art_17_3_a",
        "description": "Exercising freedom of expression and information"
      },
      {
        "id": "art_17_3_b",
        "description": "Compliance with legal obligation"
      }
    ],
    "enforcement_cases": [
      {
        "authority": "CNIL (France)",
        "date": "2022-06-15",
        "summary": "€50,000 fine for inadequate deletion procedures"
      }
    ],
    "templates": [
      {
        "id": "gdpr-deletion-handler",
        "language": "python",
        "description": "Complete deletion handler implementation"
      }
    ]
  }
}
```

## Search Regulations

```bash
GET /api/v1/regulations/search
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |
| `type` | string | Search type: `all`, `regulations`, `requirements` |

### Example Request

```bash
curl -X GET "https://api.complianceagent.io/v1/regulations/search?q=data%20deletion&type=requirements" \
  -H "Authorization: Bearer $TOKEN"
```

### Response

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "type": "requirement",
        "regulation_id": "gdpr",
        "requirement_id": "gdpr_art_17",
        "title": "Right to erasure ('right to be forgotten')",
        "highlight": "...the <em>deletion</em> of personal <em>data</em>...",
        "score": 0.95
      },
      {
        "type": "requirement",
        "regulation_id": "ccpa",
        "requirement_id": "ccpa_1798_105",
        "title": "Consumer's right to deletion",
        "highlight": "...the right to request <em>deletion</em> of the consumer's personal information...",
        "score": 0.89
      }
    ],
    "total": 15
  }
}
```

## Enable Regulation

```bash
POST /api/v1/regulations/{regulation_id}/enable
```

### Request Body

```json
{
  "jurisdictions": ["EU", "DE", "FR"],
  "categories": ["data_subject_rights", "security", "breach_notification"],
  "notification_settings": {
    "email": true,
    "slack": true,
    "updates_frequency": "weekly"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "regulation_id": "gdpr",
    "enabled": true,
    "enabled_at": "2024-01-15T10:30:00Z",
    "configuration": {
      "jurisdictions": ["EU", "DE", "FR"],
      "categories": ["data_subject_rights", "security", "breach_notification"]
    }
  }
}
```

## Disable Regulation

```bash
POST /api/v1/regulations/{regulation_id}/disable
```

## Get Regulation Updates

```bash
GET /api/v1/regulations/{regulation_id}/updates
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | datetime | Updates since this date |
| `type` | string | Update type: `amendment`, `guidance`, `enforcement` |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "update_123",
      "regulation_id": "gdpr",
      "type": "guidance",
      "source": "EDPB",
      "title": "Guidelines 05/2021 on the Interplay between Art. 3 and Chapter V",
      "summary": "New guidance on international data transfers",
      "published_at": "2024-01-10T00:00:00Z",
      "effective_at": null,
      "impact": "medium",
      "affected_requirements": ["gdpr_art_44", "gdpr_art_45", "gdpr_art_46"],
      "url": "https://edpb.europa.eu/..."
    }
  ]
}
```

## Get Code Templates

```bash
GET /api/v1/regulations/{regulation_id}/templates
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `language` | string | Programming language filter |
| `requirement_id` | string | Filter by requirement |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "gdpr-consent-banner",
      "name": "GDPR Consent Banner",
      "description": "Cookie consent UI with granular purpose selection",
      "language": "typescript",
      "framework": "react",
      "requirements": ["gdpr_art_7", "gdpr_recital_32"],
      "preview_url": "https://templates.complianceagent.io/gdpr-consent-banner"
    },
    {
      "id": "gdpr-deletion-handler",
      "name": "GDPR Deletion Handler",
      "description": "Complete user data deletion implementation",
      "language": "python",
      "framework": "fastapi",
      "requirements": ["gdpr_art_17"]
    }
  ]
}
```

## Apply Template

```bash
POST /api/v1/regulations/{regulation_id}/templates/{template_id}/apply
```

### Request Body

```json
{
  "repository_id": "repo_123",
  "target_path": "src/compliance/",
  "config": {
    "purposes": ["analytics", "marketing", "functional"],
    "default_language": "en"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "pending",
    "files_to_create": [
      "src/compliance/consent_banner.tsx",
      "src/compliance/consent_types.ts",
      "src/compliance/consent_context.tsx"
    ]
  }
}
```

---

See also: [Compliance API](./compliance) | [Repositories API](./repositories)
