# GDPR Compliance Guide

This guide covers how ComplianceAgent helps you achieve and maintain compliance with the General Data Protection Regulation (GDPR).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | General Data Protection Regulation |
| **Jurisdiction** | European Union |
| **Effective Date** | May 25, 2018 |
| **Enforcing Authority** | National Data Protection Authorities |
| **Max Penalty** | €20M or 4% of annual global revenue |

## Key Requirements

### Data Processing Principles (Article 5)

| Principle | Description | Code Impact |
|-----------|-------------|-------------|
| **Lawfulness** | Process data with legal basis | Consent collection, contract verification |
| **Purpose Limitation** | Use data only for stated purposes | Data access controls, logging |
| **Data Minimization** | Collect only necessary data | Field validation, schema design |
| **Accuracy** | Keep data accurate and current | Update mechanisms, validation |
| **Storage Limitation** | Don't keep data longer than needed | Retention policies, auto-deletion |
| **Integrity & Confidentiality** | Protect data security | Encryption, access controls |

### Data Subject Rights (Articles 12-23)

| Right | Description | Implementation Required |
|-------|-------------|------------------------|
| **Access** (Art. 15) | Users can request their data | Data export endpoint |
| **Rectification** (Art. 16) | Users can correct data | Edit functionality |
| **Erasure** (Art. 17) | "Right to be forgotten" | Delete endpoint, cascade deletion |
| **Portability** (Art. 20) | Export data in machine-readable format | JSON/CSV export |
| **Objection** (Art. 21) | Opt-out of processing | Preference management |
| **Automated Decisions** (Art. 22) | Right to human review of AI decisions | Human-in-the-loop, explainability |

## ComplianceAgent Detection

### Automatically Detected Issues

```
GDPR-001: Missing consent collection mechanism
GDPR-002: Personal data stored without encryption
GDPR-003: No data retention policy implemented
GDPR-004: Missing data subject access request handler
GDPR-005: Inadequate data deletion (soft delete only)
GDPR-006: Cross-border data transfer without safeguards
GDPR-007: Missing privacy policy disclosure
GDPR-008: Insufficient logging for data processing
GDPR-009: Third-party data sharing without consent
GDPR-010: Missing data breach notification mechanism
```

### Example Detection

**Issue: GDPR-001 - Missing consent collection**

```python
# ❌ Non-compliant: Collecting data without consent
@app.post("/api/users")
async def create_user(user: UserCreate):
    # Directly storing user data without consent
    return await db.users.create(user.dict())
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Consent verification before data collection
@app.post("/api/users")
async def create_user(user: UserCreate, consent: ConsentRecord):
    # GDPR Art. 7: Verify explicit consent before processing
    if not consent.is_valid or not consent.purposes.includes("account_creation"):
        raise HTTPException(
            status_code=400,
            detail="Valid consent required for account creation"
        )
    
    # Log consent for audit trail (GDPR Art. 7(1))
    await audit_log.record(
        action="user_created",
        consent_id=consent.id,
        purposes=consent.purposes
    )
    
    return await db.users.create(user.dict())
```

## Implementation Patterns

### Consent Management

```python
from datetime import datetime, timedelta
from enum import Enum

class ConsentPurpose(Enum):
    ACCOUNT = "account_management"
    MARKETING = "marketing_communications"
    ANALYTICS = "usage_analytics"
    THIRD_PARTY = "third_party_sharing"

class ConsentRecord(BaseModel):
    user_id: UUID
    purposes: list[ConsentPurpose]
    granted_at: datetime
    expires_at: datetime | None
    ip_address: str
    user_agent: str
    version: str  # Consent form version
    
    def is_valid_for(self, purpose: ConsentPurpose) -> bool:
        """Check if consent is valid for a specific purpose."""
        if purpose not in self.purposes:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

# Consent collection endpoint
@app.post("/api/consent")
async def record_consent(
    consent: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Record user consent with full audit trail."""
    record = ConsentRecord(
        user_id=consent.user_id,
        purposes=consent.purposes,
        granted_at=datetime.utcnow(),
        expires_at=consent.expires_at,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        version="1.0"
    )
    await db.add(record)
    await db.commit()
    return {"status": "recorded", "consent_id": record.id}
```

### Data Subject Access Request (DSAR)

```python
@app.get("/api/users/{user_id}/data-export")
async def export_user_data(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GDPR Article 15 & 20: Data access and portability.
    Export all user data in machine-readable format.
    """
    # Verify user identity
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Can only export your own data")
    
    # Collect all user data
    user_data = {
        "profile": await get_user_profile(db, user_id),
        "activity": await get_user_activity(db, user_id),
        "preferences": await get_user_preferences(db, user_id),
        "consent_records": await get_consent_history(db, user_id),
        "data_processing_log": await get_processing_log(db, user_id),
    }
    
    # Log the access request
    await audit_log.record(
        action="data_export",
        user_id=user_id,
        requested_by=current_user.id
    )
    
    return JSONResponse(
        content=user_data,
        headers={
            "Content-Disposition": f"attachment; filename=user_data_{user_id}.json"
        }
    )
```

### Right to Erasure (Delete)

```python
@app.delete("/api/users/{user_id}")
async def delete_user_data(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    GDPR Article 17: Right to erasure ("right to be forgotten").
    Permanently delete all user data.
    """
    # Verify authorization
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Unauthorized")
    
    # Check for legal holds or retention requirements
    if await has_legal_hold(db, user_id):
        raise HTTPException(
            400, 
            "Data under legal hold cannot be deleted"
        )
    
    # Delete from all tables (cascade)
    async with db.begin():
        await db.execute(delete(UserActivity).where(UserActivity.user_id == user_id))
        await db.execute(delete(UserPreferences).where(UserPreferences.user_id == user_id))
        await db.execute(delete(ConsentRecord).where(ConsentRecord.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
    
    # Delete from search indices
    await elasticsearch.delete_by_query(
        index="users",
        query={"term": {"user_id": str(user_id)}}
    )
    
    # Delete from backups (async job)
    await queue.enqueue("delete_from_backups", user_id=user_id)
    
    # Audit log (anonymized)
    await audit_log.record(
        action="user_deleted",
        user_id="[DELETED]",
        deletion_requested_by=current_user.id
    )
    
    return {"status": "deleted"}
```

### Data Encryption

```python
from cryptography.fernet import Fernet

class EncryptedField:
    """SQLAlchemy type for encrypted personal data."""
    
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.fernet.encrypt(value.encode()).decode()
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return self.fernet.decrypt(value.encode()).decode()
        return value

# Usage in model
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True)
    email = Column(EncryptedString)  # Encrypted at rest
    name = Column(EncryptedString)
    # ...
```

## Configuration

### Enable GDPR Framework

```bash
# .env
COMPLIANCE_FRAMEWORKS=gdpr,ccpa
GDPR_STRICT_MODE=true
GDPR_DATA_RETENTION_DAYS=730  # 2 years default
```

### CI/CD Integration

```yaml
# .github/workflows/compliance.yml
- name: GDPR Compliance Check
  uses: complianceagent/compliance-action@v1
  with:
    frameworks: gdpr
    fail-on: major
    gdpr-strict: true
```

## Audit Trail

ComplianceAgent maintains audit logs for GDPR compliance:

```json
{
  "event_type": "data_processing",
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "uuid",
  "action": "profile_update",
  "legal_basis": "consent",
  "consent_id": "uuid",
  "data_categories": ["name", "email"],
  "processor": "user_service",
  "ip_address": "192.168.1.1",
  "retention_until": "2026-01-15T10:30:00Z"
}
```

## Resources

- [GDPR Full Text](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [ICO GDPR Guide](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)
- [EDPB Guidelines](https://edpb.europa.eu/our-work-tools/general-guidance/gdpr-guidelines-recommendations-best-practices_en)

## Related Frameworks

- [CCPA](ccpa.md) - California privacy law with similar requirements
- [HIPAA](hipaa.md) - US health data protection
