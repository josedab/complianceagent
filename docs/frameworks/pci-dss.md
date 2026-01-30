# PCI-DSS Compliance Guide

This guide covers how ComplianceAgent helps you achieve compliance with the Payment Card Industry Data Security Standard (PCI-DSS).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Payment Card Industry Data Security Standard |
| **Version** | 4.0 (Effective March 2024) |
| **Jurisdiction** | Global (Card Brands) |
| **Enforcing Authority** | PCI Security Standards Council |
| **Penalty** | $5,000 - $100,000/month; card processing revocation |

### Applicability

Applies to all entities that:
- Store cardholder data
- Process payment card transactions
- Transmit cardholder data

### Compliance Levels

| Level | Criteria | Validation |
|-------|----------|------------|
| 1 | >6M transactions/year | Annual on-site audit |
| 2 | 1-6M transactions/year | Annual SAQ |
| 3 | 20K-1M e-commerce transactions | Annual SAQ |
| 4 | <20K e-commerce transactions | Annual SAQ |

## PCI-DSS v4.0 Requirements

### 12 High-Level Requirements

| # | Requirement | Code Impact |
|---|-------------|-------------|
| 1 | Install and maintain network security controls | Firewall config, network segmentation |
| 2 | Apply secure configurations | Hardening, no defaults |
| 3 | Protect stored account data | Encryption, masking, tokenization |
| 4 | Protect cardholder data during transmission | TLS 1.2+, encryption |
| 5 | Protect systems from malicious software | Antimalware, input validation |
| 6 | Develop secure systems and software | Secure SDLC, code review |
| 7 | Restrict access to cardholder data | RBAC, least privilege |
| 8 | Identify users and authenticate access | MFA, strong passwords |
| 9 | Restrict physical access | Physical security (N/A for code) |
| 10 | Log and monitor access | Audit trails, alerting |
| 11 | Test security regularly | Pen testing, vulnerability scans |
| 12 | Support information security with policies | Documentation, training |

## ComplianceAgent Detection

### Automatically Detected Issues

```
PCI-001: Cardholder data stored unencrypted
PCI-002: Full PAN displayed without masking
PCI-003: CVV/CVC stored (prohibited)
PCI-004: Weak encryption algorithm (< AES-256)
PCI-005: Sensitive data in logs
PCI-006: Missing TLS for card transmission
PCI-007: Hardcoded credentials
PCI-008: Insufficient input validation
PCI-009: Missing access controls
PCI-010: Inadequate session management
PCI-011: No audit logging for card access
PCI-012: SQL injection vulnerability
```

### Example Detection

**Issue: PCI-003 - CVV stored in database**

```python
# ❌ Non-compliant: Storing CVV (strictly prohibited)
class PaymentCard(Base):
    __tablename__ = "payment_cards"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    card_number = Column(String)  # Full PAN stored unencrypted!
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    cvv = Column(String)  # CVV MUST NEVER BE STORED
    cardholder_name = Column(String)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Tokenization with PCI-compliant vault
from payment_vault import TokenVault

class PaymentMethod(Base):
    """
    PCI-DSS Req 3.2: Do not store sensitive authentication data.
    PCI-DSS Req 3.4: Render PAN unreadable anywhere it is stored.
    """
    __tablename__ = "payment_methods"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    
    # Store only token reference (actual card in PCI-compliant vault)
    vault_token = Column(String, nullable=False)
    
    # Masked PAN for display (first 6, last 4)
    masked_pan = Column(String(16))  # e.g., "411111******1111"
    
    # Non-sensitive metadata
    card_brand = Column(String)  # visa, mastercard
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    
    # CVV is NEVER stored - only used for single transaction
    # cardholder_name can be stored if encrypted

async def store_card(
    user_id: str,
    card_number: str,
    expiry_month: int,
    expiry_year: int,
    cvv: str  # Used once, never stored
):
    """
    Store card securely using tokenization.
    Actual card data stored in PCI-compliant vault.
    """
    # Validate card
    if not validate_luhn(card_number):
        raise ValueError("Invalid card number")
    
    # Send to PCI-compliant vault for tokenization
    vault = TokenVault(api_key=settings.VAULT_API_KEY)
    token = await vault.tokenize(
        card_number=card_number,
        expiry_month=expiry_month,
        expiry_year=expiry_year
        # CVV passed to processor, NEVER to vault
    )
    
    # Store only token and masked PAN
    payment_method = PaymentMethod(
        user_id=user_id,
        vault_token=token.id,
        masked_pan=mask_pan(card_number),  # "411111******1111"
        card_brand=detect_brand(card_number),
        expiry_month=expiry_month,
        expiry_year=expiry_year
    )
    
    db.add(payment_method)
    await db.commit()
    
    # Log access (without sensitive data)
    audit_log.record(
        action="card_tokenized",
        user_id=user_id,
        card_brand=payment_method.card_brand,
        masked_pan=payment_method.masked_pan
    )
    
    return payment_method

def mask_pan(card_number: str) -> str:
    """PCI-DSS Req 3.4: Display at most first 6 and last 4 digits."""
    return f"{card_number[:6]}******{card_number[-4:]}"
```

## Implementation Patterns

### Requirement 3: Protect Stored Data

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class PCIDataEncryption:
    """
    PCI-DSS Req 3.5: Use strong cryptography to protect stored data.
    AES-256-GCM for authenticated encryption.
    """
    
    def __init__(self, key: bytes):
        if len(key) != 32:  # 256 bits
            raise ValueError("Key must be 256 bits")
        self.cipher = AESGCM(key)
    
    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt with authenticated encryption."""
        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = self.cipher.encrypt(
            nonce,
            plaintext.encode(),
            associated_data=None
        )
        return nonce + ciphertext
    
    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt and verify integrity."""
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        plaintext = self.cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

# Key management (PCI-DSS Req 3.6)
class KeyManager:
    """
    PCI-DSS Req 3.6: Document and implement key management procedures.
    """
    
    def __init__(self):
        # Use HSM or KMS in production
        self.kms = AWSKeyManagementService()
    
    async def get_current_key(self) -> bytes:
        """Get current encryption key from secure storage."""
        return await self.kms.get_key(
            key_id=settings.PCI_KEY_ID,
            context={"purpose": "cardholder_data"}
        )
    
    async def rotate_key(self):
        """
        PCI-DSS Req 3.6.4: Key rotation at end of cryptoperiod.
        """
        new_key = await self.kms.create_key()
        await self.re_encrypt_all_data(new_key)
        await self.kms.schedule_key_deletion(settings.PCI_KEY_ID)
        return new_key
```

### Requirement 4: Protect Data in Transit

```python
import ssl
import httpx

class PCISecureTransport:
    """
    PCI-DSS Req 4.1: Use strong cryptography and security protocols.
    """
    
    @staticmethod
    def create_ssl_context() -> ssl.SSLContext:
        """Create TLS 1.2+ context with strong ciphers."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        # PCI-DSS 4.0 requires TLS 1.2 minimum
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Strong cipher suites only
        context.set_ciphers(
            "ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20"
        )
        
        # Verify certificates
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        
        return context
    
    @staticmethod
    async def post_to_processor(endpoint: str, data: dict) -> dict:
        """Send payment data with PCI-compliant transport."""
        async with httpx.AsyncClient(
            verify=True,  # Certificate validation
            http2=True,   # HTTP/2 preferred
            timeout=30.0
        ) as client:
            response = await client.post(
                endpoint,
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": settings.PROCESSOR_API_KEY
                }
            )
            return response.json()
```

### Requirement 8: Strong Authentication

```python
from passlib.context import CryptContext
import pyotp

# PCI-DSS Req 8.3.1: Password complexity
PASSWORD_POLICY = {
    "min_length": 12,  # v4.0 increased from 7
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "history": 4,  # Cannot reuse last 4 passwords
    "max_age_days": 90
}

pwd_context = CryptContext(
    schemes=["argon2"],  # Strong hashing
    deprecated="auto"
)

def validate_password(password: str) -> bool:
    """PCI-DSS Req 8.3: Password requirements."""
    if len(password) < PASSWORD_POLICY["min_length"]:
        return False
    if PASSWORD_POLICY["require_uppercase"] and not any(c.isupper() for c in password):
        return False
    if PASSWORD_POLICY["require_lowercase"] and not any(c.islower() for c in password):
        return False
    if PASSWORD_POLICY["require_digit"] and not any(c.isdigit() for c in password):
        return False
    if PASSWORD_POLICY["require_special"] and not any(c in "!@#$%^&*" for c in password):
        return False
    return True

class MFAManager:
    """
    PCI-DSS Req 8.4: MFA for all access to cardholder data environment.
    """
    
    @staticmethod
    def generate_totp_secret() -> str:
        """Generate TOTP secret for user."""
        return pyotp.random_base32()
    
    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

@app.post("/api/auth/login")
async def login(credentials: LoginCredentials):
    """
    PCI-DSS Req 8.2.1: Unique ID for each user.
    PCI-DSS Req 8.4: MFA required for CDE access.
    """
    user = await authenticate_user(credentials.email, credentials.password)
    
    if not user:
        # PCI-DSS Req 8.2.4: Account lockout after failed attempts
        await record_failed_attempt(credentials.email)
        failed_attempts = await get_failed_attempts(credentials.email)
        
        if failed_attempts >= 6:  # v4.0: after 10 attempts max
            await lock_account(credentials.email, duration_minutes=30)
        
        raise HTTPException(401, "Invalid credentials")
    
    # Require MFA for CDE access
    if not credentials.mfa_code:
        return {"status": "mfa_required"}
    
    if not MFAManager.verify_totp(user.mfa_secret, credentials.mfa_code):
        raise HTTPException(401, "Invalid MFA code")
    
    # Generate session with limited lifetime
    session = create_session(
        user_id=user.id,
        max_idle_minutes=15  # PCI-DSS Req 8.2.8
    )
    
    return {"access_token": session.token}
```

### Requirement 10: Logging and Monitoring

```python
from datetime import datetime
from enum import Enum

class PCIAuditEvent(Enum):
    """PCI-DSS Req 10.2: Auditable events."""
    USER_ACCESS = "user_access"
    INVALID_ACCESS = "invalid_access_attempt"
    ADMIN_ACTION = "admin_action"
    AUDIT_LOG_ACCESS = "audit_log_access"
    AUTH_MECHANISM_USE = "auth_mechanism"
    AUDIT_LOG_INIT = "audit_initialization"
    OBJECT_CREATE_DELETE = "object_creation_deletion"

class PCIAuditLog(Base):
    """
    PCI-DSS Req 10.3: Record audit trail entries.
    """
    __tablename__ = "pci_audit_log"
    
    id = Column(UUID, primary_key=True)
    
    # Req 10.3.1: User identification
    user_id = Column(String, nullable=False)
    
    # Req 10.3.2: Type of event
    event_type = Column(String, nullable=False)
    
    # Req 10.3.3: Date and time
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Req 10.3.4: Success or failure
    success = Column(Boolean, nullable=False)
    
    # Req 10.3.5: Origination of event
    origination = Column(String)  # Component/service
    
    # Req 10.3.6: Identity or name of affected data/resource
    resource_type = Column(String)
    resource_id = Column(String)
    
    # Additional context
    ip_address = Column(String)
    details = Column(JSON)
    
    # Tamper protection
    hash = Column(String, nullable=False)

# Req 10.4: Time synchronization
async def log_pci_event(
    event_type: PCIAuditEvent,
    user_id: str,
    success: bool,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None
):
    """Log PCI-DSS auditable event."""
    entry = PCIAuditLog(
        user_id=user_id,
        event_type=event_type.value,
        timestamp=datetime.utcnow(),  # NTP-synchronized
        success=success,
        origination=settings.SERVICE_NAME,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=get_client_ip(),
        details=details
    )
    
    # Calculate hash for tamper detection
    entry.hash = calculate_entry_hash(entry)
    
    db.add(entry)
    await db.commit()

# Req 10.5: Secure audit trails
# Logs retained for at least 1 year, 3 months immediately available
```

## Configuration

```bash
# .env
COMPLIANCE_FRAMEWORKS=pci-dss
PCI_LEVEL=1  # 1-4
PCI_KEY_ID=aws-kms-key-id
PCI_VAULT_ENDPOINT=https://vault.example.com
PCI_LOG_RETENTION_DAYS=365
PCI_AUDIT_IMMEDIATE_DAYS=90
```

## CI/CD Integration

```yaml
- name: PCI-DSS Compliance Check
  uses: complianceagent/compliance-action@v1
  with:
    frameworks: pci-dss
    fail-on: critical
    pci-check-encryption: true
    pci-check-no-pan-storage: true
    pci-check-no-cvv-storage: true
    pci-check-audit-logging: true
```

## Resources

- [PCI SSC Document Library](https://www.pcisecuritystandards.org/document_library)
- [PCI-DSS v4.0 Quick Reference](https://www.pcisecuritystandards.org/documents/PCI_DSS_QRG_v4-0.pdf)
- [SAQ Forms](https://www.pcisecuritystandards.org/document_library?category=saqs)

## Related Frameworks

- [SOC 2](soc2.md) - Complementary security controls
- [ISO 27001](iso27001.md) - Information security management
