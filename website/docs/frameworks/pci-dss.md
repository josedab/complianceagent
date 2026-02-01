---
sidebar_position: 6
title: PCI-DSS
description: Payment Card Industry Data Security Standard compliance with ComplianceAgent
---

# PCI-DSS Compliance

The Payment Card Industry Data Security Standard (PCI-DSS) protects cardholder data. ComplianceAgent supports PCI-DSS v4.0.

## Overview

| Attribute | Value |
|-----------|-------|
| **Jurisdiction** | Global |
| **Current Version** | 4.0 (March 2022) |
| **Applies To** | Merchants, service providers handling card data |
| **Enforcement** | Card brands, acquiring banks |
| **Requirements Tracked** | 312 |

## Compliance Levels

| Level | Transactions/Year | Requirements |
|-------|-------------------|--------------|
| 1 | >6M | Annual QSA audit, quarterly scans |
| 2 | 1-6M | Annual SAQ, quarterly scans |
| 3 | 20K-1M e-commerce | Annual SAQ, quarterly scans |
| 4 | &lt;20K e-commerce, &lt;1M other | Annual SAQ, quarterly scans |

## 12 Requirements

### Build and Maintain Secure Network

#### Requirement 1: Network Security Controls

```yaml
# ComplianceAgent checks for:
network_security:
  firewall_configuration:
    - inbound_rules_restrictive: true
    - outbound_rules_restrictive: true
    - default_deny: true
    - documented: true
  
  segmentation:
    - cde_isolated: true
    - network_diagram: true
    - data_flow_diagram: true
```

#### Requirement 2: Secure Configurations

```python
# Configuration baseline checking
SECURE_DEFAULTS = {
    "vendor_defaults_changed": True,
    "unnecessary_services_disabled": True,
    "insecure_protocols_disabled": True,
    "system_hardening_applied": True
}

async def check_secure_configuration(system: System) -> ComplianceResult:
    """Verify secure configuration per PCI-DSS 2.x."""
    issues = []
    
    # Check vendor defaults
    if await has_default_credentials(system):
        issues.append("Default credentials not changed")
    
    # Check unnecessary services
    unnecessary = await find_unnecessary_services(system)
    if unnecessary:
        issues.append(f"Unnecessary services running: {unnecessary}")
    
    # Check insecure protocols
    insecure = await find_insecure_protocols(system)
    if insecure:
        issues.append(f"Insecure protocols enabled: {insecure}")
    
    return ComplianceResult(
        requirement="2",
        compliant=len(issues) == 0,
        issues=issues
    )
```

### Protect Account Data

#### Requirement 3: Protect Stored Data

```python
class CardDataProtection:
    """PCI-DSS Requirement 3 implementation."""
    
    # 3.2: Don't store sensitive authentication data
    NEVER_STORE = [
        "full_track_data",
        "cvv2_cvc2_cid",
        "pin_pin_block"
    ]
    
    # 3.4: Render PAN unreadable
    async def store_pan(self, pan: str) -> str:
        """Store PAN per PCI-DSS 3.4."""
        options = [
            self.tokenize,           # Preferred: Replace with token
            self.encrypt_strong,     # AES-256 with key management
            self.truncate,           # First 6 + last 4 only
            self.hash_one_way        # Keyed cryptographic hash
        ]
        # Using tokenization as primary method
        return await self.tokenize(pan)
    
    async def tokenize(self, pan: str) -> str:
        """Replace PAN with non-reversible token."""
        token = await self.token_service.create_token(pan)
        # Token stored in separate, segmented environment
        return token
    
    def mask_pan(self, pan: str) -> str:
        """Display PAN per PCI-DSS 3.3."""
        # Show max first 6 and last 4
        return f"{pan[:6]}******{pan[-4:]}"
```

#### Requirement 4: Protect Data in Transit

```python
class TransmissionSecurity:
    """PCI-DSS Requirement 4 implementation."""
    
    def configure_tls(self) -> SSLContext:
        """Configure TLS per PCI-DSS 4.1."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Minimum TLS 1.2 (TLS 1.3 preferred)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Strong cipher suites only
        context.set_ciphers(
            "ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20"
        )
        
        return context
    
    async def validate_certificate(self, cert: Certificate) -> bool:
        """Validate server certificates."""
        return all([
            cert.is_valid(),
            cert.not_expired(),
            cert.chain_validates(),
            cert.matches_hostname()
        ])
```

### Maintain Vulnerability Management

#### Requirement 5: Anti-Malware

```yaml
anti_malware:
  deployment:
    - all_systems_protected: true
    - automatic_updates: true
    - periodic_scans: true
  
  monitoring:
    - audit_logs_enabled: true
    - cannot_be_disabled_by_users: true
```

#### Requirement 6: Secure Development

```python
class SecureDevelopment:
    """PCI-DSS Requirement 6 implementation."""
    
    # 6.2: Software development security
    SDLC_REQUIREMENTS = {
        "secure_coding_training": "annual",
        "code_review": "all_changes",
        "testing": "before_production",
        "separation_of_environments": True
    }
    
    # 6.3: Security vulnerabilities identified and addressed
    async def manage_vulnerabilities(self):
        """Vulnerability management per 6.3."""
        return VulnerabilityManagement(
            sources=["cve", "nvd", "vendor_advisories"],
            risk_ranking=True,
            critical_patches="within_30_days",
            high_patches="within_90_days"
        )
    
    # 6.4: Web application security
    OWASP_TOP_10_CONTROLS = [
        "injection_prevention",
        "broken_authentication",
        "sensitive_data_exposure",
        "xxe",
        "broken_access_control",
        "security_misconfiguration",
        "xss",
        "insecure_deserialization",
        "vulnerable_components",
        "insufficient_logging"
    ]
```

### Strong Access Control

#### Requirement 7: Restrict Access

```python
class AccessControl:
    """PCI-DSS Requirement 7 - Need to know."""
    
    async def verify_access(
        self, 
        user: User, 
        resource: Resource
    ) -> bool:
        """Verify need-to-know access."""
        
        # Check role-based access
        if not self.role_permits(user.role, resource):
            return False
        
        # Check need-to-know
        if not self.business_need(user, resource):
            return False
        
        # Log access
        await self.log_access(user, resource)
        
        return True
    
    def define_access_matrix(self):
        """Document access control matrix."""
        return AccessMatrix(
            roles=[
                Role("admin", ["all_cde_access"]),
                Role("operator", ["view_transactions"]),
                Role("developer", ["no_cde_access"]),
            ],
            default="deny_all"
        )
```

#### Requirement 8: Identify Users

```python
class IdentityManagement:
    """PCI-DSS Requirement 8 implementation."""
    
    # 8.2: User identification
    async def authenticate_user(self, credentials: Credentials) -> User:
        # Unique ID for each user
        assert credentials.user_id is not None
        
        # Verify credentials
        user = await self.verify_password(
            credentials.user_id,
            credentials.password
        )
        
        # MFA for remote access (8.4)
        if self.is_remote_access():
            await self.require_mfa(user)
        
        return user
    
    # 8.3: Password requirements
    PASSWORD_POLICY = {
        "minimum_length": 12,  # Increased in v4.0
        "complexity": "numeric_and_alpha",
        "history": 4,  # Cannot reuse last 4
        "max_age_days": 90,
        "lockout_threshold": 10,
        "lockout_duration_minutes": 30
    }
```

#### Requirement 9: Restrict Physical Access

```yaml
physical_security:
  facility_access:
    - badge_readers: true
    - visitor_logs: true
    - escort_required: true
  
  media_handling:
    - inventory_maintained: true
    - secure_destruction: true
    - media_encryption: true
```

### Monitor and Test Networks

#### Requirement 10: Logging and Monitoring

```python
class AuditLogging:
    """PCI-DSS Requirement 10 implementation."""
    
    # Events to log (10.2)
    AUDITABLE_EVENTS = [
        "user_access_to_cardholder_data",
        "all_actions_by_admin",
        "access_to_audit_trails",
        "invalid_access_attempts",
        "identification_mechanism_changes",
        "initialization_of_audit_logs",
        "creation_deletion_system_objects"
    ]
    
    # Log entry requirements (10.3)
    def create_log_entry(self, event: Event) -> LogEntry:
        return LogEntry(
            user_id=event.user_id,
            event_type=event.type,
            date_time=datetime.utcnow(),
            success_failure=event.result,
            origination=event.source_ip,
            affected_data=event.resource_id
        )
    
    # Time synchronization (10.4)
    def sync_time(self):
        """Synchronize time across systems."""
        return NTPConfiguration(
            servers=["time.nist.gov", "pool.ntp.org"],
            sync_frequency="hourly"
        )
    
    # Log retention (10.5)
    LOG_RETENTION = {
        "immediately_available": "3_months",
        "total_retention": "1_year"
    }
```

#### Requirement 11: Test Security

```python
class SecurityTesting:
    """PCI-DSS Requirement 11 implementation."""
    
    async def vulnerability_scan(self) -> ScanResult:
        """Quarterly vulnerability scans (11.2)."""
        return await self.asv_scanner.scan(
            targets=self.external_ips,
            frequency="quarterly",
            passing_score="no_high_vulnerabilities"
        )
    
    async def penetration_test(self) -> PenTestReport:
        """Annual penetration testing (11.3)."""
        return await self.conduct_pentest(
            scope=["network", "application"],
            methodology="industry_accepted",
            frequency="annual"
        )
    
    async def monitor_changes(self):
        """File integrity monitoring (11.5)."""
        return FileIntegrityMonitor(
            critical_files=[
                "/etc/passwd",
                "/etc/shadow",
                "/var/log/audit/*",
                "application_binaries"
            ],
            alert_on_change=True,
            weekly_comparison=True
        )
```

### Maintain Security Policy

#### Requirement 12: Security Policies

```yaml
security_policy:
  documentation:
    - information_security_policy: true
    - acceptable_use_policy: true
    - incident_response_plan: true
    - vendor_management_policy: true
  
  reviews:
    - policy_review: annual
    - risk_assessment: annual
  
  training:
    - security_awareness: annual
    - role_specific_training: as_needed
```

## Common Gaps

### 1. Storing Prohibited Data

**Issue:** CVV/CVC stored after authorization.

**Solution:**

```python
async def process_payment(card: CardData) -> PaymentResult:
    """Process payment without storing prohibited data."""
    result = await payment_gateway.authorize(card)
    
    # Only store allowed data
    await store_transaction(
        token=result.token,  # Use tokenized PAN
        last_four=card.pan[-4:],
        exp_month=card.exp_month,
        exp_year=card.exp_year
        # NEVER: full_pan, cvv, track_data
    )
    
    return result
```

### 2. Inadequate Segmentation

**Issue:** CDE not properly isolated from other networks.

**Solution:** ComplianceAgent validates network segmentation:

```yaml
# Network segmentation validation
segmentation_test:
  cde_networks:
    - 10.10.1.0/24
  non_cde_networks:
    - 10.10.2.0/24
    - 10.10.3.0/24
  
  validation:
    - no_direct_routes: true
    - firewall_between: true
    - scope_reduction_confirmed: true
```

## Configuration

```yaml
# .complianceagent/config.yml
frameworks:
  pci_dss:
    enabled: true
    version: "4.0"
    
    # Your compliance level
    level: 2
    
    # SAQ type (if applicable)
    saq_type: "SAQ-D"
    
    # CDE scope
    cde:
      stores_pan: true
      processes_pan: true
      transmits_pan: true
```

## Templates

| Template | Description |
|----------|-------------|
| `pci-secure-coding` | Secure SDLC templates |
| `pci-logging` | Audit logging configuration |
| `pci-access-control` | Role-based access matrix |
| `pci-encryption` | Data protection implementation |

---

See also: [SOC 2](./soc2) | [HIPAA](./hipaa) | [Frameworks Overview](./overview)
