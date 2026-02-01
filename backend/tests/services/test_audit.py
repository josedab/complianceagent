"""Tests for AuditService."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import warnings

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEventType, AuditTrail
from app.services.audit.service import AuditService, AuditEventData, get_audit_service


@pytest_asyncio.fixture
async def audit_service(db_session: AsyncSession) -> AuditService:
    """Create AuditService instance with test database session."""
    return AuditService(db_session)


@pytest.fixture
def organization_id():
    """Create a test organization ID."""
    return uuid4()


@pytest.fixture
def sample_event_data(organization_id):
    """Create sample audit event data."""
    return AuditEventData(
        organization_id=organization_id,
        event_type=AuditEventType.MAPPING_CREATED,
        event_description="Created new compliance mapping",
        event_data={"file": "src/api/users.py", "requirement_id": "GDPR-7.1"},
        actor_type="user",
        actor_email="test@example.com",
    )


class TestAuditService:
    """Test cases for AuditService."""

    @pytest.mark.asyncio
    async def test_log_creates_audit_entry(
        self, audit_service: AuditService, sample_event_data: AuditEventData, db_session: AsyncSession
    ):
        """Test that log() creates an audit trail entry."""
        entry = await audit_service.log(sample_event_data)

        assert entry.id is not None
        assert entry.organization_id == sample_event_data.organization_id
        assert entry.event_type == AuditEventType.MAPPING_CREATED
        assert entry.event_description == "Created new compliance mapping"
        assert entry.actor_email == "test@example.com"

    @pytest.mark.asyncio
    async def test_log_generates_entry_hash(
        self, audit_service: AuditService, sample_event_data: AuditEventData
    ):
        """Test that log() generates a valid entry hash."""
        entry = await audit_service.log(sample_event_data)

        assert entry.entry_hash is not None
        assert len(entry.entry_hash) == 64  # SHA-256 hex length
        assert entry.entry_hash.isalnum()

    @pytest.mark.asyncio
    async def test_log_creates_hash_chain(
        self, audit_service: AuditService, organization_id
    ):
        """Test that sequential entries create a hash chain."""
        # Create first entry
        event1 = AuditEventData(
            organization_id=organization_id,
            event_type=AuditEventType.MAPPING_CREATED,
            event_description="First event",
        )
        entry1 = await audit_service.log(event1)

        # Create second entry
        event2 = AuditEventData(
            organization_id=organization_id,
            event_type=AuditEventType.MAPPING_UPDATED,
            event_description="Second event",
        )
        entry2 = await audit_service.log(event2)

        # Second entry should reference first entry's hash
        assert entry2.previous_hash == entry1.entry_hash

    @pytest.mark.asyncio
    async def test_log_first_entry_has_no_previous_hash(
        self, audit_service: AuditService, sample_event_data: AuditEventData
    ):
        """Test that the first entry has no previous hash."""
        entry = await audit_service.log(sample_event_data)

        assert entry.previous_hash is None

    @pytest.mark.asyncio
    async def test_log_event_shows_deprecation_warning(
        self, audit_service: AuditService, organization_id
    ):
        """Test that log_event() shows deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            await audit_service.log_event(
                organization_id=organization_id,
                event_type=AuditEventType.MAPPING_CREATED,
                event_description="Test event",
            )

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "log_event() is deprecated" in str(w[0].message)

    @pytest.mark.asyncio
    async def test_log_stores_ai_metadata(
        self, audit_service: AuditService, organization_id
    ):
        """Test that AI metadata is stored correctly."""
        event = AuditEventData(
            organization_id=organization_id,
            event_type=AuditEventType.CODE_GENERATED,
            event_description="Generated compliance code",
            actor_type="ai",
            ai_model="copilot",
            ai_confidence=0.92,
        )
        
        entry = await audit_service.log(event)

        assert entry.actor_type == "ai"
        assert entry.ai_model == "copilot"
        assert entry.ai_confidence == 0.92

    @pytest.mark.asyncio
    async def test_log_stores_request_metadata(
        self, audit_service: AuditService, organization_id
    ):
        """Test that request metadata (IP, user agent) is stored."""
        event = AuditEventData(
            organization_id=organization_id,
            event_type=AuditEventType.MAPPING_CREATED,
            event_description="Created mapping via API",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )
        
        entry = await audit_service.log(event)

        assert entry.ip_address == "192.168.1.100"
        assert entry.user_agent == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_log_stores_related_entity_ids(
        self, audit_service: AuditService, organization_id
    ):
        """Test that related entity IDs are stored correctly."""
        regulation_id = uuid4()
        requirement_id = uuid4()
        repository_id = uuid4()
        mapping_id = uuid4()

        event = AuditEventData(
            organization_id=organization_id,
            event_type=AuditEventType.MAPPING_CREATED,
            event_description="Created mapping",
            regulation_id=regulation_id,
            requirement_id=requirement_id,
            repository_id=repository_id,
            mapping_id=mapping_id,
        )
        
        entry = await audit_service.log(event)

        assert entry.regulation_id == regulation_id
        assert entry.requirement_id == requirement_id
        assert entry.repository_id == repository_id
        assert entry.mapping_id == mapping_id


class TestAuditServiceVerification:
    """Test cases for audit chain verification."""

    @pytest.mark.asyncio
    async def test_verify_chain_empty_returns_valid(
        self, audit_service: AuditService, organization_id
    ):
        """Test that verifying an empty chain returns valid."""
        result = await audit_service.verify_chain(organization_id)

        assert result["valid"] is True
        assert result["entries_checked"] == 0

    @pytest.mark.asyncio
    async def test_verify_chain_with_entries(
        self, audit_service: AuditService, organization_id
    ):
        """Test chain verification with multiple entries."""
        # Create multiple entries
        for i in range(3):
            event = AuditEventData(
                organization_id=organization_id,
                event_type=AuditEventType.MAPPING_CREATED,
                event_description=f"Event {i}",
            )
            await audit_service.log(event)

        result = await audit_service.verify_chain(organization_id)

        assert result["valid"] is True
        assert result["entries_checked"] == 3


class TestAuditServiceExport:
    """Test cases for audit trail export."""

    @pytest.mark.asyncio
    async def test_export_audit_package(
        self, audit_service: AuditService, organization_id
    ):
        """Test exporting audit trail as evidence package."""
        # Create some entries
        for i in range(2):
            event = AuditEventData(
                organization_id=organization_id,
                event_type=AuditEventType.MAPPING_CREATED,
                event_description=f"Event {i}",
            )
            await audit_service.log(event)

        package = await audit_service.export_audit_package(organization_id)

        assert package["organization_id"] == str(organization_id)
        assert package["entry_count"] == 2
        assert len(package["entries"]) == 2
        assert "package_hash" in package
        assert "export_date" in package


class TestGetAuditService:
    """Test cases for the factory function."""

    def test_get_audit_service_creates_instance(self, db_session: AsyncSession):
        """Test that get_audit_service creates a valid instance."""
        service = get_audit_service(db_session)

        assert isinstance(service, AuditService)
        assert service.db is db_session
