"""PCI-DSS tokenization templates."""

from app.services.templates.base import (
    ComplianceTemplate,
    TemplateCategory,
)


PCI_TOKENIZATION_TEMPLATE = ComplianceTemplate(
    name="PCI-DSS Tokenization",
    description="Payment card data tokenization for PCI-DSS compliance",
    category=TemplateCategory.PCI_TOKENIZATION,
    regulations=["PCI-DSS"],
    languages=["python"],
    code={
        "python": '''"""PCI-DSS compliant tokenization for payment card data.

Implements tokenization per PCI-DSS v4.0 requirements.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional


@dataclass
class TokenizedCard:
    """A tokenized payment card."""
    
    token: str
    last_four: str
    card_type: str
    expiry_month: int
    expiry_year: int
    created_at: datetime


class CardTokenizer:
    """PCI-DSS compliant card tokenizer.
    
    PCI-DSS Compliance:
    - Requirement 3.4: Render PAN unreadable
    - Requirement 3.5: Protect cryptographic keys
    - Requirement 3.6: Key management procedures
    """
    
    def __init__(self, encryption_key: bytes, vault_storage):
        self.encryption_key = encryption_key
        self.vault = vault_storage
    
    def tokenize(self, pan: str, expiry_month: int, expiry_year: int) -> TokenizedCard:
        """Tokenize a payment card number."""
        if not self._validate_luhn(pan):
            raise ValueError("Invalid card number")
        
        token = secrets.token_urlsafe(32)
        last_four = pan[-4:]
        card_type = self._detect_card_type(pan)
        
        encrypted_pan = self._encrypt(pan)
        self.vault.store(token, encrypted_pan)
        
        return TokenizedCard(
            token=token,
            last_four=last_four,
            card_type=card_type,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            created_at=datetime.now(UTC),
        )
    
    def detokenize(self, token: str) -> Optional[str]:
        """Retrieve original PAN from token."""
        encrypted = self.vault.retrieve(token)
        if encrypted:
            return self._decrypt(encrypted)
        return None
    
    def _encrypt(self, data: str) -> bytes:
        """Encrypt data using AES-256-GCM."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(self.encryption_key)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        return nonce + ciphertext
    
    def _decrypt(self, encrypted: bytes) -> str:
        """Decrypt data."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        aesgcm = AESGCM(self.encryption_key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()
    
    def _validate_luhn(self, pan: str) -> bool:
        """Validate card number using Luhn algorithm."""
        digits = [int(d) for d in pan if d.isdigit()]
        if len(digits) < 13:
            return False
        
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        
        return checksum % 10 == 0
    
    def _detect_card_type(self, pan: str) -> str:
        """Detect card type from PAN prefix."""
        if pan.startswith("4"):
            return "visa"
        elif pan.startswith(("51", "52", "53", "54", "55")):
            return "mastercard"
        elif pan.startswith(("34", "37")):
            return "amex"
        elif pan.startswith("6011"):
            return "discover"
        return "unknown"
''',
    },
    documentation="""# PCI-DSS Tokenization

## Overview
Secure tokenization of payment card data for PCI-DSS compliance.

## Compliance
- PCI-DSS Requirement 3.4: PAN rendered unreadable
- PCI-DSS Requirement 3.5: Key protection
- PCI-DSS Requirement 3.6: Key management
""",
    parameters=[],
    tags=["pci-dss", "tokenization", "payment", "encryption"],
)


PCI_TEMPLATES = [PCI_TOKENIZATION_TEMPLATE]
