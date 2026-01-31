"""Data access and DSAR templates."""

from app.services.templates.base import (
    ComplianceTemplate,
    TemplateCategory,
)


DSAR_TEMPLATE = ComplianceTemplate(
    name="Data Subject Access Request Handler",
    description="Handle GDPR/CCPA data subject access requests with automated data collection",
    category=TemplateCategory.DATA_ACCESS,
    regulations=["GDPR", "CCPA"],
    languages=["python"],
    code={
        "python": '''"""Data Subject Access Request (DSAR) handler.

Implements GDPR Article 15 and CCPA Section 1798.100 requirements.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class DSARStatus(str, Enum):
    """Status of a data subject access request."""
    
    RECEIVED = "received"
    IDENTITY_VERIFICATION = "identity_verification"
    PROCESSING = "processing"
    REVIEW = "review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXTENDED = "extended"


class DSARType(str, Enum):
    """Types of data subject requests."""
    
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"


@dataclass
class DSARRequest:
    """A data subject access request."""
    
    id: UUID = field(default_factory=uuid4)
    request_type: DSARType = DSARType.ACCESS
    subject_email: str = ""
    subject_id: str = ""
    status: DSARStatus = DSARStatus.RECEIVED
    received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deadline: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(days=30))
    completed_at: Optional[datetime] = None
    data_collected: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    verification_method: Optional[str] = None
    verified_at: Optional[datetime] = None


class DSARHandler:
    """Handler for Data Subject Access Requests.
    
    GDPR Compliance (Article 15):
    - Response within 1 month (extendable by 2 months)
    - Must verify identity
    - Must provide data in accessible format
    
    CCPA Compliance (Section 1798.100):
    - Response within 45 days (extendable by 45 days)
    """
    
    GDPR_DEADLINE_DAYS = 30
    CCPA_DEADLINE_DAYS = 45
    
    def __init__(self, data_collectors: list, storage, notifier):
        self.data_collectors = data_collectors
        self.storage = storage
        self.notifier = notifier
    
    async def submit_request(
        self,
        request_type: DSARType,
        subject_email: str,
        subject_id: Optional[str] = None,
        regulation: str = "GDPR",
    ) -> DSARRequest:
        """Submit a new DSAR."""
        deadline_days = (
            self.CCPA_DEADLINE_DAYS if regulation == "CCPA"
            else self.GDPR_DEADLINE_DAYS
        )
        
        request = DSARRequest(
            request_type=request_type,
            subject_email=subject_email,
            subject_id=subject_id or "",
            deadline=datetime.now(UTC) + timedelta(days=deadline_days),
        )
        
        await self.storage.save_request(request)
        await self.notifier.notify_dsar_received(request)
        
        return request
    
    async def verify_identity(
        self,
        request_id: UUID,
        verification_method: str,
        verified: bool,
    ) -> DSARRequest:
        """Verify the identity of the requester."""
        request = await self.storage.get_request(request_id)
        
        if verified:
            request.status = DSARStatus.PROCESSING
            request.verification_method = verification_method
            request.verified_at = datetime.now(UTC)
        else:
            request.status = DSARStatus.REJECTED
            request.notes.append(f"Identity verification failed: {verification_method}")
        
        await self.storage.update_request(request)
        return request
    
    async def collect_data(self, request_id: UUID) -> DSARRequest:
        """Collect all data for the subject."""
        request = await self.storage.get_request(request_id)
        
        if request.status != DSARStatus.PROCESSING:
            raise ValueError("Request not in processing state")
        
        collected_data = {}
        
        for collector in self.data_collectors:
            try:
                data = await collector.collect(
                    subject_id=request.subject_id,
                    subject_email=request.subject_email,
                )
                collected_data[collector.name] = data
            except Exception as e:
                request.notes.append(f"Collection error from {collector.name}: {e}")
        
        request.data_collected = collected_data
        request.status = DSARStatus.REVIEW
        
        await self.storage.update_request(request)
        return request
    
    async def complete_request(
        self,
        request_id: UUID,
        response_format: str = "json",
    ) -> tuple[DSARRequest, bytes]:
        """Complete the request and generate response."""
        request = await self.storage.get_request(request_id)
        
        if request.status != DSARStatus.REVIEW:
            raise ValueError("Request not ready for completion")
        
        if response_format == "json":
            import json
            response_data = json.dumps(request.data_collected, indent=2).encode()
        elif response_format == "csv":
            response_data = self._to_csv(request.data_collected)
        else:
            raise ValueError(f"Unsupported format: {response_format}")
        
        request.status = DSARStatus.COMPLETED
        request.completed_at = datetime.now(UTC)
        
        await self.storage.update_request(request)
        await self.notifier.notify_dsar_completed(request)
        
        return request, response_data
    
    async def extend_deadline(
        self,
        request_id: UUID,
        reason: str,
        extension_days: int = 60,
    ) -> DSARRequest:
        """Extend the deadline for complex requests."""
        request = await self.storage.get_request(request_id)
        
        request.status = DSARStatus.EXTENDED
        request.deadline = request.deadline + timedelta(days=extension_days)
        request.notes.append(f"Deadline extended: {reason}")
        
        await self.storage.update_request(request)
        await self.notifier.notify_deadline_extension(request, reason)
        
        return request
    
    def _to_csv(self, data: dict) -> bytes:
        """Convert data to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        for category, items in data.items():
            writer.writerow([f"=== {category} ==="])
            if isinstance(items, list) and items:
                if isinstance(items[0], dict):
                    writer.writerow(items[0].keys())
                    for item in items:
                        writer.writerow(item.values())
            writer.writerow([])
        
        return output.getvalue().encode()
''',
    },
    documentation="""# Data Subject Access Request Handler

## Overview
Complete handler for GDPR/CCPA data subject access requests.

## Compliance
- GDPR Article 12: Transparent communication
- GDPR Article 15: Right of access
- GDPR Article 20: Right to data portability
- CCPA Section 1798.100: Right to know

## Features
- Identity verification workflow
- Automated data collection from multiple sources
- Deadline tracking and extensions
- Multiple export formats (JSON, CSV)
""",
    parameters=[],
    tags=["gdpr", "ccpa", "dsar", "privacy", "data-access"],
)


DATA_ACCESS_TEMPLATES = [DSAR_TEMPLATE]
