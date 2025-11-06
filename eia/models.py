"""Typed models for EIA API requests and responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Union

from typing_extensions import TypeAlias

DataPoint: TypeAlias = tuple[str, Union[float, int, str, None]]


@dataclass(frozen=True)
class SeriesData:
    """A single time series from the EIA API."""

    series_id: str
    name: str
    units: str
    f: str  # Frequency
    data: list[DataPoint]
    description: str | None = None
    copyright: str | None = None
    source: str | None = None
    iso3166: str | None = None
    geography: str | None = None
    start: str | None = None
    end: str | None = None
    last_updated: str | None = None
    unitsshort: str | None = None
    latestPeriod: str | None = None


@dataclass(frozen=True)
class ChildCategory:
    """A child category in the EIA category hierarchy."""

    category_id: int
    name: str


@dataclass(frozen=True)
class ChildSeries:
    """A child series reference in a category."""

    series_id: str
    name: str
    f: str
    units: str
    updated: str
    unitsshort: str | None = None


@dataclass(frozen=True)
class CategoryData:
    """Category information from the EIA API."""

    category_id: int
    name: str
    parent_category_id: int | None = None
    childcategories: list[ChildCategory] = field(default_factory=list)
    childseries: list[ChildSeries] = field(default_factory=list)
    notes: str | None = None


@dataclass(frozen=True)
class GeosetRegion:
    """Geographic region data from geoset endpoint."""

    geoset_id: str
    region_id: str
    name: str
    data: list[DataPoint]
    f: str
    units: str
    unitsshort: str | None = None


@dataclass(frozen=True)
class SearchResult:
    """A single search result."""

    series_id: str
    name: str
    f: str
    units: str
    last_updated: str
    unitsshort: str | None = None
    description: str | None = None
    geography: str | None = None
    start: str | None = None
    end: str | None = None


@dataclass(frozen=True)
class UpdateResult:
    """A single update result from the updates endpoint."""

    series_id: str
    name: str
    f: str
    units: str
    updated: str
    unitsshort: str | None = None


@dataclass(frozen=True)
class SeriesCategoryResult:
    """Category information for a series."""

    series_id: str
    categories: list[int]


# Request types
SearchField: TypeAlias = Literal["series_id", "name", "last_updated"]


@dataclass(frozen=True)
class SeriesRequest:
    """Request for series data."""

    series_ids: list[str]
    api_key: str


@dataclass(frozen=True)
class CategoryRequest:
    """Request for category data."""

    category_id: int | None
    api_key: str


@dataclass(frozen=True)
class GeosetRequest:
    """Request for geoset data."""

    geoset_id: str
    regions: list[str]
    api_key: str


@dataclass(frozen=True)
class SearchRequest:
    """Request for search."""

    search_term: str
    search_value: str | tuple[str, str]
    rows_per_page: int
    api_key: str


@dataclass(frozen=True)
class UpdatesRequest:
    """Request for updates."""

    category_id: int | None
    rows: int
    firstrow: int
    deep: bool
    api_key: str


@dataclass(frozen=True)
class SeriesCategoryRequest:
    """Request for series categories."""

    series_ids: list[str]
    api_key: str


# Response wrappers
@dataclass(frozen=True)
class SeriesResponse:
    """Response from series endpoint."""

    request: dict[str, Any]
    series: list[SeriesData]


@dataclass(frozen=True)
class CategoryResponse:
    """Response from category endpoint."""

    request: dict[str, Any]
    category: CategoryData


@dataclass(frozen=True)
class GeosetResponse:
    """Response from geoset endpoint."""

    request: dict[str, Any]
    geoset: list[GeosetRegion]


@dataclass(frozen=True)
class SearchResponse:
    """Response from search endpoint."""

    request: dict[str, Any]
    response: dict[str, Any]
    results: list[SearchResult]
    total_results: int


@dataclass(frozen=True)
class UpdatesResponse:
    """Response from updates endpoint."""

    request: dict[str, Any]
    updates: list[UpdateResult]


@dataclass(frozen=True)
class SeriesCategoryResponse:
    """Response from series category endpoint."""

    request: dict[str, Any]
    series_categories: list[SeriesCategoryResult]
