"""
pyEIA - Modern Python client for the U.S. Energy Information Administration API.

This package provides both v1 (deprecated) and v2 (current) API clients.
For new projects, use the v2 client.
"""

try:
    from importlib import metadata
    __version__ = metadata.version("pyeia")
except Exception:
    __version__ = "2.0.0"

# Export v2 client as the default
from eia.v2 import (
    EIAClient,
    AsyncEIAClient,
    DataResponse,
    FacetResponse,
    RouteResponse,
    ErrorResponse,
    FrequencyType,
    EIAError,
    EIAAPIError,
    EIAValidationError,
)

__all__ = [
    "__version__",
    "EIAClient",
    "AsyncEIAClient",
    "DataResponse",
    "FacetResponse",
    "RouteResponse",
    "ErrorResponse",
    "FrequencyType",
    "EIAError",
    "EIAAPIError",
    "EIAValidationError",
]
