---
sidebar_position: 3
title: CCPA
description: California Consumer Privacy Act compliance with ComplianceAgent
---

# CCPA/CPRA Compliance

The California Consumer Privacy Act (CCPA), as amended by the California Privacy Rights Act (CPRA), provides California residents with privacy rights.

## Overview

| Attribute | Value |
|-----------|-------|
| **Jurisdiction** | California, USA |
| **Effective Date** | CCPA: Jan 1, 2020 / CPRA: Jan 1, 2023 |
| **Applies To** | Businesses meeting revenue/data thresholds |
| **Maximum Penalty** | $7,500 per intentional violation |
| **Requirements Tracked** | 68 |

## Who Must Comply

CCPA applies if you:

- Have >$25M annual gross revenue, OR
- Buy/sell data of 100,000+ consumers/households, OR
- Derive 50%+ revenue from selling personal information

## Key Requirements

### Consumer Rights

| Right | Description | Response Time |
|-------|-------------|---------------|
| Know | What data is collected and how it's used | 45 days |
| Delete | Request deletion of personal information | 45 days |
| Opt-Out | Opt out of sale/sharing of data | Immediate |
| Correct | Correct inaccurate personal information | 45 days |
| Limit | Limit use of sensitive personal information | Immediate |
| Non-Discrimination | Equal service regardless of privacy choices | - |

### Right to Know Implementation

```python
# CCPA Right to Know handler
async def handle_know_request(consumer_id: str) -> KnowResponse:
    """Handle CCPA Right to Know request."""
    
    # Verify consumer identity
    await verify_identity(consumer_id)
    
    # Collect all personal information
    data = await collect_consumer_data(consumer_id)
    
    return KnowResponse(
        categories_collected=[
            "identifiers",
            "commercial_information",
            "internet_activity",
            "geolocation"
        ],
        specific_pieces=data,
        sources=["direct_collection", "service_providers"],
        purposes=["provide_services", "analytics", "marketing"],
        third_parties_shared=["analytics_provider", "ad_network"],
        sold_or_shared=True
    )
```

### Do Not Sell/Share

```typescript
// "Do Not Sell My Personal Information" implementation
interface OptOutPreference {
  consumerId: string;
  optedOut: boolean;
  timestamp: Date;
  scope: 'all' | 'advertising' | 'analytics';
}

async function handleOptOut(consumerId: string): Promise<void> {
  // Record opt-out preference
  await saveOptOutPreference({
    consumerId,
    optedOut: true,
    timestamp: new Date(),
    scope: 'all'
  });
  
  // Notify all downstream systems
  await notifyOptOutToVendors(consumerId);
  
  // Stop current data sharing
  await stopDataSharing(consumerId);
  
  // Add to Global Privacy Control responders
  await updateGPCResponse(consumerId, true);
}
```

### Sensitive Personal Information

CPRA introduced restrictions on sensitive data:

```python
SENSITIVE_CATEGORIES = [
    "social_security_number",
    "drivers_license",
    "passport",
    "financial_account",
    "precise_geolocation",
    "racial_ethnic_origin",
    "religious_beliefs",
    "union_membership",
    "genetic_data",
    "biometric_data",
    "health_data",
    "sex_life_orientation"
]

async def process_sensitive_data(
    consumer_id: str,
    data_category: str,
    purpose: str
) -> None:
    """Process sensitive data with CPRA restrictions."""
    
    if data_category in SENSITIVE_CATEGORIES:
        # Check for limit preference
        limit = await get_limit_preference(consumer_id)
        
        if limit.limited:
            allowed_purposes = [
                "provide_requested_service",
                "security",
                "fraud_prevention",
                "safety"
            ]
            if purpose not in allowed_purposes:
                raise SensitiveDataLimitedError(
                    f"Consumer limited use of {data_category}"
                )
```

### Privacy Notice Requirements

```yaml
# Required privacy notice disclosures
privacy_notice:
  required_disclosures:
    - categories_collected
    - purposes_of_collection
    - categories_sold_or_shared
    - categories_disclosed_to_service_providers
    - retention_periods
    - consumer_rights
    - opt_out_link
    - financial_incentive_terms
  
  update_frequency: "at_collection_and_annually"
  
  links_required:
    - "Do Not Sell or Share My Personal Information"
    - "Limit the Use of My Sensitive Personal Information"
```

## Common Gaps

### 1. Missing Opt-Out Link

**Issue:** No "Do Not Sell or Share" link on homepage.

**Solution:**

```html
<!-- Required homepage link -->
<footer>
  <a href="/privacy/do-not-sell">
    Do Not Sell or Share My Personal Information
  </a>
</footer>
```

### 2. Ignoring Global Privacy Control

**Issue:** Not honoring GPC browser signals.

**Solution:**

```javascript
// Detect and honor Global Privacy Control
function checkGlobalPrivacyControl(): boolean {
  return navigator.globalPrivacyControl === true;
}

async function handlePageLoad(): Promise<void> {
  if (checkGlobalPrivacyControl()) {
    // Treat as opt-out request
    await setOptOutPreference(getCurrentUser(), true);
    disableTrackingScripts();
  }
}
```

### 3. Incomplete Deletion

**Issue:** Not deleting from all systems including service providers.

**Solution:**

```python
async def handle_deletion_request(consumer_id: str) -> DeletionResult:
    """CCPA-compliant deletion."""
    
    # Delete from own systems
    await delete_from_database(consumer_id)
    await delete_from_analytics(consumer_id)
    await delete_from_marketing(consumer_id)
    
    # Direct service providers to delete
    service_providers = await get_service_providers()
    for provider in service_providers:
        await provider.delete_consumer_data(consumer_id)
    
    # Document deletion
    return DeletionResult(
        consumer_id=consumer_id,
        deleted_categories=["all"],
        service_providers_notified=len(service_providers)
    )
```

### 4. Inadequate Verification

**Issue:** Processing requests without verifying identity.

**Solution:**

```python
async def verify_consumer_identity(
    request: PrivacyRequest
) -> VerificationResult:
    """Verify consumer identity per CCPA requirements."""
    
    verification_methods = []
    
    # Method 1: Match to existing account
    if request.email:
        account = await find_account(request.email)
        if account and await verify_email_ownership(request.email):
            verification_methods.append("account_match")
    
    # Method 2: Match data points
    matches = await match_data_points(
        request.provided_info,
        minimum_matches=2
    )
    if matches >= 2:
        verification_methods.append("data_point_match")
    
    # Determine verification level
    if len(verification_methods) >= 2:
        return VerificationResult(level="high", verified=True)
    elif len(verification_methods) == 1:
        return VerificationResult(level="medium", verified=True)
    else:
        return VerificationResult(level="none", verified=False)
```

## Service Provider Requirements

If you're a service provider:

```python
# Service provider contract requirements
SERVICE_PROVIDER_OBLIGATIONS = {
    "contract_requirements": [
        "specific_business_purpose",
        "prohibition_on_selling",
        "prohibition_on_combining_data",
        "compliance_certification",
        "audit_rights"
    ],
    "data_handling": {
        "use_limitation": "only_for_specified_purpose",
        "notification_of_requests": "required",
        "assistance_with_requests": "required"
    }
}
```

## Configuration

```yaml
# .complianceagent/config.yml
frameworks:
  ccpa:
    enabled: true
    
    # Business type affects requirements
    business_type: "business"  # or "service_provider"
    
    # Categories of data you process
    data_categories:
      - identifiers
      - commercial_information
      - internet_activity
      - geolocation
    
    # Whether you sell/share data
    sells_data: true
    shares_for_advertising: true
    
    # Sensitive data handling
    processes_sensitive_data: false
```

## Templates

| Template | Description |
|----------|-------------|
| `ccpa-opt-out-link` | Do Not Sell/Share link component |
| `ccpa-request-handler` | Consumer request processing |
| `ccpa-verification` | Identity verification flow |
| `ccpa-gpc-handler` | Global Privacy Control support |

## Differences from GDPR

| Aspect | GDPR | CCPA |
|--------|------|------|
| Consent Model | Opt-in required | Opt-out (for selling) |
| Scope | All personal data | Consumer data only |
| Response Time | 30 days | 45 days |
| Private Right of Action | No | Yes (data breaches) |
| Sensitive Data | Special category | Separate treatment (CPRA) |

---

See also: [GDPR](./gdpr) | [HIPAA](./hipaa) | [Frameworks Overview](./overview)
