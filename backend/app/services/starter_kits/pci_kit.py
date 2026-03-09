"""PCI-DSS starter kit definition."""

from app.services.starter_kits.models import (
    CodeTemplate,
    ConfigTemplate,
    StarterKit,
    TemplateCategory,
    TemplateLanguage,
)


def create_pci_kit() -> StarterKit:
    """Create PCI-DSS starter kit."""
    kit = StarterKit(
        name="PCI-DSS Compliance Starter Kit",
        description="Templates for PCI-DSS compliant payment processing",
        framework="PCI_DSS",
        version="4.0.0",
        requirements_covered=[
            "Requirement 3 - Protect Stored Cardholder Data",
            "Requirement 4 - Encrypt Transmission of Cardholder Data",
            "Requirement 6 - Develop Secure Systems",
            "Requirement 8 - Identify and Authenticate Access",
            "Requirement 10 - Track and Monitor Access",
        ],
        supported_languages=[
            TemplateLanguage.PYTHON,
            TemplateLanguage.TYPESCRIPT,
        ],
        prerequisites=[
            "TLS 1.2+ support",
            "HSM or secure key storage",
            "PCI-compliant hosting environment",
        ],
        quick_start="""
1. Review PCI-DSS requirements
2. Configure encryption using HSM
3. Set up card data handling
4. Enable comprehensive logging
5. Implement tokenization
""",
    )

    kit.code_templates = [
        CodeTemplate(
            name="Card Data Tokenizer",
            description="Tokenize card data to reduce PCI scope",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.DATA_PROTECTION,
            file_name="tokenizer.py",
            content=_pci_tokenizer_template(),
            frameworks=["PCI_DSS"],
            requirement_ids=["3.4"],
        ),
        CodeTemplate(
            name="PAN Masking Utility",
            description="Mask PANs in logs and displays",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.DATA_PROTECTION,
            file_name="pan_masking.py",
            content=_pan_masking_template(),
            frameworks=["PCI_DSS"],
            requirement_ids=["3.3"],
        ),
    ]

    kit.config_templates = [
        ConfigTemplate(
            name="PCI Security Configuration",
            description="PCI-DSS security settings",
            file_name="pci_config.yaml",
            content=_pci_config_template(),
            frameworks=["PCI_DSS"],
        ),
    ]

    return kit


def _pci_tokenizer_template() -> str:
    return '''"""
PCI-DSS Card Data Tokenization

Implements Requirement 3.4 - Render PAN unreadable.
"""

import secrets
import hashlib
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TokenizedCard:
"""Tokenized card data."""
token: str
last_four: str
card_type: str
expiry_month: int
expiry_year: int
created_at: datetime


class CardTokenizer:
"""
PCI-DSS compliant card tokenization.

Replaces sensitive card data with non-sensitive tokens,
reducing PCI scope significantly.
"""

def __init__(self, token_vault):
    self.vault = token_vault

def tokenize(
    self,
    card_number: str,
    expiry_month: int,
    expiry_year: int,
    cvv: str,  # Never stored!
) -> TokenizedCard:
    """
    Tokenize card data.
    
    The actual card number is stored in a PCI-compliant vault.
    Only the token is returned for use in the application.
    """
    # Validate card number
    if not _validate_luhn(card_number):
        raise ValueError("Invalid card number")
    
    # Generate secure token
    token = _generate_token()
    
    # Store in secure vault (this is the only place actual PAN exists)
    self.vault.store(
        token=token,
        pan=card_number,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
    )
    # CVV is NEVER stored per PCI-DSS
    
    return TokenizedCard(
        token=token,
        last_four=card_number[-4:],
        card_type=_detect_card_type(card_number),
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        created_at=datetime.now(UTC),
    )

def _generate_token() -> str:
    """Generate cryptographically secure token."""
    return f"tok_{secrets.token_urlsafe(24)}"

def _validate_luhn(self, number: str) -> bool:
    """Validate card number using Luhn algorithm."""
    digits = [int(d) for d in number if d.isdigit()]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    
    return total % 10 == 0

def _detect_card_type(self, number: str) -> str:
    """Detect card type from number prefix."""
    if number.startswith("4"):
        return "visa"
    elif number.startswith(("51", "52", "53", "54", "55")):
        return "mastercard"
    elif number.startswith(("34", "37")):
        return "amex"
    elif number.startswith("6011"):
        return "discover"
    return "unknown"
'''


def _pan_masking_template() -> str:
    return '''"""
PAN Masking Utility

Implements PCI-DSS Requirement 3.3 - Mask PAN when displayed.
"""

import re
from typing import Optional


class PANMasker:
"""
Mask Primary Account Numbers for display.

PCI-DSS allows showing only first 6 and last 4 digits.
"""

@staticmethod
def mask(pan: str, show_first: int = 6, show_last: int = 4) -> str:
    """
    Mask a PAN for display.
    
    Args:
        pan: The full card number
        show_first: Digits to show at start (max 6)
        show_last: Digits to show at end (max 4)
        
    Returns:
        Masked PAN like "411111******1234"
    """
    # Remove any spaces or dashes
    pan = re.sub(r"[\\s-]", "", pan)
    
    if len(pan) < 13:
        raise ValueError("Invalid PAN length")
    
    # PCI-DSS limit
    show_first = min(show_first, 6)
    show_last = min(show_last, 4)
    
    masked_length = len(pan) - show_first - show_last
    masked = pan[:show_first] + "*" * masked_length + pan[-show_last:]
    
    return masked

@staticmethod
def mask_in_text(text: str) -> str:
    """
    Find and mask any PANs in text (e.g., logs).
    
    Prevents accidental logging of card numbers.
    """
    # Pattern for card numbers (13-19 digits, possibly with spaces/dashes)
    pattern = r"\\b(\\d[\\d\\s-]{11,22}\\d)\\b"
    
    def mask_match(match):
        potential_pan = re.sub(r"[\\s-]", "", match.group(1))
        if 13 <= len(potential_pan) <= 19:
            return PANMasker.mask(potential_pan)
        return match.group(0)
    
    return re.sub(pattern, mask_match, text)

@staticmethod
def get_last_four(pan: str) -> str:
    """Get last 4 digits of PAN (safe to store/display)."""
    pan = re.sub(r"[\\s-]", "", pan)
    return pan[-4:]
'''


def _pci_config_template() -> str:
    return """# PCI-DSS Security Configuration

pci_dss:
  version: "4.0"

  # Requirement 1: Network Security
  network:
firewall_enabled: true
dmz_configured: true
ingress_filtering: true

  # Requirement 3: Protect Stored Data
  storage:
pan_encryption: "AES-256"
key_rotation_days: 90
never_store_cvv: true
never_store_track_data: true
truncation_enabled: true

  # Requirement 4: Encrypt Transmission
  transmission:
tls_version: "1.2"
strong_ciphers_only: true
certificate_validation: true

  # Requirement 7: Restrict Access
  access:
need_to_know: true
role_based: true
unique_ids: true

  # Requirement 8: Authentication
  authentication:
mfa_required: true
password_length: 12
password_complexity: true
account_lockout: 6

  # Requirement 10: Logging
  logging:
log_all_access: true
log_admin_actions: true
time_sync: true
retention_days: 365
tamper_protection: true

  # Tokenization settings
  tokenization:
enabled: true
vault_provider: "{{ vault_provider }}"
"""
