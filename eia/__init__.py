"""Python client for the Energy Information Administration (EIA) API.

This package provides two API versions:

**API v2 (Recommended)**: Modern hierarchical API with facet-based filtering
    >>> from eia import EIAConfig
    >>> from eia.v2 import EIAClient
    >>> config = EIAConfig.from_env()
    >>> client = EIAClient(config)
    >>> df = client.get_dataframe(
    ...     route="electricity/retail-sales",
    ...     facets={"stateid": ["CA"]},
    ...     frequency="monthly"
    ... )

**API v1 (Legacy)**: Original series-based API (deprecated by EIA in 2023)
    >>> from eia import EIA
    >>> client = EIA.from_env()
    >>> # Note: v1 endpoints may not work - v2 is recommended
"""

from __future__ import annotations

from importlib import metadata

from eia.config import EIAConfig
from eia.constants import Category
from eia.eia_client import EIA

# v1 Legacy imports (for backward compatibility)
from eia.endpoints import (
    CategoryEndpoint,
    GeosetEndpoint,
    SearchEndpoint,
    SeriesCategoryEndpoint,
    SeriesEndpoint,
    UpdatesEndpoint,
)
from eia.models import (
    CategoryData,
    ChildCategory,
    ChildSeries,
    GeosetRegion,
    SearchResult,
    SeriesData,
    UpdateResult,
)

# v2 is exposed via eia.v2 subpackage

try:
    __version__ = metadata.version("pyeia")
except metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    # Configuration (used by both v1 and v2)
    "EIAConfig",
    # Constants
    "Category",
    # v1 Legacy client (deprecated)
    "EIA",
    # v1 Endpoints (for advanced usage - deprecated)
    "SeriesEndpoint",
    "CategoryEndpoint",
    "GeosetEndpoint",
    "SearchEndpoint",
    "UpdatesEndpoint",
    "SeriesCategoryEndpoint",
    # v1 Models (deprecated)
    "SeriesData",
    "CategoryData",
    "ChildCategory",
    "ChildSeries",
    "GeosetRegion",
    "SearchResult",
    "UpdateResult",
]
