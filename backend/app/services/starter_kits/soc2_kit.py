"""SOC2 starter kit definition."""

from app.services.starter_kits.gdpr_kit import _audit_logger_template
from app.services.starter_kits.models import (
    CodeTemplate,
    ConfigTemplate,
    DocumentTemplate,
    StarterKit,
    TemplateCategory,
    TemplateLanguage,
)


def create_soc2_kit() -> StarterKit:
    """Create SOC2 starter kit."""
    kit = StarterKit(
        name="SOC2 Compliance Starter Kit",
        description="Templates for SOC2 Type II compliance",
        framework="SOC2",
        version="1.0.0",
        requirements_covered=[
            "CC6.1 - Logical Access Security",
            "CC6.6 - Access Authentication",
            "CC6.7 - Data Encryption",
            "CC7.1 - Vulnerability Management",
            "CC8.1 - Change Management",
        ],
        supported_languages=[
            TemplateLanguage.PYTHON,
            TemplateLanguage.TYPESCRIPT,
            TemplateLanguage.GO,
        ],
        prerequisites=[
            "Git for version control",
            "CI/CD pipeline",
            "Logging infrastructure",
        ],
        quick_start="""
1. Set up authentication module
2. Configure audit logging
3. Implement change management
4. Enable vulnerability scanning
""",
    )

    kit.code_templates = [
        CodeTemplate(
            name="MFA Authentication",
            description="Multi-factor authentication implementation",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.AUTHENTICATION,
            file_name="mfa_auth.py",
            content=_soc2_mfa_template(),
            frameworks=["SOC2"],
            requirement_ids=["CC6.6"],
        ),
        CodeTemplate(
            name="Comprehensive Audit Logger",
            description="Full audit trail implementation",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.AUDIT,
            file_name="soc2_audit.py",
            content=_audit_logger_template(),
            frameworks=["SOC2"],
            requirement_ids=["CC6.1"],
        ),
    ]

    return kit


def _soc2_mfa_template() -> str:
    return '''"""
Multi-Factor Authentication Implementation

Implements SOC2 CC6.6 - Access Authentication.
"""

import secrets
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class MFAMethod(str, Enum):
"""Supported MFA methods."""
TOTP = "totp"  # Time-based One-Time Password
SMS = "sms"
EMAIL = "email"
PUSH = "push"
HARDWARE_KEY = "hardware_key"


@dataclass
class MFAChallenge:
"""MFA verification challenge."""
challenge_id: str
user_id: str
method: MFAMethod
code: Optional[str]
created_at: float
expires_at: float
verified: bool = False


class MFAService:
"""
Multi-factor authentication service.

SOC2 Requirements:
- CC6.6: User authentication
- CC6.1: Logical access security
"""

def __init__(self, sms_provider=None, email_provider=None):
    self.sms = sms_provider
    self.email = email_provider
    _challenges: dict[str, MFAChallenge] = {}
    _secrets: dict[str, str] = {}  # User TOTP secrets

def setup_totp(self, user_id: str) -> str:
    """
    Set up TOTP for a user.
    
    Returns the secret for QR code generation.
    """
    secret = secrets.token_hex(20)
    _secrets[user_id] = secret
    return secret

def generate_totp(self, secret: str, timestamp: Optional[int] = None) -> str:
    """Generate TOTP code."""
    if timestamp is None:
        timestamp = int(time.time())
    
    counter = timestamp // 30
    
    # HMAC-SHA1 based OTP
    key = bytes.fromhex(secret)
    counter_bytes = counter.to_bytes(8, byteorder="big")
    
    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    code = ((hmac_hash[offset] & 0x7F) << 24 |
            (hmac_hash[offset + 1] & 0xFF) << 16 |
            (hmac_hash[offset + 2] & 0xFF) << 8 |
            (hmac_hash[offset + 3] & 0xFF))
    
    return str(code % 1000000).zfill(6)

async def initiate_challenge(
    self,
    user_id: str,
    method: MFAMethod,
    destination: Optional[str] = None,
) -> MFAChallenge:
    """Initiate an MFA challenge."""
    challenge_id = secrets.token_urlsafe(32)
    code = None
    
    if method == MFAMethod.SMS:
        code = str(secrets.randbelow(1000000)).zfill(6)
        if self.sms and destination:
            await self.sms.send(destination, f"Your verification code: {code}")
    
    elif method == MFAMethod.EMAIL:
        code = str(secrets.randbelow(1000000)).zfill(6)
        if self.email and destination:
            await self.email.send(destination, "Verification Code", f"Your code: {code}")
    
    elif method == MFAMethod.TOTP:
        # TOTP is verified against user's secret
        pass
    
    challenge = MFAChallenge(
        challenge_id=challenge_id,
        user_id=user_id,
        method=method,
        code=code,  # Stored hashed in production
        created_at=time.time(),
        expires_at=time.time() + 300,  # 5 minutes
    )
    
    _challenges[challenge_id] = challenge
    return challenge

async def verify_challenge(
    self,
    challenge_id: str,
    code: str,
) -> bool:
    """Verify an MFA challenge."""
    challenge = _challenges.get(challenge_id)
    
    if not challenge:
        return False
    
    if time.time() > challenge.expires_at:
        return False
    
    if challenge.verified:
        return False  # Already used
    
    if challenge.method == MFAMethod.TOTP:
        secret = _secrets.get(challenge.user_id)
        if not secret:
            return False
        
        # Check current and previous time windows
        for offset in [0, -1, 1]:
            expected = self.generate_totp(secret, int(time.time()) + offset * 30)
            if secrets.compare_digest(code, expected):
                challenge.verified = True
                return True
        return False
    
    else:
        # SMS/Email code verification
        if challenge.code and secrets.compare_digest(code, challenge.code):
            challenge.verified = True
            return True
    
    return False
'''
