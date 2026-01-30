# CCPA/CPRA Compliance Guide

This guide covers how ComplianceAgent helps you achieve compliance with the California Consumer Privacy Act (CCPA) and California Privacy Rights Act (CPRA).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | California Consumer Privacy Act / California Privacy Rights Act |
| **Jurisdiction** | California, USA |
| **Effective Date** | CCPA: Jan 1, 2020 / CPRA: Jan 1, 2023 |
| **Enforcing Authority** | California Privacy Protection Agency (CPPA) |
| **Max Penalty** | $7,500 per intentional violation |

### Applicability

CCPA applies to businesses that:
- Have gross annual revenue > $25 million, OR
- Buy/sell personal information of 100,000+ consumers, OR
- Derive 50%+ of revenue from selling personal information

## Key Requirements

### Consumer Rights

| Right | Description | Implementation |
|-------|-------------|----------------|
| **Right to Know** | What data is collected and how it's used | Privacy policy, data inventory |
| **Right to Delete** | Request deletion of personal data | Delete endpoint |
| **Right to Opt-Out** | Opt out of sale/sharing of data | "Do Not Sell" link |
| **Right to Correct** | Correct inaccurate data (CPRA) | Edit functionality |
| **Right to Limit** | Limit use of sensitive data (CPRA) | Data use controls |
| **Non-Discrimination** | No penalty for exercising rights | Equal service access |

### Categories of Personal Information

```python
class CCPADataCategory(Enum):
    """CCPA-defined categories of personal information."""
    IDENTIFIERS = "identifiers"  # Name, email, IP, SSN
    CUSTOMER_RECORDS = "customer_records"  # Account info
    PROTECTED_CHARACTERISTICS = "protected_characteristics"  # Age, race
    COMMERCIAL_INFO = "commercial_info"  # Purchase history
    BIOMETRIC = "biometric"  # Fingerprints, face data
    INTERNET_ACTIVITY = "internet_activity"  # Browsing, search
    GEOLOCATION = "geolocation"  # Location data
    SENSORY_DATA = "sensory_data"  # Audio, video
    PROFESSIONAL_INFO = "professional_info"  # Employment
    EDUCATION_INFO = "education_info"  # Education records
    INFERENCES = "inferences"  # Profiles, predictions
    SENSITIVE_PI = "sensitive_pi"  # SSN, financial, health (CPRA)
```

## ComplianceAgent Detection

### Automatically Detected Issues

```
CCPA-001: Missing "Do Not Sell My Personal Information" link
CCPA-002: No consumer data access request mechanism
CCPA-003: Data sold to third parties without opt-out
CCPA-004: Missing privacy policy disclosures
CCPA-005: Inadequate data deletion mechanism
CCPA-006: No data inventory/categorization
CCPA-007: Missing verification for consumer requests
CCPA-008: Discriminatory treatment of opt-out users
CCPA-009: Sensitive personal information handling (CPRA)
CCPA-010: Missing data retention schedule
```

### Example Detection

**Issue: CCPA-001 - Missing opt-out mechanism**

```javascript
// ❌ Non-compliant: No opt-out for data selling
function trackUser(userId, eventData) {
  // Sending data to third-party analytics without opt-out check
  thirdPartyAnalytics.track(userId, eventData);
  adNetwork.sendConversion(userId, eventData);
}
```

**ComplianceAgent Fix:**

```javascript
// ✅ Compliant: Check opt-out before sharing data
async function trackUser(userId, eventData) {
  const userPreferences = await getUserPrivacyPreferences(userId);
  
  // CCPA: Check "Do Not Sell" preference
  if (userPreferences.doNotSell) {
    // Only first-party tracking allowed
    internalAnalytics.track(userId, eventData);
    return;
  }
  
  // User has not opted out - proceed with third-party sharing
  thirdPartyAnalytics.track(userId, eventData);
  adNetwork.sendConversion(userId, eventData);
  
  // Log for audit trail
  await auditLog.record({
    action: 'data_shared',
    userId,
    recipients: ['thirdPartyAnalytics', 'adNetwork'],
    categories: ['internet_activity'],
    optOutStatus: false
  });
}
```

## Implementation Patterns

### "Do Not Sell" Implementation

```typescript
// Privacy preferences schema
interface PrivacyPreferences {
  userId: string;
  doNotSell: boolean;
  doNotShare: boolean;  // CPRA addition
  limitSensitiveData: boolean;  // CPRA
  updatedAt: Date;
}

// API endpoint for opt-out
app.post('/api/privacy/do-not-sell', async (req, res) => {
  const { userId } = req.user;
  
  await db.privacyPreferences.upsert({
    userId,
    doNotSell: true,
    doNotShare: true,  // CPRA: Also opt out of sharing
    updatedAt: new Date()
  });
  
  // Propagate to third parties
  await notifyThirdParties(userId, { doNotSell: true });
  
  // Audit log
  await auditLog.record({
    action: 'opt_out_sale',
    userId,
    timestamp: new Date()
  });
  
  res.json({ status: 'opted_out' });
});

// Footer component with required link
function Footer() {
  return (
    <footer>
      {/* CCPA required link */}
      <a href="/privacy/do-not-sell">
        Do Not Sell or Share My Personal Information
      </a>
      <a href="/privacy">Privacy Policy</a>
    </footer>
  );
}
```

### Consumer Data Request Handler

```python
from datetime import datetime, timedelta

class ConsumerDataRequest(BaseModel):
    """CCPA consumer data request."""
    request_type: Literal["access", "delete", "correct", "opt-out"]
    consumer_email: str
    verification_method: str
    submitted_at: datetime
    deadline: datetime  # 45 days from submission

@app.post("/api/privacy/request")
async def submit_privacy_request(
    request: ConsumerDataRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle CCPA consumer requests.
    Must respond within 45 days (extendable to 90).
    """
    # Verify consumer identity
    verification = await verify_consumer(
        email=request.consumer_email,
        method=request.verification_method
    )
    
    if not verification.verified:
        return {"status": "verification_required", "methods": ["email", "sms"]}
    
    # Create request record
    record = PrivacyRequest(
        type=request.request_type,
        consumer_id=verification.consumer_id,
        submitted_at=datetime.utcnow(),
        deadline=datetime.utcnow() + timedelta(days=45),
        status="pending"
    )
    db.add(record)
    await db.commit()
    
    # Queue for processing
    await queue.enqueue(
        "process_privacy_request",
        request_id=record.id,
        deadline=record.deadline
    )
    
    return {
        "status": "received",
        "request_id": record.id,
        "expected_completion": record.deadline.isoformat()
    }
```

### Data Inventory

```python
# Track what data is collected and why
DATA_INVENTORY = {
    "identifiers": {
        "fields": ["email", "name", "ip_address", "device_id"],
        "purposes": ["account_management", "security"],
        "retention": "account_lifetime",
        "shared_with": [],
        "sold": False
    },
    "internet_activity": {
        "fields": ["page_views", "clicks", "search_queries"],
        "purposes": ["analytics", "personalization", "advertising"],
        "retention": "12_months",
        "shared_with": ["analytics_provider"],
        "sold": True  # Requires opt-out
    },
    "geolocation": {
        "fields": ["ip_geolocation", "gps_coordinates"],
        "purposes": ["service_delivery", "advertising"],
        "retention": "30_days",
        "shared_with": ["ad_network"],
        "sold": True
    }
}

def get_privacy_disclosure():
    """Generate CCPA-compliant privacy disclosure."""
    categories_collected = list(DATA_INVENTORY.keys())
    categories_sold = [k for k, v in DATA_INVENTORY.items() if v["sold"]]
    
    return {
        "categories_collected": categories_collected,
        "categories_sold": categories_sold,
        "purposes": get_all_purposes(),
        "retention_periods": get_retention_summary(),
        "third_parties": get_third_party_list()
    }
```

### Privacy Policy Requirements

```markdown
## Privacy Policy (CCPA Required Sections)

### Categories of Personal Information Collected
- Identifiers (name, email, IP address)
- Internet activity (browsing history, search queries)
- Geolocation data
- Commercial information (purchase history)

### Business Purposes for Collection
- Providing our services
- Processing transactions
- Security and fraud prevention
- Analytics and improvement

### Categories of Personal Information Sold or Shared
- Internet activity (shared with advertising partners)
- Identifiers (shared with analytics providers)

### Your California Privacy Rights
- **Right to Know**: Request what data we collect
- **Right to Delete**: Request deletion of your data
- **Right to Opt-Out**: Opt out of sale/sharing of your data
- **Right to Non-Discrimination**: We won't treat you differently

### How to Exercise Your Rights
- Online: [Privacy Request Form](/privacy/request)
- Email: privacy@example.com
- Phone: 1-800-XXX-XXXX

### Do Not Sell or Share My Personal Information
[Click here to opt out](/privacy/do-not-sell)
```

## Sensitive Personal Information (CPRA)

CPRA adds protections for sensitive data:

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

@app.post("/api/privacy/limit-sensitive")
async def limit_sensitive_data(user_id: str):
    """
    CPRA: Allow consumers to limit use of sensitive data.
    """
    await db.privacy_preferences.update(
        user_id,
        {"limitSensitiveData": True}
    )
    
    # Restrict processing
    await restrict_sensitive_processing(user_id)
    
    return {"status": "limited"}
```

## Configuration

```bash
# .env
COMPLIANCE_FRAMEWORKS=ccpa
CCPA_THRESHOLD_CONSUMERS=100000
CCPA_THRESHOLD_REVENUE=25000000
CCPA_REQUEST_DEADLINE_DAYS=45
CPRA_ENABLED=true
```

## CI/CD Integration

```yaml
- name: CCPA Compliance Check
  uses: complianceagent/compliance-action@v1
  with:
    frameworks: ccpa
    fail-on: major
    ccpa-check-opt-out: true
    ccpa-check-privacy-policy: true
```

## Resources

- [CCPA Text](https://oag.ca.gov/privacy/ccpa)
- [CPRA Text](https://cppa.ca.gov/regulations/)
- [CPPA Enforcement](https://cppa.ca.gov/enforcement/)

## Related Frameworks

- [GDPR](gdpr.md) - Similar but broader scope
- [Virginia VCDPA](vcdpa.md) - Virginia privacy law
- [Colorado CPA](colorado-cpa.md) - Colorado privacy law
