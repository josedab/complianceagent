---
sidebar_position: 6
title: Multi-Jurisdiction
description: How ComplianceAgent handles conflicting requirements across regions
---

# Multi-Jurisdiction Compliance

Real-world applications serve users globally, often facing conflicting regulatory requirements. ComplianceAgent helps you navigate this complexity.

## The Challenge

Consider a global SaaS application:

```
┌─────────────────────────────────────────────────────────────────┐
│                  Multi-Jurisdiction Challenge                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Your Application serves users in:                               │
│                                                                  │
│  🇪🇺 EU (GDPR)          🇺🇸 California (CCPA)    🇸🇬 Singapore   │
│  - 72hr breach notify   - 45-day data access   - PDPA rules     │
│  - Explicit consent     - Opt-out model        - Consent or     │
│  - DPO required         - No DPO required        legitimate      │
│                                                    interest      │
│                                                                  │
│  Conflicts:                                                      │
│  • Consent model: Opt-in (EU) vs Opt-out (US)                   │
│  • Breach timing: 72 hours (EU) vs "expeditiously" (CCPA)       │
│  • Data access: 30 days (EU) vs 45 days (CCPA)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## How ComplianceAgent Helps

### Conflict Detection

ComplianceAgent automatically identifies conflicting requirements:

```json
{
  "conflict_id": "consent-model-2024",
  "requirements": [
    {
      "framework": "GDPR",
      "article": "Art. 7",
      "requirement": "Explicit opt-in consent required",
      "jurisdiction": "EU"
    },
    {
      "framework": "CCPA",
      "article": "§1798.120",
      "requirement": "Right to opt-out of sale",
      "jurisdiction": "US-CA"
    }
  ],
  "conflict_type": "consent_model",
  "description": "EU requires opt-in, California allows opt-out with sale restrictions",
  "resolution_options": ["strictest", "jurisdiction_based", "custom"]
}
```

### Resolution Strategies

#### 1. Strictest Wins

Apply the most restrictive requirement globally:

```yaml
# Configuration
resolution_strategy: strictest

# Result for consent conflict:
# → Apply GDPR opt-in globally
# → Exceed CCPA requirements (compliant)
```

**Pros:**
- Simple to implement
- Always compliant everywhere
- Single code path

**Cons:**
- May over-comply in some regions
- Could impact user experience
- Higher implementation effort

#### 2. Jurisdiction-Based

Apply requirements based on user location:

```yaml
# Configuration
resolution_strategy: jurisdiction_based
user_location_source: ip_geolocation

# Result:
# → EU users: GDPR opt-in consent
# → California users: CCPA opt-out with notices
# → Singapore users: PDPA consent flow
```

**Pros:**
- Optimal compliance per region
- Better user experience
- Appropriate effort per market

**Cons:**
- More complex implementation
- Need accurate location detection
- Multiple code paths to maintain

#### 3. Custom Rules

Define specific rules for conflicts:

```yaml
# Configuration
resolution_strategy: custom
rules:
  - conflict: consent_model
    resolution: 
      default: gdpr_opt_in
      exceptions:
        - jurisdiction: US-CA
          apply: ccpa_with_opt_out
          condition: user_is_california_resident
          
  - conflict: breach_notification
    resolution:
      default: strictest  # 72 hours
      
  - conflict: data_retention
    resolution:
      jurisdiction_based: true
      fallback: shortest_period
```

## Jurisdiction Hierarchy

ComplianceAgent understands jurisdictional relationships:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Jurisdiction Hierarchy                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Federal/International                                           │
│  ├── GDPR (EU-wide)                                             │
│  │   ├── German BDSG (national)                                 │
│  │   │   └── State-specific (Landesdatenschutzgesetze)         │
│  │   ├── French CNIL guidance                                   │
│  │   └── Dutch UAVG                                             │
│  │                                                              │
│  ├── US Federal (FTC Act, HIPAA)                                │
│  │   ├── State: California (CCPA/CPRA)                          │
│  │   ├── State: Virginia (VCDPA)                                │
│  │   ├── State: Colorado (CPA)                                  │
│  │   └── Sector: Healthcare (HIPAA)                             │
│  │                                                              │
│  └── APAC                                                       │
│      ├── Singapore PDPA                                         │
│      ├── Japan APPI                                             │
│      └── Australia Privacy Act                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Hierarchy Rules

1. **Stricter always applies** - If a sub-jurisdiction is stricter, it prevails
2. **Sector rules stack** - HIPAA + state law both apply to healthcare
3. **Latest version wins** - Most recent regulation version applies

## Implementation Patterns

### Location-Based Compliance

```python
# Generated by ComplianceAgent for jurisdiction-based compliance

from compliance import get_user_jurisdiction, get_requirements

class ComplianceMiddleware:
    """Apply jurisdiction-specific compliance rules."""
    
    async def __call__(self, request: Request, call_next):
        # Determine user jurisdiction
        jurisdiction = await get_user_jurisdiction(
            ip=request.client.host,
            user_id=request.user.id if request.user else None,
            explicit_location=request.headers.get("X-User-Jurisdiction")
        )
        
        # Get applicable requirements
        requirements = get_requirements(jurisdiction)
        
        # Attach to request context
        request.state.jurisdiction = jurisdiction
        request.state.compliance = requirements
        
        return await call_next(request)
```

### Consent Management

```python
# Multi-jurisdiction consent handling

class ConsentManager:
    """Handle consent across jurisdictions."""
    
    CONSENT_MODELS = {
        "EU": "opt_in",      # GDPR
        "US-CA": "opt_out",  # CCPA
        "BR": "opt_in",      # LGPD
        "DEFAULT": "opt_in"  # Safe default
    }
    
    def get_consent_model(self, jurisdiction: str) -> str:
        return self.CONSENT_MODELS.get(
            jurisdiction, 
            self.CONSENT_MODELS["DEFAULT"]
        )
    
    def collect_consent(self, user: User, purposes: list[str]) -> ConsentRecord:
        model = self.get_consent_model(user.jurisdiction)
        
        if model == "opt_in":
            # Must have explicit consent for each purpose
            return self._collect_explicit_consent(user, purposes)
        else:
            # Opt-out model: provide notice and opt-out mechanism
            return self._provide_opt_out_notice(user, purposes)
    
    def check_consent(self, user: User, purpose: str) -> bool:
        model = self.get_consent_model(user.jurisdiction)
        consent = self._get_consent_record(user, purpose)
        
        if model == "opt_in":
            return consent and consent.granted
        else:
            return consent is None or not consent.opted_out
```

### Data Subject Requests

```python
# Handle varying response timeframes

class DataSubjectRequest:
    """Process data subject requests per jurisdiction."""
    
    RESPONSE_DEADLINES = {
        "EU": timedelta(days=30),       # GDPR
        "US-CA": timedelta(days=45),    # CCPA
        "US-VA": timedelta(days=45),    # VCDPA
        "UK": timedelta(days=30),       # UK GDPR
        "BR": timedelta(days=15),       # LGPD
    }
    
    def calculate_deadline(self, jurisdiction: str) -> datetime:
        deadline = self.RESPONSE_DEADLINES.get(
            jurisdiction,
            timedelta(days=30)  # Safe default
        )
        return datetime.now() + deadline
    
    def process_access_request(self, request: AccessRequest) -> None:
        deadline = self.calculate_deadline(request.jurisdiction)
        
        # Create task with jurisdiction-appropriate deadline
        task = DataAccessTask(
            request_id=request.id,
            deadline=deadline,
            jurisdiction=request.jurisdiction,
            requirements=self._get_jurisdiction_requirements(request.jurisdiction)
        )
        
        queue.enqueue(task)
```

## Conflict Visualization

### Dashboard View

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jurisdiction Conflicts                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Active Conflicts: 3                    Resolution: Strictest    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Consent Model                                    HIGH    │    │
│  │ GDPR (opt-in) ←→ CCPA (opt-out)                         │    │
│  │ Resolution: Apply GDPR opt-in globally                   │    │
│  │ Status: ✅ Implemented                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Breach Notification                              MEDIUM  │    │
│  │ GDPR (72h) ←→ CCPA (expedient)                          │    │
│  │ Resolution: Apply 72 hour deadline everywhere            │    │
│  │ Status: ✅ Implemented                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Data Retention                                   LOW     │    │
│  │ Varies by jurisdiction and purpose                       │    │
│  │ Resolution: Jurisdiction-based with shortest default     │    │
│  │ Status: ⚠️ Needs implementation                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Compliance Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    Compliance Matrix                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Requirement          │ GDPR │ CCPA │ PDPA │ Your Implementation │
│  ─────────────────────┼──────┼──────┼──────┼────────────────────│
│  Explicit consent     │  ✓   │  -   │  ~   │  ✅ Global opt-in  │
│  Right to access      │  ✓   │  ✓   │  ✓   │  ✅ 30-day SLA     │
│  Right to delete      │  ✓   │  ✓   │  ✓   │  ✅ Implemented    │
│  Data portability     │  ✓   │  -   │  -   │  ✅ JSON export    │
│  Breach notification  │ 72h  │ exp  │ 3d   │  ✅ 72h global     │
│  DPO required         │  ✓   │  -   │  -   │  ✅ Appointed      │
│  Cross-border rules   │ SCCs │  -   │ CBPR │  ✅ SCCs in place  │
│                                                                  │
│  Legend: ✓ Required  - Not required  ~ Conditional               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration

### Organization Settings

```yaml
# .complianceagent/jurisdiction.yml
organization: acme-corp

# Operating jurisdictions
jurisdictions:
  primary: US
  additional:
    - EU
    - UK
    - SG
    - AU

# Resolution strategy
conflict_resolution:
  default_strategy: strictest
  
  # Override for specific conflicts
  overrides:
    - conflict_type: consent_model
      strategy: jurisdiction_based
      
    - conflict_type: data_retention
      strategy: custom
      rules:
        - jurisdiction: EU
          retention: 3_years
        - jurisdiction: US
          retention: 7_years

# User jurisdiction detection
jurisdiction_detection:
  methods:
    - ip_geolocation
    - user_profile
    - explicit_selection
  fallback: strictest_applicable
```

### Per-Repository Configuration

```yaml
# Repository-specific overrides
repository: acme/customer-portal

jurisdictions:
  # This repository only serves EU and UK
  scope:
    - EU
    - UK
    
  # Always apply strictest (GDPR)
  resolution: strictest
```

## Reporting

### Compliance by Jurisdiction

Generate reports showing compliance status per region:

```bash
curl -X GET "http://localhost:8000/api/v1/reports/jurisdiction-compliance" \
  -H "Authorization: Bearer $TOKEN"
```

Response:

```json
{
  "report_date": "2024-01-15",
  "organization": "acme-corp",
  "jurisdictions": {
    "EU": {
      "frameworks": ["GDPR"],
      "compliance_score": 94,
      "gaps": 2,
      "critical_gaps": 0
    },
    "US-CA": {
      "frameworks": ["CCPA"],
      "compliance_score": 91,
      "gaps": 3,
      "critical_gaps": 1
    },
    "SG": {
      "frameworks": ["PDPA"],
      "compliance_score": 88,
      "gaps": 4,
      "critical_gaps": 0
    }
  },
  "conflicts_resolved": 3,
  "conflicts_pending": 0
}
```

---

Now you understand the core concepts. Continue to [Guides](../guides/connecting-repositories) for step-by-step tutorials.
