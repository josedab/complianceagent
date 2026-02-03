# NIS2 Directive Compliance Guide

This guide covers how ComplianceAgent helps you achieve and maintain compliance with the EU NIS2 Directive (Network and Information Security Directive 2).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Directive (EU) 2022/2555 on Network and Information Security |
| **Jurisdiction** | European Union |
| **Effective Date** | January 16, 2023 (transposition deadline: October 17, 2024) |
| **Enforcing Authority** | National competent authorities in each EU Member State |
| **Applies To** | Essential and important entities in critical sectors |
| **Max Penalty** | €10M or 2% of global annual turnover (essential entities) |

## Scope

### Essential Entities

High criticality sectors with stricter requirements:

| Sector | Examples |
|--------|----------|
| **Energy** | Electricity, oil, gas, hydrogen, district heating |
| **Transport** | Air, rail, water, road transport |
| **Banking** | Credit institutions |
| **Financial Market** | Trading venues, central counterparties |
| **Health** | Healthcare providers, EU reference laboratories |
| **Drinking Water** | Water supply and distribution |
| **Wastewater** | Wastewater collection and treatment |
| **Digital Infrastructure** | DNS, TLD registries, cloud, data centers, CDNs |
| **ICT Service Management** | Managed service providers, managed security providers |
| **Public Administration** | Central government entities |
| **Space** | Ground-based infrastructure operators |

### Important Entities

Other critical sectors with standard requirements:

| Sector | Examples |
|--------|----------|
| **Postal and Courier** | Postal service providers |
| **Waste Management** | Waste collection and treatment |
| **Chemicals** | Manufacturing and distribution |
| **Food** | Production and distribution |
| **Manufacturing** | Medical devices, machinery, vehicles, electronics |
| **Digital Providers** | Online marketplaces, search engines, social networks |
| **Research** | Research organizations |

## Key Requirements

### Risk Management Measures (Article 21)

| Measure | Description | Code Impact |
|---------|-------------|-------------|
| **Risk Analysis** | Policies for risk analysis and IS security | Security assessments, threat modeling |
| **Incident Handling** | Detection, response, and recovery | Logging, alerting, incident response |
| **Business Continuity** | Backup, DR, crisis management | Redundancy, failover, backup systems |
| **Supply Chain Security** | Secure supplier relationships | Third-party assessments, SBOMs |
| **Secure Development** | Security in acquisition and development | SSDLC, code review, testing |
| **Effectiveness Assessment** | Policies to assess security measures | Penetration testing, audits |
| **Cyber Hygiene** | Basic practices and training | Security training, awareness |
| **Cryptography** | Policies on encryption use | Encryption standards, key management |
| **HR Security** | Access control, asset management | RBAC, IAM, asset inventory |
| **MFA/Secure Auth** | Multi-factor and continuous authentication | MFA implementation, SSO |

### Incident Reporting (Article 23)

| Notification | Deadline | Content |
|--------------|----------|---------|
| **Early Warning** | 24 hours | Suspected significant incident |
| **Incident Notification** | 72 hours | Initial assessment, severity, impact |
| **Intermediate Report** | On request | Status updates |
| **Final Report** | 1 month | Root cause, mitigation, cross-border impact |

### Significant Incident Criteria

An incident is significant if it:
- Causes or may cause severe operational disruption or financial loss
- Affects or may affect other natural or legal persons by causing considerable damage

## ComplianceAgent Detection

### Automatically Detected Issues

```
NIS2-001: Missing incident detection mechanisms
NIS2-002: Inadequate logging for security events
NIS2-003: No multi-factor authentication implementation
NIS2-004: Missing encryption for data in transit
NIS2-005: Inadequate access control mechanisms
NIS2-006: No backup or recovery procedures
NIS2-007: Missing vulnerability management
NIS2-008: Insecure third-party dependencies
NIS2-009: No security in development lifecycle
NIS2-010: Missing network segmentation
```

### Example Detection

**Issue: NIS2-001 - Missing incident detection**

```python
# ❌ Non-compliant: No security event detection
@app.post("/api/login")
async def login(credentials: LoginRequest):
    user = await authenticate(credentials.email, credentials.password)
    if user:
        return {"token": create_token(user)}
    return {"error": "Invalid credentials"}
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Security event detection and logging
import structlog
from datetime import datetime, timedelta
from collections import defaultdict

logger = structlog.get_logger()
failed_attempts = defaultdict(list)

BRUTE_FORCE_THRESHOLD = 5
BRUTE_FORCE_WINDOW = timedelta(minutes=15)

@app.post("/api/login")
async def login(credentials: LoginRequest, request: Request):
    client_ip = request.client.host
    
    # NIS2 Art. 21: Incident detection - check for brute force
    recent_failures = [
        t for t in failed_attempts[client_ip]
        if datetime.utcnow() - t < BRUTE_FORCE_WINDOW
    ]
    
    if len(recent_failures) >= BRUTE_FORCE_THRESHOLD:
        # Log potential security incident
        logger.warning(
            "potential_brute_force_attack",
            ip_address=client_ip,
            attempt_count=len(recent_failures),
            email=credentials.email,
        )
        # Alert security team for incident handling
        await alert_security_incident(
            incident_type="brute_force_attempt",
            severity="medium",
            details={"ip": client_ip, "attempts": len(recent_failures)},
        )
        raise HTTPException(429, "Too many failed attempts")
    
    user = await authenticate(credentials.email, credentials.password)
    
    if not user:
        failed_attempts[client_ip].append(datetime.utcnow())
        logger.info(
            "login_failure",
            ip_address=client_ip,
            email=credentials.email,
        )
        raise HTTPException(401, "Invalid credentials")
    
    # Clear failed attempts on success
    failed_attempts[client_ip].clear()
    
    logger.info(
        "login_success",
        user_id=str(user.id),
        ip_address=client_ip,
    )
    
    return {"token": create_token(user)}
```

**Issue: NIS2-003 - Missing MFA**

```python
# ❌ Non-compliant: Single-factor authentication only
@app.get("/api/admin/settings")
@require_authentication
async def get_admin_settings(current_user: User):
    return await db.settings.get_all()
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: MFA required for sensitive operations
import pyotp

@app.get("/api/admin/settings")
@require_authentication
@require_mfa  # NIS2 Art. 21(2)(j): MFA for sensitive access
async def get_admin_settings(current_user: User):
    # Verify MFA was completed in current session
    if not current_user.mfa_verified_at:
        raise HTTPException(
            status_code=403,
            detail="MFA verification required for admin access"
        )
    
    # Check MFA verification is recent (within 15 minutes)
    if datetime.utcnow() - current_user.mfa_verified_at > timedelta(minutes=15):
        raise HTTPException(
            status_code=403,
            detail="MFA verification expired, please re-authenticate"
        )
    
    return await db.settings.get_all()

# MFA verification endpoint
@app.post("/api/auth/mfa/verify")
@require_authentication
async def verify_mfa(
    mfa_code: MFAVerifyRequest,
    current_user: User,
):
    totp = pyotp.TOTP(current_user.mfa_secret)
    
    if not totp.verify(mfa_code.code, valid_window=1):
        logger.warning(
            "mfa_verification_failed",
            user_id=str(current_user.id),
        )
        raise HTTPException(401, "Invalid MFA code")
    
    # Update MFA verification timestamp
    await db.users.update(
        current_user.id,
        mfa_verified_at=datetime.utcnow(),
    )
    
    logger.info(
        "mfa_verification_success",
        user_id=str(current_user.id),
    )
    
    return {"status": "verified"}
```

**Issue: NIS2-008 - Insecure dependencies**

```python
# ❌ Non-compliant: No dependency vulnerability checking
# requirements.txt with outdated packages
flask==1.0.0  # Known vulnerabilities
requests==2.20.0  # Known vulnerabilities
```

**ComplianceAgent Fix:**

```yaml
# ✅ Compliant: Automated dependency scanning in CI/CD
# .github/workflows/security.yml
name: NIS2 Security Checks

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # NIS2 Art. 21(2)(e): Secure development - dependency scanning
      - name: Python dependency audit
        run: |
          pip install pip-audit
          pip-audit -r requirements.txt --strict
      
      - name: Node.js dependency audit
        run: npm audit --audit-level=high
      
      # Generate SBOM for supply chain security
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          format: spdx-json
          output-file: sbom.spdx.json
      
      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx.json
```

## Incident Response Framework

```python
# NIS2-compliant incident response
from enum import Enum
from datetime import datetime, timedelta

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NIS2Incident:
    def __init__(self, incident_type: str, severity: IncidentSeverity):
        self.id = str(uuid.uuid4())
        self.type = incident_type
        self.severity = severity
        self.detected_at = datetime.utcnow()
        self.status = "detected"
        
        # NIS2 reporting deadlines
        self.early_warning_deadline = self.detected_at + timedelta(hours=24)
        self.notification_deadline = self.detected_at + timedelta(hours=72)
        self.final_report_deadline = self.detected_at + timedelta(days=30)

class IncidentManager:
    async def report_incident(self, incident: NIS2Incident):
        # Log incident
        await self.log_incident(incident)
        
        # Determine if significant (NIS2 criteria)
        if self.is_significant(incident):
            # Schedule required notifications
            await self.schedule_early_warning(incident)
            await self.schedule_incident_notification(incident)
            await self.schedule_final_report(incident)
            
            # Alert competent authority contact
            await self.notify_nis2_contact(incident)
    
    def is_significant(self, incident: NIS2Incident) -> bool:
        """Determine if incident meets NIS2 significance criteria."""
        return (
            incident.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]
            or self.affects_service_availability(incident)
            or self.affects_other_entities(incident)
        )
    
    async def schedule_early_warning(self, incident: NIS2Incident):
        """Schedule 24-hour early warning to competent authority."""
        await self.scheduler.schedule(
            task="send_early_warning",
            incident_id=incident.id,
            deadline=incident.early_warning_deadline,
        )
```

## Supply Chain Security

```python
# NIS2 Art. 21(2)(d): Supply chain security
class SupplierSecurityAssessment(Base):
    __tablename__ = "supplier_assessments"
    
    id = Column(UUID, primary_key=True)
    supplier_name = Column(String)
    supplier_type = Column(String)  # software, cloud, hardware, service
    
    # Assessment details
    last_assessment_date = Column(DateTime)
    next_assessment_date = Column(DateTime)
    risk_level = Column(String)  # low, medium, high, critical
    
    # NIS2 specific
    nis2_compliant = Column(Boolean)
    security_certifications = Column(ARRAY(String))  # ISO27001, SOC2, etc.
    incident_notification_clause = Column(Boolean)
    
    # SBOM tracking
    sbom_available = Column(Boolean)
    sbom_last_updated = Column(DateTime)

# Verify supplier compliance before integration
async def verify_supplier(supplier_id: str) -> bool:
    assessment = await db.supplier_assessments.get(supplier_id)
    
    if not assessment:
        raise ComplianceException("Supplier not assessed")
    
    if assessment.next_assessment_date < datetime.utcnow():
        raise ComplianceException("Supplier assessment expired")
    
    if assessment.risk_level == "critical" and not assessment.nis2_compliant:
        raise ComplianceException("Critical supplier must be NIS2 compliant")
    
    return True
```

## SDK Integration

```python
from complianceagent import configure, nis2_protected, incident_log

configure(regulations=["NIS2"])

# Protect critical infrastructure operations
@nis2_protected(sector="digital_infrastructure")
async def modify_dns_records(changes: DNSChanges):
    return await dns_service.apply(changes)

# Log security incidents
@incident_log(regulation="NIS2", auto_classify=True)
async def handle_security_event(event: SecurityEvent):
    return await process_event(event)

# Supply chain verification
@verify_supplier_compliance
async def integrate_third_party(service: ThirdPartyService):
    return await service.connect()
```

## Compliance Dashboard

```
Dashboard → Compliance → NIS2

┌─────────────────────────────────────────────────────────┐
│ NIS2 Compliance Status                                  │
├─────────────────────────────────────────────────────────┤
│ Entity Classification: Essential Entity                 │
│ Sector: Digital Infrastructure                          │
│ Overall Status: ✅ Compliant                            │
│                                                         │
│ Risk Management Measures (Art. 21):                     │
│   Risk Analysis:           ✅ Documented                │
│   Incident Handling:       ✅ Procedures in place       │
│   Business Continuity:     ✅ DR tested                 │
│   Supply Chain Security:   ✅ 23 suppliers assessed     │
│   Secure Development:      ✅ SSDLC implemented         │
│   Security Assessment:     ✅ Last pentest: 2024-01-15  │
│   Cyber Hygiene:           ✅ Training completed        │
│   Cryptography:            ✅ AES-256, TLS 1.3         │
│   Access Control:          ✅ RBAC + MFA               │
│                                                         │
│ Incident Reporting:                                     │
│   Open Incidents:          0                           │
│   Last 30 Days:            2 (both resolved)           │
│   Avg Response Time:       4.2 hours                   │
└─────────────────────────────────────────────────────────┘
```

## Best Practices

### 1. Defense in Depth

```python
# Multiple security layers per NIS2 requirements
@require_network_segmentation  # Network-level isolation
@require_authentication        # Identity verification
@require_mfa                   # Multi-factor auth
@require_role("operator")      # Authorization
@rate_limit(100, 60)          # DoS protection
@audit_log("critical_operation")  # Logging
async def critical_infrastructure_operation():
    pass
```

### 2. Continuous Monitoring

```python
# NIS2 Art. 21(2)(b): Incident handling requires detection
MONITORING_CONFIG = {
    "security_events": {
        "failed_logins": {"threshold": 5, "window": "5m", "action": "alert"},
        "privilege_escalation": {"threshold": 1, "window": "1m", "action": "block"},
        "data_exfiltration": {"threshold": 100, "window": "1h", "action": "alert"},
    },
    "availability": {
        "uptime_threshold": 99.9,
        "latency_threshold_ms": 500,
    },
}
```

### 3. Regular Testing

```python
# NIS2 Art. 21(2)(f): Assess effectiveness of measures
TESTING_SCHEDULE = {
    "vulnerability_scan": "weekly",
    "penetration_test": "annually",
    "incident_response_drill": "quarterly",
    "backup_recovery_test": "monthly",
    "supplier_assessment": "annually",
}
```

## Resources

- [NIS2 Directive Full Text](https://eur-lex.europa.eu/eli/dir/2022/2555)
- [ENISA NIS2 Guidance](https://www.enisa.europa.eu/topics/nis-directive)
- [National Transposition Status](https://digital-strategy.ec.europa.eu/en/policies/nis2-directive)

## Related Documentation

- [ISO 27001 Compliance](iso27001.md)
- [Security Best Practices](../guides/security.md)
- [Incident Response Runbook](../guides/runbook.md)
