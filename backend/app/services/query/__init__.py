"""Query engine — re-exports from canonical module.

.. deprecated::
    This package is a compatibility shim. Use :mod:`app.services.query_engine`
    for the natural language compliance query engine.
"""

import contextlib
import warnings as _warnings


_warnings.warn(
    "app.services.query is deprecated. Import from app.services.query_engine instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export canonical service for backwards compatibility
with contextlib.suppress(ImportError):
    from app.services.query_engine import QueryEngineService  # noqa: F401
