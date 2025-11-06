"""
Modern, fully-typed Python client for EIA API v2.

This module provides both synchronous and asynchronous interfaces for interacting
with the U.S. Energy Information Administration's API v2.
"""

from eia.v2.client import EIAClient, AsyncEIAClient
from eia.v2.models import (
    DataResponse,
    FacetResponse,
    RouteResponse,
    ErrorResponse,
    FrequencyType,
)
from eia.v2.exceptions import EIAError, EIAAPIError, EIAValidationError

__all__ = [
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
