"""EIA API endpoint implementations."""

from eia.endpoints.category import CategoryEndpoint
from eia.endpoints.geoset import GeosetEndpoint
from eia.endpoints.search import SearchEndpoint
from eia.endpoints.series import SeriesEndpoint
from eia.endpoints.series_category import SeriesCategoryEndpoint
from eia.endpoints.updates import UpdatesEndpoint

__all__ = [
    "SeriesEndpoint",
    "CategoryEndpoint",
    "GeosetEndpoint",
    "SearchEndpoint",
    "UpdatesEndpoint",
    "SeriesCategoryEndpoint",
]
