"""Typed models for EIA API v2 requests and responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict, Union

from typing_extensions import NotRequired, TypeAlias

# TypedDict for API response structures


class RouteInfoDict(TypedDict, total=False):
    """Raw route info from API response."""

    id: str
    name: str
    description: NotRequired[str]
    frequency: NotRequired[list[str]]
    facets: NotRequired[list[str]]
    data: NotRequired[list[str]]
    startPeriod: NotRequired[str]
    endPeriod: NotRequired[str]
    lastUpdated: NotRequired[str]


class RoutesResponseDict(TypedDict):
    """Response containing routes."""

    response: RoutesResponseDataDict


class RoutesResponseDataDict(TypedDict):
    """Response data with routes list."""

    routes: list[RouteInfoDict]


class DataResponseDict(TypedDict, total=False):
    """Response from data endpoint."""

    response: DataResponseDataDict


class DataResponseDataDict(TypedDict, total=False):
    """Data response content."""

    total: int
    dateFormat: NotRequired[str]
    frequency: NotRequired[str]
    data: list[DataPointDict]
    description: NotRequired[str]
    copyright: NotRequired[str]
    units: NotRequired[str]


class DataPointDict(TypedDict, total=False):
    """Generic data point structure.

    Note: Actual structure varies by route and facets.
    Common fields include period, value, and various facet dimensions.
    """

    period: str
    value: str | float | int | None
    # Facet fields (examples - actual fields vary)
    stateid: NotRequired[str]
    sectorid: NotRequired[str]
    productid: NotRequired[str]
    seriesId: NotRequired[str]
    regionid: NotRequired[str]
    fueltype: NotRequired[str]
    # Additional metadata fields
    price: NotRequired[float | str | None]
    units: NotRequired[str]


# Frozen dataclass models (user-facing)


@dataclass(frozen=True)
class RouteInfo:
    """Information about a route in the EIA API hierarchy.

    Routes represent datasets or collections in the hierarchical API structure.
    """

    id: str
    name: str
    description: str | None = None
    frequency: list[str] | None = None
    facets: list[str] | None = None
    data_columns: list[str] | None = None
    start_period: str | None = None
    end_period: str | None = None
    last_updated: datetime | None = None


@dataclass(frozen=True)
class DataResponse:
    """Response from a data query.

    Contains metadata about the query and the actual data points.
    """

    total: int
    date_format: str | None
    frequency: str | None
    data: list[DataPointDict]
    description: str | None = None
    copyright: str | None = None
    units: str | None = None


@dataclass(frozen=True)
class RoutesResponse:
    """Response containing child routes for navigation."""

    routes: list[RouteInfo]


@dataclass
class QueryParams:
    """Parameters for a data query.

    Uses modern Python dataclass with mutable fields for building queries.
    """

    frequency: str | None = None
    data: list[str] = field(default_factory=lambda: ["value"])
    facets: dict[str, list[str]] = field(default_factory=dict)
    start: str | None = None
    end: str | None = None
    sort: list[dict[str, str]] = field(default_factory=lambda: [
        {"column": "period", "direction": "desc"}
    ])
    offset: int = 0
    length: int = 5000

    def to_params(self) -> dict[str, str | int]:
        """Convert to URL parameters using v2 array notation.

        Returns:
            Dictionary of parameters formatted for v2 API
        """
        params: dict[str, str | int] = {}

        # Add data fields with array notation
        for i, col in enumerate(self.data):
            params[f"data[{i}]"] = col

        # Add facets with array notation
        for facet_key, facet_values in self.facets.items():
            if isinstance(facet_values, list):
                for value in facet_values:
                    # Array notation for multiple values
                    key = f"facets[{facet_key}][]"
                    if key in params:
                        # Handle multiple values - need to store as list
                        pass  # httpx will handle this
                    params[key] = value
            else:
                params[f"facets[{facet_key}][]"] = facet_values

        # Add sort parameters
        for i, sort_item in enumerate(self.sort):
            params[f"sort[{i}][column]"] = sort_item["column"]
            params[f"sort[{i}][direction]"] = sort_item["direction"]

        # Add other parameters
        if self.frequency:
            params["frequency"] = self.frequency
        if self.start:
            params["start"] = self.start
        if self.end:
            params["end"] = self.end

        params["offset"] = self.offset
        params["length"] = self.length

        return params


@dataclass(frozen=True)
class PaginatedData:
    """Result of fetching paginated data.

    Combines all pages into a single response.
    """

    total: int
    data: list[DataPointDict]
    pages_fetched: int
    frequency: str | None = None
    date_format: str | None = None


# Type aliases for convenience
Facets: TypeAlias = dict[str, Union[list[str], str]]
