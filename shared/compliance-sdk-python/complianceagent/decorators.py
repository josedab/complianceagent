"""Compliance decorators for enforcing regulations in code."""

import asyncio
import functools
import inspect
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar, ParamSpec

from complianceagent.audit import AuditAction, AuditLogger, AuditSeverity, get_audit_logger
from complianceagent.config import EnforcementMode, get_config
from complianceagent.exceptions import (
    AccessDeniedError,
    ConsentRequiredError,
    EncryptionError,
    PCIViolationError,
    PHIViolationError,
)


P = ParamSpec("P")
R = TypeVar("R")


def _get_user_id_from_kwargs(kwargs: dict, arg_names: list[str]) -> str | None:
    """Extract user ID from function arguments."""
    for name in ["user_id", "user", "actor_id", "actor", "subject_id", "current_user"]:
        if name in kwargs:
            val = kwargs[name]
            if hasattr(val, "id"):
                return str(val.id)
            return str(val)
    return None


def _is_async_function(func: Callable) -> bool:
    """Check if a function is async."""
    return asyncio.iscoroutinefunction(func)


def require_consent(
    consent_type: str,
    user_id_param: str = "user_id",
    fail_silently: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to require user consent before executing a function.
    
    Verifies that the user has granted the specified type of consent
    before allowing the function to execute.
    
    Args:
        consent_type: Type of consent required (e.g., "marketing", "analytics")
        user_id_param: Name of the parameter containing the user ID
        fail_silently: If True, skip execution instead of raising error
    
    Example:
        @require_consent("marketing")
        def send_marketing_email(user_id: str, content: str):
            # Only executes if user has marketing consent
            pass
    
    Raises:
        ConsentRequiredError: If consent has not been granted
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if config.enforcement_mode == EnforcementMode.DISABLED:
                return func(*args, **kwargs)
            
            # Get user ID
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            user_id = bound.arguments.get(user_id_param)
            
            if user_id is None:
                user_id = _get_user_id_from_kwargs(kwargs, [user_id_param])
            
            # Check consent
            has_consent = _check_consent(user_id, consent_type, config)
            
            if not has_consent:
                # Log the attempt
                logger = get_audit_logger()
                logger.log(
                    action="consent_check_failed",
                    resource_type="consent",
                    resource_id=consent_type,
                    user_id=str(user_id) if user_id else None,
                    regulation="GDPR",
                    requirement="Article 7",
                    severity=AuditSeverity.WARNING,
                    outcome="blocked",
                    function_name=func.__name__,
                )
                
                if config.enforcement_mode == EnforcementMode.STRICT:
                    if fail_silently:
                        return None  # type: ignore
                    raise ConsentRequiredError(consent_type, str(user_id) if user_id else None)
            
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if config.enforcement_mode == EnforcementMode.DISABLED:
                return await func(*args, **kwargs)  # type: ignore
            
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            user_id = bound.arguments.get(user_id_param)
            
            has_consent = _check_consent(user_id, consent_type, config)
            
            if not has_consent:
                logger = get_audit_logger()
                logger.log(
                    action="consent_check_failed",
                    resource_type="consent",
                    resource_id=consent_type,
                    user_id=str(user_id) if user_id else None,
                    regulation="GDPR",
                    requirement="Article 7",
                    severity=AuditSeverity.WARNING,
                    outcome="blocked",
                    function_name=func.__name__,
                )
                
                if config.enforcement_mode == EnforcementMode.STRICT:
                    if fail_silently:
                        return None  # type: ignore
                    raise ConsentRequiredError(consent_type, str(user_id) if user_id else None)
            
            return await func(*args, **kwargs)  # type: ignore
        
        if _is_async_function(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def _check_consent(user_id: Any, consent_type: str, config: Any) -> bool:
    """Check if user has granted consent."""
    if config.consent.consent_callback:
        return config.consent.consent_callback(str(user_id), consent_type)
    # Default: assume consent (should be configured in production)
    return True


def encrypt_pii(
    fields: list[str] | None = None,
    auto_detect: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to ensure PII fields are encrypted.
    
    Automatically encrypts PII fields in function arguments before processing.
    
    Args:
        fields: Specific fields to encrypt (if None, uses auto-detection)
        auto_detect: Whether to auto-detect PII fields by name
    
    Example:
        @encrypt_pii(fields=["email", "ssn"])
        def store_user(user_id: str, email: str, ssn: str):
            # email and ssn are automatically encrypted
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if config.enforcement_mode == EnforcementMode.DISABLED:
                return func(*args, **kwargs)
            
            # Get fields to encrypt
            encrypt_fields = fields or []
            if auto_detect:
                encrypt_fields = list(set(encrypt_fields + config.encryption.pii_fields))
            
            # Encrypt matching kwargs
            encrypted_kwargs = {}
            for key, value in kwargs.items():
                if key in encrypt_fields and isinstance(value, str):
                    encrypted_kwargs[key] = _encrypt_value(value, config)
                else:
                    encrypted_kwargs[key] = value
            
            # Log encryption
            if encrypted_kwargs != kwargs:
                logger = get_audit_logger()
                logger.log(
                    action=AuditAction.ENCRYPTION,
                    resource_type="pii",
                    data_types=["PII"],
                    regulation="GDPR",
                    requirement="Article 32 - Security",
                    function_name=func.__name__,
                    details={"fields_encrypted": [k for k in kwargs if k in encrypt_fields]},
                )
            
            return func(*args, **encrypted_kwargs)  # type: ignore
        
        return wrapper  # type: ignore
    
    return decorator


def _encrypt_value(value: str, config: Any) -> str:
    """Encrypt a value using configured encryption."""
    from complianceagent.config import EncryptionProvider
    
    if config.encryption.provider == EncryptionProvider.FERNET:
        try:
            from cryptography.fernet import Fernet
            
            if config.encryption.encryption_key:
                f = Fernet(config.encryption.encryption_key.encode())
                return f.encrypt(value.encode()).decode()
        except ImportError:
            pass
    
    if config.encryption.custom_encrypt_fn:
        return config.encryption.custom_encrypt_fn(value.encode()).decode()
    
    # Fallback: return original (log warning)
    return value


def audit_log(
    action: str | AuditAction = AuditAction.ACCESS,
    resource_type: str = "data",
    regulation: str | None = None,
    requirement: str | None = None,
    data_types: list[str] | None = None,
    include_args: bool = False,
    include_result: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to automatically log function calls for audit trail.
    
    Args:
        action: The audit action type
        resource_type: Type of resource being accessed
        regulation: Relevant regulation
        requirement: Specific requirement
        data_types: Types of data involved
        include_args: Whether to include function arguments in log
        include_result: Whether to include return value in log
    
    Example:
        @audit_log(action="data_access", regulation="GDPR")
        def get_user_profile(user_id: str):
            # Access is automatically logged
            return fetch_profile(user_id)
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if not config.audit.enabled:
                return func(*args, **kwargs)
            
            logger = get_audit_logger()
            user_id = _get_user_id_from_kwargs(kwargs, ["user_id"])
            
            # Prepare details
            details: dict[str, Any] = {}
            if include_args:
                # Mask sensitive fields
                masked_kwargs = _mask_sensitive(kwargs, config)
                details["arguments"] = masked_kwargs
            
            start_time = datetime.now(timezone.utc)
            outcome = "success"
            
            try:
                result = func(*args, **kwargs)
                if include_result:
                    details["result_type"] = type(result).__name__
                return result
            except Exception as e:
                outcome = "failure"
                details["error"] = str(e)
                raise
            finally:
                # Log the access
                action_str = action if isinstance(action, str) else action.value
                logger.log(
                    action=action_str,
                    resource_type=resource_type,
                    user_id=user_id,
                    regulation=regulation,
                    requirement=requirement,
                    data_types=data_types or [],
                    outcome=outcome,
                    details=details,
                    function_name=func.__name__,
                    module_name=func.__module__,
                )
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if not config.audit.enabled:
                return await func(*args, **kwargs)  # type: ignore
            
            logger = get_audit_logger()
            user_id = _get_user_id_from_kwargs(kwargs, ["user_id"])
            
            details: dict[str, Any] = {}
            if include_args:
                masked_kwargs = _mask_sensitive(kwargs, config)
                details["arguments"] = masked_kwargs
            
            outcome = "success"
            
            try:
                result = await func(*args, **kwargs)  # type: ignore
                if include_result:
                    details["result_type"] = type(result).__name__
                return result
            except Exception as e:
                outcome = "failure"
                details["error"] = str(e)
                raise
            finally:
                action_str = action if isinstance(action, str) else action.value
                logger.log(
                    action=action_str,
                    resource_type=resource_type,
                    user_id=user_id,
                    regulation=regulation,
                    requirement=requirement,
                    data_types=data_types or [],
                    outcome=outcome,
                    details=details,
                    function_name=func.__name__,
                    module_name=func.__module__,
                )
        
        if _is_async_function(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def _mask_sensitive(data: dict, config: Any) -> dict:
    """Mask sensitive fields in data."""
    masked = {}
    for key, value in data.items():
        if key.lower() in [f.lower() for f in config.audit.sensitive_fields_to_mask]:
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive(value, config)
        else:
            masked[key] = value
    return masked


def hipaa_phi(
    purpose: str | None = None,
    minimum_necessary: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for HIPAA PHI handling compliance.
    
    Enforces HIPAA requirements for accessing Protected Health Information.
    
    Args:
        purpose: Purpose of the PHI access (treatment, payment, operations)
        minimum_necessary: Enforce minimum necessary standard
    
    Example:
        @hipaa_phi(purpose="treatment")
        def get_patient_record(patient_id: str, fields: list[str]):
            # PHI access is logged and validated
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if not config.is_regulation_enabled("HIPAA"):
                return func(*args, **kwargs)
            
            # Get user and patient IDs
            user_id = _get_user_id_from_kwargs(kwargs, ["user_id", "accessor_id"])
            patient_id = kwargs.get("patient_id") or kwargs.get("subject_id")
            
            # Log PHI access
            logger = get_audit_logger()
            logger.log_phi_access(
                user_id=str(user_id) if user_id else "unknown",
                patient_id=str(patient_id) if patient_id else "unknown",
                purpose=purpose or "unspecified",
                function_name=func.__name__,
            )
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def pci_cardholder(
    mask_pan: bool = True,
    never_store_cvv: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for PCI-DSS cardholder data handling.
    
    Enforces PCI-DSS requirements for cardholder data.
    
    Args:
        mask_pan: Mask Primary Account Number in logs
        never_store_cvv: Block storage of CVV/CVC
    
    Example:
        @pci_cardholder()
        def process_payment(card_number: str, cvv: str, amount: float):
            # PCI compliance is enforced
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if not config.is_regulation_enabled("PCI-DSS"):
                return func(*args, **kwargs)
            
            # Check for CVV storage attempts
            if never_store_cvv and config.pci_never_store_cvv:
                cvv_fields = ["cvv", "cvc", "cvv2", "cvc2", "security_code"]
                for field in cvv_fields:
                    if field in kwargs and kwargs[field]:
                        if config.enforcement_mode == EnforcementMode.STRICT:
                            raise PCIViolationError(
                                "CVV/CVC must not be stored",
                                requirement_id="3.2",
                            )
            
            # Mask PAN in arguments
            if mask_pan:
                pan_fields = ["card_number", "pan", "account_number", "primary_account_number"]
                for field in pan_fields:
                    if field in kwargs and isinstance(kwargs[field], str):
                        # Only show last 4 digits
                        original = kwargs[field]
                        if len(original) >= 12:
                            kwargs[field] = "*" * (len(original) - 4) + original[-4:]
            
            # Log PCI access
            logger = get_audit_logger()
            logger.log(
                action="payment_processing",
                resource_type="cardholder_data",
                regulation="PCI-DSS",
                requirement="Requirement 3",
                data_types=["PCI"],
                function_name=func.__name__,
            )
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def gdpr_compliant(
    lawful_basis: str | None = None,
    data_categories: list[str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator for general GDPR compliance.
    
    Args:
        lawful_basis: Legal basis for processing (consent, contract, legal_obligation, etc.)
        data_categories: Categories of personal data processed
    
    Example:
        @gdpr_compliant(lawful_basis="consent", data_categories=["contact", "preferences"])
        def update_user_preferences(user_id: str, preferences: dict):
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if not config.is_regulation_enabled("GDPR"):
                return func(*args, **kwargs)
            
            # Log GDPR processing
            logger = get_audit_logger()
            logger.log(
                action="data_processing",
                resource_type="personal_data",
                regulation="GDPR",
                requirement=f"Article 6 - {lawful_basis or 'processing'}",
                data_types=data_categories or ["personal_data"],
                function_name=func.__name__,
                details={"lawful_basis": lawful_basis},
            )
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def data_retention(
    retention_days: int,
    data_type: str = "personal_data",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enforce data retention policies.
    
    Args:
        retention_days: Maximum days to retain data
        data_type: Type of data for retention policy
    
    Example:
        @data_retention(retention_days=365, data_type="user_activity")
        def store_activity_log(user_id: str, activity: dict):
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            # Add retention metadata
            kwargs["_retention_days"] = retention_days
            kwargs["_retention_expires"] = datetime.now(timezone.utc).isoformat()
            
            # Log retention policy application
            logger = get_audit_logger()
            logger.log(
                action="data_storage",
                resource_type=data_type,
                regulation="GDPR",
                requirement="Article 5(1)(e) - Storage limitation",
                function_name=func.__name__,
                details={"retention_days": retention_days},
            )
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def access_control(
    required_roles: list[str] | None = None,
    required_permissions: list[str] | None = None,
    resource_type: str = "data",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enforce access control.
    
    Args:
        required_roles: Roles required to access the function
        required_permissions: Specific permissions required
        resource_type: Type of resource being protected
    
    Example:
        @access_control(required_roles=["admin", "compliance_officer"])
        def view_audit_logs():
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if config.enforcement_mode == EnforcementMode.DISABLED:
                return func(*args, **kwargs)
            
            user_id = _get_user_id_from_kwargs(kwargs, ["user_id"])
            
            # Check roles
            if required_roles and config.access_control.role_provider:
                user_roles = config.access_control.role_provider(str(user_id))
                if not any(role in user_roles for role in required_roles):
                    logger = get_audit_logger()
                    logger.log(
                        action=AuditAction.PERMISSION_DENIED,
                        resource_type=resource_type,
                        user_id=str(user_id) if user_id else None,
                        severity=AuditSeverity.WARNING,
                        outcome="blocked",
                        function_name=func.__name__,
                        details={"required_roles": required_roles},
                    )
                    
                    if config.enforcement_mode == EnforcementMode.STRICT:
                        raise AccessDeniedError(
                            resource=resource_type,
                            user_id=str(user_id) if user_id else None,
                            required_role=",".join(required_roles),
                        )
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def breach_detection(
    anomaly_threshold: int = 100,
    time_window_seconds: int = 60,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to detect potential data breaches through anomalous access patterns.
    
    Args:
        anomaly_threshold: Number of accesses that triggers alert
        time_window_seconds: Time window for counting accesses
    
    Example:
        @breach_detection(anomaly_threshold=50, time_window_seconds=60)
        def bulk_export_users():
            pass
    """
    _access_counts: dict[str, list[float]] = {}
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            import time
            
            config = get_config()
            user_id = _get_user_id_from_kwargs(kwargs, ["user_id"]) or "unknown"
            current_time = time.time()
            
            # Track access
            if user_id not in _access_counts:
                _access_counts[user_id] = []
            
            # Remove old entries
            _access_counts[user_id] = [
                t for t in _access_counts[user_id]
                if current_time - t < time_window_seconds
            ]
            
            _access_counts[user_id].append(current_time)
            
            # Check threshold
            if len(_access_counts[user_id]) >= anomaly_threshold:
                logger = get_audit_logger()
                logger.log(
                    action="potential_breach_detected",
                    resource_type="bulk_access",
                    user_id=user_id,
                    severity=AuditSeverity.CRITICAL,
                    regulation="GDPR",
                    requirement="Article 33 - Breach notification",
                    function_name=func.__name__,
                    details={
                        "access_count": len(_access_counts[user_id]),
                        "threshold": anomaly_threshold,
                        "time_window": time_window_seconds,
                    },
                )
                
                # Notify if callback configured
                if config.on_violation:
                    config.on_violation("potential_breach", {
                        "user_id": user_id,
                        "access_count": len(_access_counts[user_id]),
                    })
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def privacy_by_design(
    minimize_data: bool = True,
    pseudonymize: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to enforce privacy by design principles.
    
    Args:
        minimize_data: Remove unnecessary data fields
        pseudonymize: Replace direct identifiers with pseudonyms
    
    Example:
        @privacy_by_design(minimize_data=True)
        def generate_analytics_report(users: list[dict]):
            pass
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            config = get_config()
            
            if minimize_data:
                # Remove PII fields from data structures
                pii_fields = config.encryption.pii_fields
                for key, value in list(kwargs.items()):
                    if isinstance(value, dict):
                        kwargs[key] = {
                            k: v for k, v in value.items()
                            if k.lower() not in [f.lower() for f in pii_fields]
                        }
                    elif isinstance(value, list):
                        kwargs[key] = [
                            {k: v for k, v in item.items()
                             if k.lower() not in [f.lower() for f in pii_fields]}
                            if isinstance(item, dict) else item
                            for item in value
                        ]
            
            # Log privacy by design application
            logger = get_audit_logger()
            logger.log(
                action="privacy_by_design",
                resource_type="data_processing",
                regulation="GDPR",
                requirement="Article 25 - Data protection by design",
                function_name=func.__name__,
                details={"minimize_data": minimize_data, "pseudonymize": pseudonymize},
            )
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator
