"""HIPAA-compliant PHI storage using S3 + KMS envelope encryption."""

import asyncio

import structlog

from app.core.exceptions import ComplianceProcessingError, ResourceNotFoundError


logger = structlog.get_logger()

try:
    import boto3  # type: ignore[import-untyped]
    from botocore.exceptions import ClientError  # type: ignore[import-untyped]

    _BOTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]
    _BOTO_AVAILABLE = False

    class ClientError(Exception):  # type: ignore[no-redef]
        def __init__(self, response=None, operation_name=""):
            self.response = response or {}
            super().__init__(str(response))


class EncryptedPHIStorage:
    def __init__(self, settings, s3_client=None, kms_client=None):
        self.settings = settings
        if settings.hipaa_encryption_enabled:
            if not settings.kms_key_id or not settings.phi_storage_bucket:
                raise ComplianceProcessingError(
                    "HIPAA encryption enabled but KMS key or bucket not configured"
                )
        self.s3 = s3_client
        self.kms = kms_client
        if self.s3 is None and _BOTO_AVAILABLE:
            self.s3 = boto3.client("s3")
        if self.kms is None and _BOTO_AVAILABLE:
            self.kms = boto3.client("kms")

    def _key(self, phi_type: str, record_id: str) -> str:
        return f"phi/{phi_type}/{record_id}"

    async def store(
        self, record_id: str, encrypted_data: bytes, patient_id: str, phi_type: str
    ) -> dict:
        """Store PHI encrypted at rest via SSE-KMS. patient_id is NOT written to metadata."""
        if self.s3 is None:
            raise ComplianceProcessingError("S3 client unavailable")
        key = self._key(phi_type, record_id)
        try:
            await asyncio.to_thread(
                self.s3.put_object,
                Bucket=self.settings.phi_storage_bucket,
                Key=key,
                Body=encrypted_data,
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self.settings.kms_key_id,
                Metadata={"phi_type": phi_type, "record_id": record_id},
            )
        except ClientError as exc:
            logger.exception("phi store failed", record_id=record_id, phi_type=phi_type)
            raise ComplianceProcessingError("failed to store encrypted PHI") from exc
        logger.info("phi stored", record_id=record_id, phi_type=phi_type, key=key)
        return {"record_id": record_id, "key": key, "bucket": self.settings.phi_storage_bucket}

    async def retrieve(self, record_id: str, phi_type: str = "") -> bytes:
        """Retrieve encrypted PHI bytes."""
        if self.s3 is None:
            raise ComplianceProcessingError("S3 client unavailable")
        key = self._key(phi_type, record_id)
        try:
            resp = await asyncio.to_thread(
                self.s3.get_object,
                Bucket=self.settings.phi_storage_bucket,
                Key=key,
            )
            body = resp["Body"]
            data = await asyncio.to_thread(body.read)
            return data
        except ClientError as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
            if code == "NoSuchKey":
                raise ResourceNotFoundError(f"PHI record not found: {record_id}") from exc
            logger.exception("phi retrieve failed", record_id=record_id, phi_type=phi_type)
            raise ComplianceProcessingError("failed to retrieve encrypted PHI") from exc
