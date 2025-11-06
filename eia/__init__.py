"""Python client for the Energy Information Administration (EIA) API."""

from __future__ import annotations

from importlib import metadata

from eia.config import EIAConfig
from eia.constants import Category
from eia.eia_client import EIA
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

try:
    __version__ = metadata.version("pyeia")
except metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    # Main client
    "EIA",
    # Configuration
    "EIAConfig",
    # Constants
    "Category",
    # Endpoints (for advanced usage)
    "SeriesEndpoint",
    "CategoryEndpoint",
    "GeosetEndpoint",
    "SearchEndpoint",
    "UpdatesEndpoint",
    "SeriesCategoryEndpoint",
    # Models
    "SeriesData",
    "CategoryData",
    "ChildCategory",
    "ChildSeries",
    "GeosetRegion",
    "SearchResult",
    "UpdateResult",
]
