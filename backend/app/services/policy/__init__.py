"""Policy management — re-exports from canonical modules.

.. deprecated::
    This package is a compatibility shim. Use the canonical modules directly:
    - :mod:`app.services.policy_as_code` for Rego/OPA policy generation
    - :mod:`app.services.policy_sdk` for the compliance-as-code SDK
    - :mod:`app.services.policy_marketplace` for shared policy templates
"""

import contextlib
import warnings as _warnings


_warnings.warn(
    "app.services.policy is deprecated. "
    "Import from app.services.policy_as_code or app.services.policy_sdk instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export canonical services for backwards compatibility
with contextlib.suppress(ImportError):
    from app.services.policy_as_code import PolicyAsCodeService  # noqa: F401

with contextlib.suppress(ImportError):
    from app.services.policy_sdk import PolicySDKService  # noqa: F401
