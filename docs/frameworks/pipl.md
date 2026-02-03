# PIPL Compliance Guide

This guide covers how ComplianceAgent helps you achieve and maintain compliance with China's Personal Information Protection Law (PIPL).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | 中华人民共和国个人信息保护法 (Personal Information Protection Law) |
| **Jurisdiction** | People's Republic of China |
| **Effective Date** | November 1, 2021 |
| **Enforcing Authority** | Cyberspace Administration of China (CAC), Ministry of Public Security |
| **Applies To** | All organizations processing personal information of individuals in China |
| **Max Penalty** | ¥50M or 5% of previous year's revenue |

## Extraterritorial Scope

PIPL applies to processing activities outside China when:

1. **Purpose**: Processing is for providing products/services to individuals in China
2. **Analysis**: Processing analyzes or assesses behavior of individuals in China
3. **Other**: Circumstances stipulated by laws and administrative regulations

## Key Definitions

| Term | Definition |
|------|------------|
| **Personal Information (PI)** | Information relating to identified or identifiable natural persons |
| **Sensitive PI** | Information that may cause harm to dignity or safety if leaked (biometrics, health, financial, location, minors' data) |
| **Personal Information Handler** | Entity that determines purposes and means of processing (similar to GDPR controller) |
| **Entrusted Party** | Third party processing on behalf of handler (similar to GDPR processor) |
| **Separate Consent** | Explicit consent required for specific processing activities |

## Legal Bases for Processing

| Legal Basis | Description | Requirements |
|-------------|-------------|--------------|
| **Consent** | Individual's consent | Must be informed, voluntary, explicit |
| **Contract** | Necessary for contract | Limited to contract performance |
| **Legal Obligation** | Required by law | Statutory requirement |
| **Public Health** | Emergency response | Epidemic, public health emergencies |
| **Public Interest** | News reporting, public interest | Reasonable scope |
| **Publicly Disclosed** | Already public information | Within reasonable scope |
| **Other** | Laws and regulations | As specified |

## Individual Rights

| Right | Description | Implementation Required |
|-------|-------------|------------------------|
| **Right to Know** | Know about processing activities | Privacy notice, transparency |
| **Right to Decide** | Consent and withdrawal | Consent management |
| **Right to Access** | Access their personal information | Data export functionality |
| **Right to Rectification** | Correct inaccurate information | Edit capability |
| **Right to Deletion** | Request deletion | Delete endpoint |
| **Right to Explanation** | Understand automated decisions | Explainability |
| **Right to Portability** | Transfer to other handlers | Data export |
| **Right to Refuse Automated Decisions** | Opt-out of profiling | Manual processing option |

## Key Requirements

### Consent Requirements

| Type | When Required | Implementation |
|------|---------------|----------------|
| **General Consent** | All processing | Consent collection |
| **Separate Consent** | Sensitive PI, cross-border transfers, public disclosure | Explicit consent flows |
| **Guardian Consent** | Minor's data (under 14) | Age verification, guardian consent |

### Data Localization

| Requirement | Threshold | Implementation |
|-------------|-----------|----------------|
| **Critical Infrastructure** | Must store in China | Local data centers |
| **Large Handlers** | ≥1M individuals | Local storage, security assessment |
| **Cross-border Transfer** | Requires approval | CAC assessment or certification |

### Cross-border Transfer Mechanisms

| Mechanism | Applicability |
|-----------|---------------|
| **CAC Security Assessment** | Critical infrastructure, large handlers |
| **Standard Contract** | Non-critical with CAC filing |
| **Certification** | By recognized institution |
| **International Treaty** | As specified by treaties |

## ComplianceAgent Detection

### Automatically Detected Issues

```
PIPL-001: Missing consent collection before processing
PIPL-002: No separate consent for sensitive personal information
PIPL-003: Personal information transferred outside China without authorization
PIPL-004: Missing privacy notice / transparency
PIPL-005: No mechanism for individual rights exercise
PIPL-006: Inadequate data retention controls
PIPL-007: Missing data localization for China users
PIPL-008: No personal information protection impact assessment
PIPL-009: Processing minor's data without guardian consent
PIPL-010: Automated decision-making without opt-out option
```

### Example Detection

**Issue: PIPL-001 - Missing consent collection**

```python
# ❌ Non-compliant: Processing without consent
@app.post("/api/users")
async def create_user(user: UserCreate):
    # Processing personal information without consent
    return await db.users.create(user.dict())
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Proper consent collection per PIPL
from enum import Enum
from datetime import datetime

class ConsentType(Enum):
    GENERAL = "general"           # Basic processing consent
    SENSITIVE = "sensitive"       # Sensitive PI consent
    CROSS_BORDER = "cross_border" # International transfer consent
    MARKETING = "marketing"       # Marketing communications

class ConsentRecord(Base):
    """PIPL-compliant consent records."""
    __tablename__ = "consent_records"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    consent_type = Column(Enum(ConsentType))
    granted = Column(Boolean)
    granted_at = Column(DateTime)
    withdrawn_at = Column(DateTime, nullable=True)
    
    # PIPL: Record how consent was obtained
    consent_method = Column(String)  # "checkbox", "signature", "verbal"
    privacy_notice_version = Column(String)
    ip_address = Column(String)
    
    # PIPL: Consent must be specific about purposes
    purposes = Column(ARRAY(String))
    data_categories = Column(ARRAY(String))

@app.post("/api/users")
async def create_user(user: UserCreate, consent: ConsentSubmission):
    """Create user with PIPL-compliant consent."""
    
    # PIPL Art. 14: Consent must be informed
    if not consent.privacy_notice_acknowledged:
        raise HTTPException(
            status_code=400,
            detail="Privacy notice must be acknowledged before processing"
        )
    
    # PIPL Art. 13: Verify consent for processing
    if not consent.general_consent:
        raise HTTPException(
            status_code=400,
            detail="Consent required to process personal information"
        )
    
    # PIPL Art. 29: Separate consent for sensitive PI
    if user.contains_sensitive_pi():
        if not consent.sensitive_consent:
            raise HTTPException(
                status_code=400,
                detail="Separate consent required for sensitive personal information"
            )
    
    # Record consent
    consent_record = await db.consent_records.create(
        user_email=user.email,  # Temporary identifier before user created
        consent_type=ConsentType.GENERAL,
        granted=True,
        granted_at=datetime.utcnow(),
        consent_method="checkbox",
        privacy_notice_version=consent.privacy_notice_version,
        ip_address=request.client.host,
        purposes=consent.purposes,
        data_categories=["identity", "contact"],
    )
    
    # Create user after consent recorded
    new_user = await db.users.create(user.dict())
    
    # Link consent to user
    await db.consent_records.update(
        consent_record.id,
        user_id=new_user.id,
    )
    
    logger.info(
        "user_created_with_consent",
        user_id=str(new_user.id),
        consent_id=str(consent_record.id),
    )
    
    return new_user
```

**Issue: PIPL-003 - Cross-border transfer without authorization**

```python
# ❌ Non-compliant: Sending data outside China without controls
@app.post("/api/analytics/sync")
async def sync_analytics(user_ids: list[str]):
    user_data = await db.users.get_many(user_ids)
    # Sending to US-based analytics server without authorization
    await analytics_api.send(user_data)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Cross-border transfer with PIPL requirements
from dataclasses import dataclass

@dataclass
class CrossBorderTransferAuth:
    """PIPL Chapter 3: Cross-border transfer authorization."""
    
    mechanism: str  # "cac_assessment", "standard_contract", "certification"
    authorization_id: str
    valid_until: datetime
    recipient_country: str
    recipient_name: str
    data_categories: list[str]
    purposes: list[str]

class CrossBorderTransferManager:
    def __init__(self):
        self.authorizations = {}
    
    async def verify_transfer_authorized(
        self,
        recipient_id: str,
        data_categories: list[str],
    ) -> CrossBorderTransferAuth:
        """Verify cross-border transfer is authorized per PIPL."""
        
        auth = self.authorizations.get(recipient_id)
        
        if not auth:
            raise TransferNotAuthorizedException(
                "No cross-border transfer authorization for this recipient"
            )
        
        if datetime.utcnow() > auth.valid_until:
            raise TransferNotAuthorizedException(
                "Cross-border transfer authorization has expired"
            )
        
        # Verify data categories are covered
        unauthorized_categories = set(data_categories) - set(auth.data_categories)
        if unauthorized_categories:
            raise TransferNotAuthorizedException(
                f"Transfer not authorized for categories: {unauthorized_categories}"
            )
        
        return auth
    
    async def verify_user_consent(
        self,
        user_id: str,
        recipient_country: str,
    ) -> bool:
        """PIPL Art. 39: Separate consent for cross-border transfer."""
        
        consent = await db.consent_records.get_latest(
            user_id=user_id,
            consent_type=ConsentType.CROSS_BORDER,
        )
        
        if not consent or not consent.granted:
            return False
        
        if consent.withdrawn_at:
            return False
        
        return True

transfer_manager = CrossBorderTransferManager()

@app.post("/api/analytics/sync")
async def sync_analytics(user_ids: list[str]):
    """Sync analytics with PIPL cross-border controls."""
    
    # PIPL Art. 38: Verify transfer authorization mechanism
    auth = await transfer_manager.verify_transfer_authorized(
        recipient_id="analytics_us",
        data_categories=["usage_analytics", "device_info"],
    )
    
    # PIPL Art. 39: Verify separate consent for each user
    authorized_users = []
    unauthorized_users = []
    
    for user_id in user_ids:
        has_consent = await transfer_manager.verify_user_consent(
            user_id=user_id,
            recipient_country=auth.recipient_country,
        )
        if has_consent:
            authorized_users.append(user_id)
        else:
            unauthorized_users.append(user_id)
    
    if unauthorized_users:
        logger.warning(
            "cross_border_transfer_blocked",
            reason="missing_consent",
            user_count=len(unauthorized_users),
        )
    
    if not authorized_users:
        return {"synced": 0, "blocked": len(unauthorized_users)}
    
    # Proceed with authorized transfers only
    user_data = await db.users.get_many(authorized_users)
    
    # PIPL: Log cross-border transfer
    await log_cross_border_transfer(
        authorization_id=auth.authorization_id,
        recipient=auth.recipient_name,
        country=auth.recipient_country,
        user_count=len(authorized_users),
        data_categories=["usage_analytics", "device_info"],
    )
    
    await analytics_api.send(user_data)
    
    return {
        "synced": len(authorized_users),
        "blocked": len(unauthorized_users),
    }
```

**Issue: PIPL-009 - Minor's data without guardian consent**

```python
# ❌ Non-compliant: Processing minor's data without guardian consent
@app.post("/api/game/register")
async def register_player(player: PlayerRegistration):
    return await db.players.create(player.dict())
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Minor's data with guardian consent per PIPL Art. 31
from datetime import date
from dateutil.relativedelta import relativedelta

MINOR_AGE_THRESHOLD = 14  # PIPL defines minors as under 14

class GuardianConsent(Base):
    """PIPL Art. 31: Guardian consent for minors."""
    __tablename__ = "guardian_consents"
    
    id = Column(UUID, primary_key=True)
    minor_id = Column(UUID, ForeignKey("users.id"))
    guardian_name = Column(String)
    guardian_relationship = Column(String)
    guardian_id_verified = Column(Boolean)
    consent_granted = Column(Boolean)
    consent_date = Column(DateTime)
    verification_method = Column(String)

def calculate_age(birth_date: date) -> int:
    today = date.today()
    return relativedelta(today, birth_date).years

@app.post("/api/game/register")
async def register_player(
    player: PlayerRegistration,
    guardian_consent: Optional[GuardianConsentSubmission] = None,
):
    """Register player with PIPL minor protection."""
    
    age = calculate_age(player.birth_date)
    
    # PIPL Art. 31: Special protection for minors
    if age < MINOR_AGE_THRESHOLD:
        logger.info(
            "minor_registration_attempt",
            age=age,
            has_guardian_consent=guardian_consent is not None,
        )
        
        if not guardian_consent:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "guardian_consent_required",
                    "message": "Guardian consent required for users under 14",
                    "required_fields": ["guardian_name", "guardian_relationship", "guardian_verification"],
                }
            )
        
        # Verify guardian consent
        if not guardian_consent.guardian_verified:
            raise HTTPException(
                status_code=400,
                detail="Guardian identity must be verified"
            )
        
        # Create player record
        new_player = await db.players.create({
            **player.dict(),
            "is_minor": True,
            "requires_guardian_consent": True,
        })
        
        # Record guardian consent
        await db.guardian_consents.create(
            minor_id=new_player.id,
            guardian_name=guardian_consent.guardian_name,
            guardian_relationship=guardian_consent.relationship,
            guardian_id_verified=guardian_consent.guardian_verified,
            consent_granted=True,
            consent_date=datetime.utcnow(),
            verification_method=guardian_consent.verification_method,
        )
        
        # PIPL: Formulate specific processing rules for minors
        await apply_minor_protection_rules(new_player.id)
        
        logger.info(
            "minor_registered_with_guardian_consent",
            player_id=str(new_player.id),
            age=age,
        )
        
        return new_player
    
    # Adult registration
    return await db.players.create(player.dict())

async def apply_minor_protection_rules(player_id: str):
    """PIPL Art. 31: Specific rules for processing minor's PI."""
    
    rules = {
        "data_minimization": True,
        "sensitive_features_disabled": ["location_tracking", "behavioral_profiling"],
        "marketing_prohibited": True,
        "play_time_limits": True,
        "parental_controls_enabled": True,
    }
    
    await db.player_settings.update(player_id, **rules)
```

## Data Localization Implementation

```python
# PIPL Art. 40: Data localization for critical infrastructure
class DataLocationRouter:
    def __init__(self):
        self.china_regions = ["cn-north", "cn-south", "cn-east"]
        self.china_database = get_china_database()
        self.global_database = get_global_database()
    
    async def route_user_data(
        self,
        user: User,
        data: dict,
    ):
        """Route data based on user location per PIPL."""
        
        if self._is_china_user(user):
            # PIPL: Store in China
            await self.china_database.store(user.id, data)
            
            logger.info(
                "data_stored_china",
                user_id=str(user.id),
                region="cn",
            )
        else:
            await self.global_database.store(user.id, data)
    
    def _is_china_user(self, user: User) -> bool:
        return user.country == "CN" or user.registration_country == "CN"

# Personal Information Protection Impact Assessment (PIPIA)
class PIImpactAssessment:
    """PIPL Art. 55: Personal Information Protection Impact Assessment."""
    
    REQUIRED_SCENARIOS = [
        "sensitive_pi_processing",
        "automated_decision_making",
        "third_party_disclosure",
        "cross_border_transfer",
        "public_disclosure",
        "large_scale_processing",
    ]
    
    async def conduct_assessment(
        self,
        processing_activity: str,
        purposes: list[str],
        data_categories: list[str],
    ) -> dict:
        """Conduct PIPIA per PIPL Art. 56."""
        
        assessment = {
            "assessment_id": str(uuid.uuid4()),
            "date": datetime.utcnow().isoformat(),
            "processing_activity": processing_activity,
            
            # Art. 56(1): Legality and necessity
            "legal_basis_assessment": {
                "has_legal_basis": True,
                "basis_type": "consent",
                "necessity_justified": True,
            },
            
            # Art. 56(2): Impact on rights and interests
            "rights_impact": {
                "risk_level": "medium",
                "affected_rights": ["privacy", "dignity"],
                "number_affected": "large_scale",
            },
            
            # Art. 56(3): Security measures
            "security_measures": {
                "encryption": True,
                "access_control": True,
                "audit_logging": True,
                "incident_response": True,
            },
            
            # Conclusion
            "risk_accepted": True,
            "mitigations": [
                "Enhanced consent flow",
                "Data minimization",
                "Regular audits",
            ],
        }
        
        await db.impact_assessments.create(assessment)
        
        return assessment
```

## SDK Integration

```python
from complianceagent import configure, pipl_consent, pipl_localize, pipl_minor

configure(regulations=["PIPL"])

# Consent-protected processing
@pipl_consent(
    consent_type="general",
    purposes=["service_provision"],
)
async def process_user_data(user_id: str, data: dict):
    return await service.process(user_id, data)

# Data localization
@pipl_localize(region="cn")
async def store_china_user_data(user_id: str, data: dict):
    return await db.store(user_id, data)

# Minor protection
@pipl_minor(require_guardian_consent=True)
async def process_minor_data(user_id: str, birth_date: date):
    return await service.process_minor(user_id)
```

## Compliance Dashboard

```
Dashboard → Compliance → PIPL

┌─────────────────────────────────────────────────────────┐
│ PIPL Compliance Status                                  │
├─────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Compliant                            │
│                                                         │
│ Consent Management:                                     │
│   Active Consents:         1,234,567                   │
│   Withdrawal Rate:         0.3%                        │
│   Sensitive PI Consents:   45,678                      │
│                                                         │
│ Data Localization:                                      │
│   China Users:             456,789                     │
│   Data Location:           ✅ China (cn-north-1)       │
│   Local Storage:           ✅ 100% compliant           │
│                                                         │
│ Cross-border Transfers:                                 │
│   Authorization Type:      Standard Contract           │
│   CAC Filing:              ✅ Approved                 │
│   User Consents:           89% obtained                │
│                                                         │
│ Minor Protection:                                       │
│   Minors Registered:       12,345                      │
│   Guardian Consents:       ✅ 100%                     │
│   Protection Rules:        ✅ Active                   │
│                                                         │
│ Impact Assessments:                                     │
│   Total Conducted:         15                          │
│   Pending Review:          2                           │
└─────────────────────────────────────────────────────────┘
```

## Resources

- [PIPL Full Text (Chinese)](http://www.npc.gov.cn/npc/c30834/202108/a8c4e3672c74491a80b53a172bb753fe.shtml)
- [PIPL English Translation](https://digichina.stanford.edu/work/translation-personal-information-protection-law-of-the-peoples-republic-of-china-effective-nov-1-2021/)
- [CAC Standard Contract Measures](https://www.cac.gov.cn/)
- [TC260 Security Specifications](https://www.tc260.org.cn/)

## Related Documentation

- [GDPR Compliance](gdpr.md) - EU data protection comparison
- [CCPA Compliance](ccpa.md) - California privacy law
- [Security Best Practices](../guides/security.md)
