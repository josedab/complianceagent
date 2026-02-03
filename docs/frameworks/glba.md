# GLBA Compliance Guide

This guide covers how ComplianceAgent helps you achieve and maintain compliance with the Gramm-Leach-Bliley Act (GLBA).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Gramm-Leach-Bliley Act (Financial Services Modernization Act) |
| **Jurisdiction** | United States |
| **Effective Date** | November 12, 1999 |
| **Enforcing Authorities** | FTC, SEC, OCC, FDIC, Federal Reserve, State regulators |
| **Applies To** | Financial institutions |
| **Key Rule** | Safeguards Rule (16 CFR Part 314) |

## Key Components

### Three Main Rules

| Rule | Focus | Requirement |
|------|-------|-------------|
| **Financial Privacy Rule** | Notice & Choice | Disclose privacy practices, allow opt-out |
| **Safeguards Rule** | Security Program | Implement comprehensive information security |
| **Pretexting Provisions** | Social Engineering | Prevent fraudulent access to NPI |

### Nonpublic Personal Information (NPI)

Information covered by GLBA:

| Included (NPI) | Excluded |
|----------------|----------|
| Social Security numbers | Publicly available information |
| Account numbers | Information from public records |
| Credit/debit card numbers | Information disclosed with consent |
| Income and credit history | Business contact information |
| Account balances | Widely distributed media information |
| Transaction history | |

## Safeguards Rule Requirements (2023 Update)

The updated Safeguards Rule requires:

### Designated Qualified Individual

| Requirement | Description |
|-------------|-------------|
| Designation | Appoint qualified individual to oversee security program |
| Accountability | Report to board/senior management |
| Expertise | Sufficient knowledge of information security |

### Risk Assessment

| Element | Implementation |
|---------|----------------|
| Inventory | Identify all systems handling NPI |
| Threats | Assess internal and external threats |
| Controls | Evaluate existing safeguards |
| Documentation | Written risk assessment |

### Required Safeguards

| Safeguard | Description | Code Impact |
|-----------|-------------|-------------|
| Access Controls | Limit access to authorized users | RBAC, authentication |
| Data Inventory | Know what NPI you have and where | Data classification |
| Encryption | Encrypt NPI in transit and at rest | TLS, AES-256 |
| MFA | Multi-factor authentication for NPI access | MFA implementation |
| Secure Development | Security in SDLC | Code review, testing |
| Change Management | Authorized changes only | Approval workflows |
| Monitoring | Continuous monitoring for threats | Logging, SIEM |
| Penetration Testing | Annual pen tests or continuous scanning | Security testing |
| Incident Response | Written incident response plan | IR procedures |
| Vendor Management | Assess service providers | Third-party assessments |

## ComplianceAgent Detection

### Automatically Detected Issues

```
GLBA-001: NPI accessible without authentication
GLBA-002: Missing encryption for NPI in transit
GLBA-003: Missing encryption for NPI at rest
GLBA-004: No MFA for NPI access
GLBA-005: Insufficient access logging
GLBA-006: NPI in application logs
GLBA-007: Hardcoded credentials
GLBA-008: Missing input validation on financial data
GLBA-009: Inadequate session management
GLBA-010: Third-party NPI sharing without controls
```

### Example Detection

**Issue: GLBA-002/003 - Unencrypted NPI**

```python
# ❌ Non-compliant: NPI stored and transmitted without encryption
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    ssn = Column(String)  # Stored in plaintext
    account_number = Column(String)  # Stored in plaintext
    income = Column(Numeric)

@app.get("/api/customers/{id}")
async def get_customer(id: int):
    # NPI returned without encryption
    return await db.customers.get(id)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: NPI encrypted at rest and in transit
from complianceagent import encrypt_field, EncryptedType
from sqlalchemy_utils import StringEncryptedType
from cryptography.fernet import Fernet

# GLBA Safeguards: Encryption at rest
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    # GLBA: Encrypt NPI at rest
    ssn = Column(StringEncryptedType(String, get_encryption_key()))
    account_number = Column(StringEncryptedType(String, get_encryption_key()))
    income = Column(StringEncryptedType(Numeric, get_encryption_key()))

# GLBA: Require MFA for NPI access
@app.get("/api/customers/{id}")
@require_authentication
@require_mfa
@require_role(["account_manager", "compliance_officer"])
@audit_log(action="npi_access", regulation="GLBA")
async def get_customer(
    id: int,
    current_user: User = Depends(get_current_user),
):
    # GLBA: Log all NPI access
    await log_npi_access(
        user_id=current_user.id,
        customer_id=id,
        fields_accessed=["ssn", "account_number", "income"],
    )
    
    customer = await db.customers.get(id)
    
    # GLBA: Mask sensitive data in response unless needed
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        ssn_last_four=customer.ssn[-4:],  # Only last 4
        account_masked=mask_account(customer.account_number),
    )
```

**Issue: GLBA-004 - No MFA for NPI access**

```python
# ❌ Non-compliant: Single-factor auth for financial data
@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate(credentials.email, credentials.password)
    if user:
        return {"token": create_access_token(user)}
    raise HTTPException(401, "Invalid credentials")

@app.get("/api/accounts/{account_id}/transactions")
@require_authentication  # Only password auth required
async def get_transactions(account_id: str):
    return await db.transactions.get_by_account(account_id)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: MFA required for NPI access
import pyotp
from datetime import datetime, timedelta

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate(credentials.email, credentials.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # GLBA: MFA required - return partial token
    return {
        "mfa_required": True,
        "mfa_token": create_mfa_challenge_token(user),
        "methods": user.mfa_methods,  # ["totp", "sms"]
    }

@app.post("/api/auth/mfa/verify")
async def verify_mfa(mfa_request: MFAVerifyRequest):
    user = await get_user_from_mfa_token(mfa_request.mfa_token)
    
    # Verify TOTP code
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(mfa_request.code, valid_window=1):
        await log_failed_mfa(user.id)
        raise HTTPException(401, "Invalid MFA code")
    
    # GLBA: Full access granted after MFA
    return {
        "access_token": create_access_token(user, mfa_verified=True),
        "expires_in": 3600,
    }

# GLBA: MFA verification required for NPI access
@app.get("/api/accounts/{account_id}/transactions")
@require_authentication
@require_mfa_verified  # Checks mfa_verified claim in token
@audit_log(action="transaction_access", regulation="GLBA")
async def get_transactions(account_id: str, current_user: User):
    return await db.transactions.get_by_account(account_id)
```

**Issue: GLBA-006 - NPI in logs**

```python
# ❌ Non-compliant: NPI written to application logs
import logging
logger = logging.getLogger(__name__)

@app.post("/api/accounts/verify")
async def verify_account(account: AccountVerify):
    logger.info(f"Verifying account: SSN={account.ssn}, Account={account.account_number}")
    # SSN and account number logged in plaintext
    result = await verify_with_bank(account)
    logger.info(f"Verification result for {account.ssn}: {result}")
    return result
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: NPI redacted from logs
import structlog
from complianceagent import redact_npi

logger = structlog.get_logger()

# Configure log processor to redact NPI
structlog.configure(
    processors=[
        redact_npi(),  # Automatically redacts SSN, account numbers, etc.
        structlog.processors.JSONRenderer(),
    ]
)

@app.post("/api/accounts/verify")
@audit_log(action="account_verification", regulation="GLBA")
async def verify_account(account: AccountVerify):
    # GLBA: Log without NPI
    logger.info(
        "account_verification_started",
        ssn_last_four=account.ssn[-4:],
        account_masked=f"***{account.account_number[-4:]}",
        request_id=request.state.request_id,
    )
    
    result = await verify_with_bank(account)
    
    logger.info(
        "account_verification_completed",
        ssn_last_four=account.ssn[-4:],
        result_status=result.status,
        request_id=request.state.request_id,
    )
    
    return result
```

## Privacy Notice Requirements

### Required Disclosures

```python
# Privacy notice content requirements
PRIVACY_NOTICE_SECTIONS = {
    "categories_collected": [
        "Information from applications (name, SSN, income)",
        "Information from transactions (account balances, payment history)",
        "Information from consumer reports (credit history)",
    ],
    "categories_disclosed": [
        "To process transactions you request",
        "To service providers who work on our behalf",
        "As permitted or required by law",
    ],
    "opt_out_rights": {
        "description": "You may opt out of information sharing with non-affiliates",
        "methods": ["Online at [URL]", "Call [Phone]", "Mail opt-out form"],
        "deadline": "30 days to process opt-out request",
    },
    "security_practices": "We maintain physical, electronic, and procedural safeguards",
}
```

### Opt-Out Implementation

```python
@app.post("/api/privacy/opt-out")
@require_authentication
async def opt_out_sharing(
    opt_out: OptOutRequest,
    current_user: User = Depends(get_current_user),
):
    """GLBA: Allow customers to opt out of NPI sharing."""
    
    await db.privacy_preferences.update(
        customer_id=current_user.customer_id,
        share_with_affiliates=not opt_out.affiliates,
        share_with_nonaffiliates=not opt_out.nonaffiliates,
        share_for_marketing=not opt_out.marketing,
    )
    
    await audit_log(
        action="privacy_opt_out",
        customer_id=current_user.customer_id,
        preferences=opt_out.dict(),
    )
    
    return {"status": "preferences_updated"}
```

## SDK Integration

```python
from complianceagent import configure, glba_protected, require_mfa, audit_log

configure(regulations=["GLBA"])

# Protect NPI access
@glba_protected(data_types=["ssn", "account_number"])
async def get_customer_npi(customer_id: str):
    return await db.customers.get_sensitive(customer_id)

# Require MFA for NPI operations
@require_mfa
@glba_protected()
async def transfer_funds(transfer: TransferRequest):
    return await process_transfer(transfer)

# Audit all NPI access
@audit_log(action="npi_access", regulation="GLBA", log_fields=["customer_id"])
async def view_account_details(account_id: str):
    return await db.accounts.get(account_id)
```

## Vendor Management

```python
# GLBA requires assessing service provider security
class ServiceProviderAssessment(Base):
    __tablename__ = "service_provider_assessments"
    
    id = Column(UUID, primary_key=True)
    provider_name = Column(String)
    service_type = Column(String)
    npi_access = Column(Boolean)
    
    # Assessment details
    security_assessment_date = Column(DateTime)
    assessment_result = Column(String)  # approved, conditional, rejected
    contract_includes_security_requirements = Column(Boolean)
    
    # Monitoring
    last_audit_date = Column(DateTime)
    next_audit_date = Column(DateTime)
    incidents_reported = Column(Integer, default=0)

# Before sharing NPI with vendor
async def share_with_vendor(vendor_id: str, data: dict):
    assessment = await db.assessments.get_by_vendor(vendor_id)
    
    if not assessment or assessment.assessment_result != "approved":
        raise ComplianceException(
            "GLBA: Cannot share NPI with unapproved service provider"
        )
    
    if assessment.next_audit_date < datetime.utcnow():
        raise ComplianceException(
            "GLBA: Service provider assessment expired"
        )
    
    # Proceed with sharing
    await vendor_api.send(data)
```

## Compliance Dashboard

```
Dashboard → Compliance → GLBA

┌─────────────────────────────────────────────────────────┐
│ GLBA Compliance Status                                  │
├─────────────────────────────────────────────────────────┤
│ Overall Status: ✅ Compliant                            │
│                                                         │
│ Safeguards Rule:                                        │
│   Access Controls:         ✅ Implemented               │
│   Encryption (Transit):    ✅ TLS 1.3                   │
│   Encryption (Rest):       ✅ AES-256                   │
│   MFA for NPI:             ✅ Required                  │
│   Audit Logging:           ✅ 100% coverage            │
│   Penetration Test:        ✅ Last: 2024-01-15         │
│                                                         │
│ Privacy Rule:                                           │
│   Privacy Notice:          ✅ Published                 │
│   Opt-Out Mechanism:       ✅ Active                   │
│   Opt-Out Requests:        23 (last 30 days)           │
│                                                         │
│ Vendor Management:                                      │
│   Assessed Providers:      12                          │
│   Pending Assessments:     ⚠️  2                        │
└─────────────────────────────────────────────────────────┘
```

## Incident Response

GLBA requires incident response procedures:

```python
# Incident response workflow
class SecurityIncident(Base):
    __tablename__ = "security_incidents"
    
    id = Column(UUID, primary_key=True)
    incident_type = Column(String)
    severity = Column(String)
    npi_affected = Column(Boolean)
    
    # Timeline
    detected_at = Column(DateTime)
    contained_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Impact
    records_affected = Column(Integer)
    customers_notified = Column(Boolean)
    regulators_notified = Column(Boolean)

@app.post("/api/security/incidents")
@require_role(["security_team"])
async def report_incident(incident: IncidentReport):
    """Report and track security incidents per GLBA requirements."""
    
    record = await db.incidents.create(incident)
    
    # GLBA: Notify if NPI breach
    if incident.npi_affected and incident.severity in ["high", "critical"]:
        await notify_compliance_officer(record)
        await schedule_customer_notification(record)
        await prepare_regulator_notification(record)
    
    return record
```

## Resources

- [GLBA Safeguards Rule (16 CFR Part 314)](https://www.ecfr.gov/current/title-16/part-314)
- [FTC GLBA Resources](https://www.ftc.gov/business-guidance/privacy-security/gramm-leach-bliley-act)
- [Safeguards Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/ftc-safeguards-rule-what-your-business-needs-know)

## Related Documentation

- [PCI-DSS Compliance](pci-dss.md) - Payment card data
- [SOC 2 Compliance](soc2.md) - Service organization controls
- [Security Best Practices](../guides/security.md)
