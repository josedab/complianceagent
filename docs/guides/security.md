# Security Best Practices Guide

This guide covers security best practices for developing, deploying, and operating ComplianceAgent.

## Security Principles

| Principle | Description |
|-----------|-------------|
| **Defense in Depth** | Multiple layers of security controls |
| **Least Privilege** | Minimum necessary permissions |
| **Secure by Default** | Security enabled out of the box |
| **Fail Securely** | Errors should not expose vulnerabilities |
| **Zero Trust** | Verify everything, trust nothing |

---

## Authentication & Authorization

### Password Security

```python
# ✅ DO: Use strong password hashing
from passlib.hash import argon2

def hash_password(password: str) -> str:
    return argon2.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return argon2.verify(password, hash)

# ❌ DON'T: Use weak hashing algorithms
import hashlib
def bad_hash(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()  # NEVER DO THIS
```

### Password Requirements

```python
# Enforce strong passwords
PASSWORD_REQUIREMENTS = {
    "min_length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "forbidden_patterns": ["password", "123456", "qwerty"],
    "check_breached": True,  # Check against HaveIBeenPwned
}
```

### JWT Token Security

```python
# ✅ DO: Secure JWT configuration
from datetime import datetime, timedelta
import jwt

JWT_CONFIG = {
    "algorithm": "RS256",  # Use asymmetric keys
    "access_token_expire": timedelta(minutes=15),
    "refresh_token_expire": timedelta(days=7),
    "issuer": "complianceagent",
    "audience": "complianceagent-api",
}

def create_access_token(user_id: str) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + JWT_CONFIG["access_token_expire"],
            "iss": JWT_CONFIG["issuer"],
            "aud": JWT_CONFIG["audience"],
        },
        private_key,
        algorithm=JWT_CONFIG["algorithm"],
    )
```

### Multi-Factor Authentication

```python
# Implement MFA for sensitive operations
import pyotp

class MFAService:
    def generate_totp_secret(self) -> str:
        return pyotp.random_base32()
    
    def verify_totp(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> list[str]:
        return [secrets.token_hex(4) for _ in range(count)]
```

### Role-Based Access Control

```python
# Define granular permissions
PERMISSIONS = {
    "regulations:read": "View regulations",
    "regulations:write": "Create/update regulations",
    "regulations:delete": "Delete regulations",
    "users:read": "View user information",
    "users:admin": "Manage users",
    "audit:read": "View audit logs",
    "billing:manage": "Manage billing",
}

ROLES = {
    "viewer": ["regulations:read"],
    "analyst": ["regulations:read", "audit:read"],
    "editor": ["regulations:read", "regulations:write"],
    "admin": list(PERMISSIONS.keys()),
}

# Check permissions before actions
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if permission not in current_user.permissions:
                raise ForbiddenException(f"Missing permission: {permission}")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

---

## Data Protection

### Encryption at Rest

```python
# ✅ DO: Encrypt sensitive fields in database
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID, primary_key=True)
    name = Column(String)
    # Encrypt PII at rest
    ssn = Column(StringEncryptedType(String, get_key(), AesEngine, 'pkcs5'))
    tax_id = Column(StringEncryptedType(String, get_key(), AesEngine, 'pkcs5'))
```

### Encryption in Transit

```python
# ✅ DO: Enforce TLS 1.3
# In nginx or load balancer config:
ssl_protocols TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers on;

# In Python requests
import requests
response = requests.get(url, verify=True)  # Always verify certificates
```

### Key Management

```python
# ✅ DO: Use proper key management
import os
from cryptography.fernet import Fernet

def get_encryption_key() -> bytes:
    # Load from secure environment/vault
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY not configured")
    return key.encode()

# Key rotation support
class KeyManager:
    def __init__(self):
        self.current_key = self._load_current_key()
        self.previous_keys = self._load_previous_keys()
    
    def decrypt(self, data: bytes) -> bytes:
        # Try current key first, then previous keys
        for key in [self.current_key] + self.previous_keys:
            try:
                return Fernet(key).decrypt(data)
            except:
                continue
        raise DecryptionError("Unable to decrypt with any known key")
```

### Data Masking

```python
# Mask sensitive data in responses and logs
def mask_pii(value: str, visible_chars: int = 4) -> str:
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]

def mask_email(email: str) -> str:
    local, domain = email.split("@")
    return f"{local[0]}***@{domain}"

# Usage
masked_ssn = mask_pii("123-45-6789")  # "*****6789"
masked_email = mask_email("john.doe@example.com")  # "j***@example.com"
```

---

## Input Validation

### Validate All Input

```python
# ✅ DO: Use Pydantic for strict validation
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=12, max_length=128)
    
    @validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[\w\s\-\.]+$", v):
            raise ValueError("Invalid characters in name")
        return v.strip()
    
    @validator("password")
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain special character")
        return v
```

### Prevent SQL Injection

```python
# ✅ DO: Use parameterized queries
from sqlalchemy import select

async def get_user_by_email(email: str) -> User:
    # SQLAlchemy handles parameterization
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()

# ❌ DON'T: String concatenation in queries
async def bad_get_user(email: str) -> User:
    # NEVER DO THIS - SQL injection vulnerability
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return await db.execute(query)
```

### Prevent XSS

```python
# ✅ DO: Sanitize output
import html

def sanitize_html(content: str) -> str:
    return html.escape(content)

# In templates (Jinja2 auto-escapes by default)
# {{ user_input }}  # Auto-escaped
# {{ user_input | safe }}  # Only use for trusted content
```

### File Upload Security

```python
import magic
import hashlib

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload(file: UploadFile) -> bool:
    # Check file size
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise ValueError("File too large")
    
    # Check MIME type (don't trust Content-Type header)
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_TYPES:
        raise ValueError(f"File type not allowed: {mime_type}")
    
    # Reset file pointer
    await file.seek(0)
    return True
```

---

## Secrets Management

### Never Hardcode Secrets

```python
# ❌ DON'T: Hardcode secrets
DATABASE_URL = "postgresql://admin:supersecret@db.example.com/prod"
API_KEY = "sk_live_abc123"

# ✅ DO: Use environment variables
import os

DATABASE_URL = os.environ["DATABASE_URL"]
API_KEY = os.environ["API_KEY"]
```

### Use Secret Management Systems

```python
# Production: Use HashiCorp Vault, AWS Secrets Manager, etc.
import hvac

def get_secret(path: str) -> str:
    client = hvac.Client(url=os.environ["VAULT_ADDR"])
    client.token = os.environ["VAULT_TOKEN"]
    secret = client.secrets.kv.read_secret_version(path=path)
    return secret["data"]["data"]["value"]

# Or AWS Secrets Manager
import boto3

def get_aws_secret(secret_name: str) -> dict:
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])
```

### Rotate Secrets Regularly

```python
# Implement secret rotation
class SecretRotation:
    def __init__(self):
        self.rotation_interval = timedelta(days=90)
    
    async def rotate_api_keys(self):
        # Create new key
        new_key = secrets.token_urlsafe(32)
        
        # Update in secret manager
        await self.secret_manager.update("api_key", new_key)
        
        # Allow grace period for old key
        await self.mark_key_deprecated(old_key, grace_period=timedelta(hours=24))
        
        # Notify services to reload
        await self.notify_key_rotation()
```

---

## Logging & Monitoring

### Security Event Logging

```python
import structlog

logger = structlog.get_logger()

# Log security events
SECURITY_EVENTS = [
    "login_success",
    "login_failure",
    "logout",
    "password_change",
    "mfa_enabled",
    "mfa_disabled",
    "permission_change",
    "api_key_created",
    "api_key_revoked",
    "suspicious_activity",
]

async def log_security_event(
    event_type: str,
    user_id: str,
    details: dict,
    severity: str = "info",
):
    logger.log(
        severity,
        event_type,
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
        **details,
    )
```

### Protect Log Data

```python
# ✅ DO: Redact sensitive data from logs
from structlog import processors

def redact_sensitive_fields(logger, method_name, event_dict):
    SENSITIVE_FIELDS = ["password", "ssn", "credit_card", "api_key", "token"]
    
    for key in event_dict:
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            event_dict[key] = "[REDACTED]"
    
    return event_dict

structlog.configure(
    processors=[
        redact_sensitive_fields,
        structlog.processors.JSONRenderer(),
    ]
)
```

### Intrusion Detection

```python
# Monitor for suspicious patterns
class SecurityMonitor:
    def __init__(self):
        self.failed_logins = defaultdict(list)
        self.api_requests = defaultdict(list)
    
    async def check_brute_force(self, ip: str, user_id: str) -> bool:
        key = f"{ip}:{user_id}"
        now = datetime.utcnow()
        
        # Clean old entries
        self.failed_logins[key] = [
            t for t in self.failed_logins[key]
            if now - t < timedelta(minutes=15)
        ]
        
        # Check threshold
        if len(self.failed_logins[key]) >= 5:
            await self.alert_security_team(
                "brute_force_detected",
                {"ip": ip, "user_id": user_id}
            )
            return True
        
        return False
```

---

## API Security

### Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Configure rate limits
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",
    "sensitive": "20/minute",
}

@app.post("/api/v1/auth/login")
@limiter.limit("10/minute")
async def login(credentials: LoginRequest):
    pass

@app.get("/api/v1/regulations")
@limiter.limit("100/minute")
async def list_regulations():
    pass
```

### API Key Security

```python
# Generate secure API keys
def generate_api_key() -> tuple[str, str]:
    # Public key prefix for identification
    prefix = "ca_live_"
    # Secret portion
    secret = secrets.token_urlsafe(32)
    full_key = f"{prefix}{secret}"
    
    # Store only the hash
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    return full_key, key_hash

# Validate API keys securely
async def validate_api_key(key: str) -> Optional[APIKey]:
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    # Constant-time comparison to prevent timing attacks
    api_key = await db.api_keys.get_by_hash(key_hash)
    return api_key
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# ✅ DO: Restrict CORS in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.complianceagent.ai"],  # Specific origins
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)

# ❌ DON'T: Allow all origins in production
# allow_origins=["*"]  # NEVER in production
```

---

## Dependency Security

### Keep Dependencies Updated

```bash
# Check for vulnerabilities
pip-audit
npm audit

# Update dependencies
cd backend && uv pip install -e ".[dev]" --upgrade
npm update
```

### Pin Dependency Versions

```toml
# pyproject.toml - Pin major versions
[project]
dependencies = [
    "fastapi>=0.109.0,<0.110.0",
    "sqlalchemy>=2.0.0,<3.0.0",
    "cryptography>=41.0.0,<42.0.0",
]
```

### Automated Security Scanning

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
  schedule:
    - cron: '0 0 * * *'

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run pip-audit
        run: pip-audit --desc on
      
      - name: Run npm audit
        run: npm audit --audit-level=high
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'HIGH,CRITICAL'
```

---

## Incident Response

### Security Incident Checklist

1. **Detect**: Monitor alerts, logs, user reports
2. **Contain**: Isolate affected systems
3. **Eradicate**: Remove threat, patch vulnerabilities
4. **Recover**: Restore services safely
5. **Learn**: Post-incident review, update procedures

### Security Contacts

```python
# Security notification configuration
SECURITY_CONTACTS = {
    "critical": {
        "email": "security-emergency@company.com",
        "pagerduty": "SECURITY_SERVICE_KEY",
        "slack": "#security-incidents",
    },
    "high": {
        "email": "security@company.com",
        "slack": "#security-alerts",
    },
}
```

---

## Security Checklist

### Before Deployment

- [ ] All secrets stored in secret manager (not in code)
- [ ] TLS enabled for all connections
- [ ] Authentication required for all sensitive endpoints
- [ ] Input validation on all user input
- [ ] Output encoding to prevent XSS
- [ ] Rate limiting configured
- [ ] Security logging enabled
- [ ] Dependency vulnerabilities checked
- [ ] Security headers configured
- [ ] CORS properly restricted

### Regular Security Tasks

- [ ] Weekly: Review security logs
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security assessment
- [ ] Annually: Penetration testing
- [ ] Annually: Security training

---

## Related Documentation

- [SOC 2 Compliance](../frameworks/soc2.md)
- [ISO 27001 Compliance](../frameworks/iso27001.md)
- [Deployment Guide](../deployment/README.md)
- [Troubleshooting](troubleshooting.md)
