"""Tests for HIPAA-compliant encrypted PHI storage."""

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import ComplianceProcessingError, ResourceNotFoundError
from app.services.templates.encrypted_storage import EncryptedPHIStorage


class _Settings:
    def __init__(self, hipaa_encryption_enabled=False, kms_key_id="", phi_storage_bucket=""):
        self.hipaa_encryption_enabled = hipaa_encryption_enabled
        self.kms_key_id = kms_key_id
        self.phi_storage_bucket = phi_storage_bucket


def _make_storage(kms_key_id="alias/test", phi_storage_bucket="test-bucket"):
    settings = _Settings(
        hipaa_encryption_enabled=True, kms_key_id=kms_key_id, phi_storage_bucket=phi_storage_bucket
    )
    s3_mock = MagicMock()
    kms_mock = MagicMock()
    return EncryptedPHIStorage(settings, s3_client=s3_mock, kms_client=kms_mock), s3_mock


def test_init_hipaa_enabled_missing_kms_key_raises():
    settings = _Settings(hipaa_encryption_enabled=True, kms_key_id="", phi_storage_bucket="bucket")
    with pytest.raises(ComplianceProcessingError, match="KMS key or bucket not configured"):
        EncryptedPHIStorage(settings)


@pytest.mark.asyncio
async def test_store_calls_put_object_with_sse_kms():
    storage, s3_mock = _make_storage()
    await storage.store(
        record_id="abc", encrypted_data=b"encrypted", patient_id="secret", phi_type="lab"
    )
    s3_mock.put_object.assert_called_once()
    kwargs = s3_mock.put_object.call_args[1]
    assert kwargs["ServerSideEncryption"] == "aws:kms"
    assert kwargs["SSEKMSKeyId"] == "alias/test"
    assert kwargs["Key"] == "phi/lab/abc"
    assert "patient_id" not in kwargs["Metadata"]
    assert kwargs["Metadata"]["phi_type"] == "lab"
    assert kwargs["Metadata"]["record_id"] == "abc"


@pytest.mark.asyncio
async def test_retrieve_returns_bytes():
    storage, s3_mock = _make_storage()
    body_mock = MagicMock()
    body_mock.read.return_value = b"secret-phi-data"
    s3_mock.get_object.return_value = {"Body": body_mock}
    data = await storage.retrieve(record_id="abc", phi_type="lab")
    assert data == b"secret-phi-data"


@pytest.mark.asyncio
async def test_retrieve_raises_not_found_on_no_such_key():
    storage, s3_mock = _make_storage()
    s3_mock.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
    )
    with pytest.raises(ResourceNotFoundError, match="abc"):
        await storage.retrieve(record_id="abc", phi_type="lab")


@pytest.mark.asyncio
async def test_retrieve_raises_processing_error_on_other_client_error():
    storage, s3_mock = _make_storage()
    s3_mock.get_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Denied"}}, "GetObject"
    )
    with pytest.raises(ComplianceProcessingError, match="failed to retrieve"):
        await storage.retrieve(record_id="abc", phi_type="lab")
