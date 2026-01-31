"""GDPR/Privacy consent templates."""

from app.services.templates.base import (
    ComplianceTemplate,
    TemplateCategory,
    TemplateParameter,
)


GDPR_CONSENT_TEMPLATE = ComplianceTemplate(
    name="GDPR Consent Manager",
    description="Complete consent collection and management module with granular consent tracking",
    category=TemplateCategory.CONSENT,
    regulations=["GDPR", "CCPA"],
    languages=["python", "typescript"],
    code={
        "python": '''"""GDPR-compliant consent management module.

Implements consent collection, storage, and verification per GDPR Article 7.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ConsentPurpose(str, Enum):
    """Purposes for which consent can be collected."""
    
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PERSONALIZATION = "personalization"
    THIRD_PARTY_SHARING = "third_party_sharing"
    ESSENTIAL = "essential"  # Does not require consent


@dataclass
class ConsentRecord:
    """Record of user consent per GDPR Article 7."""
    
    id: UUID
    user_id: str
    purpose: ConsentPurpose
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: str
    user_agent: str
    consent_text_version: str
    
    @property
    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        return self.granted and self.revoked_at is None


class ConsentManager:
    """Manages user consent records.
    
    GDPR Article 7 Compliance:
    - Consent must be freely given, specific, informed, and unambiguous
    - Data subject can withdraw consent at any time
    - Withdrawal must be as easy as giving consent
    - Must keep records of consent
    """
    
    def __init__(self, storage):
        self.storage = storage
    
    async def record_consent(
        self,
        user_id: str,
        purpose: ConsentPurpose,
        granted: bool,
        ip_address: str,
        user_agent: str,
        consent_text_version: str,
    ) -> ConsentRecord:
        """Record a consent decision."""
        record = ConsentRecord(
            id=uuid4(),
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            granted_at=datetime.now(UTC) if granted else None,
            revoked_at=None,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text_version=consent_text_version,
        )
        
        await self.storage.save_consent(record)
        return record
    
    async def check_consent(
        self,
        user_id: str,
        purpose: ConsentPurpose,
    ) -> bool:
        """Check if user has valid consent for a purpose."""
        if purpose == ConsentPurpose.ESSENTIAL:
            return True
        
        record = await self.storage.get_latest_consent(user_id, purpose)
        return record is not None and record.is_valid
    
    async def revoke_consent(
        self,
        user_id: str,
        purpose: ConsentPurpose,
    ) -> bool:
        """Revoke consent for a purpose."""
        record = await self.storage.get_latest_consent(user_id, purpose)
        if record and record.is_valid:
            record.revoked_at = datetime.now(UTC)
            await self.storage.update_consent(record)
            return True
        return False
    
    async def get_consent_status(
        self,
        user_id: str,
    ) -> dict[ConsentPurpose, bool]:
        """Get all consent statuses for a user."""
        statuses = {}
        for purpose in ConsentPurpose:
            statuses[purpose] = await self.check_consent(user_id, purpose)
        return statuses
''',
        "typescript": '''/**
 * GDPR-compliant consent management module.
 * Implements consent collection per GDPR Article 7.
 */

export enum ConsentPurpose {
  MARKETING = 'marketing',
  ANALYTICS = 'analytics',
  PERSONALIZATION = 'personalization',
  THIRD_PARTY_SHARING = 'third_party_sharing',
  ESSENTIAL = 'essential',
}

export interface ConsentRecord {
  id: string;
  userId: string;
  purpose: ConsentPurpose;
  granted: boolean;
  grantedAt: Date | null;
  revokedAt: Date | null;
  ipAddress: string;
  userAgent: string;
  consentTextVersion: string;
}

export class ConsentManager {
  constructor(private storage: ConsentStorage) {}

  async recordConsent(params: {
    userId: string;
    purpose: ConsentPurpose;
    granted: boolean;
    ipAddress: string;
    userAgent: string;
    consentTextVersion: string;
  }): Promise<ConsentRecord> {
    const record: ConsentRecord = {
      id: crypto.randomUUID(),
      userId: params.userId,
      purpose: params.purpose,
      granted: params.granted,
      grantedAt: params.granted ? new Date() : null,
      revokedAt: null,
      ipAddress: params.ipAddress,
      userAgent: params.userAgent,
      consentTextVersion: params.consentTextVersion,
    };

    await this.storage.saveConsent(record);
    return record;
  }

  async checkConsent(userId: string, purpose: ConsentPurpose): Promise<boolean> {
    if (purpose === ConsentPurpose.ESSENTIAL) {
      return true;
    }
    const record = await this.storage.getLatestConsent(userId, purpose);
    return record !== null && record.granted && !record.revokedAt;
  }

  async revokeConsent(userId: string, purpose: ConsentPurpose): Promise<boolean> {
    const record = await this.storage.getLatestConsent(userId, purpose);
    if (record && record.granted && !record.revokedAt) {
      record.revokedAt = new Date();
      await this.storage.updateConsent(record);
      return true;
    }
    return false;
  }
}
''',
    },
    tests={
        "python": '''"""Tests for GDPR consent manager."""

import pytest
from unittest.mock import AsyncMock
from consent_manager import ConsentManager, ConsentPurpose


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.get_latest_consent.return_value = None
    return storage


@pytest.fixture
def consent_manager(mock_storage):
    return ConsentManager(mock_storage)


@pytest.mark.asyncio
async def test_record_consent(consent_manager, mock_storage):
    result = await consent_manager.record_consent(
        user_id="user123",
        purpose=ConsentPurpose.MARKETING,
        granted=True,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        consent_text_version="v1.0",
    )
    
    assert result.granted is True
    assert result.user_id == "user123"
    mock_storage.save_consent.assert_called_once()


@pytest.mark.asyncio
async def test_essential_consent_always_true(consent_manager):
    result = await consent_manager.check_consent(
        user_id="user123",
        purpose=ConsentPurpose.ESSENTIAL,
    )
    assert result is True
''',
    },
    documentation="""# GDPR Consent Manager

## Overview
GDPR-compliant consent management functionality.

## Compliance
- **Article 7(1)**: Records when consent was given
- **Article 7(2)**: Tracks consent text version shown to user
- **Article 7(3)**: Supports easy consent withdrawal
- **Article 7(4)**: Separates consent by purpose
""",
    parameters=[
        TemplateParameter(
            name="storage_backend",
            description="Storage backend for consent records",
            type="string",
            default="database",
        ),
        TemplateParameter(
            name="custom_purposes",
            description="Additional consent purposes to support",
            type="array",
            required=False,
        ),
    ],
    tags=["gdpr", "consent", "privacy", "article-7"],
)


CONSENT_TEMPLATES = [GDPR_CONSENT_TEMPLATE]
