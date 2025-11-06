"""
Fully typed models for EIA API v2 responses using TypedDict.

These models provide complete type safety with zero runtime overhead
and no external dependencies beyond the standard library.
"""

from typing import Any, TypedDict, NotRequired, Literal
from enum import Enum


# Enums for valid values


class FrequencyType(str, Enum):
    """Valid frequency types for data requests."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class SortDirection(str, Enum):
    """Sort direction options."""

    ASC = "asc"
    DESC = "desc"


# Request echo models


class RequestParams(TypedDict, total=False):
    """Parameters echoed back in the request object."""

    api_key: NotRequired[str]
    frequency: NotRequired[str]
    data: NotRequired[list[str]]
    facets: NotRequired[dict[str, list[str]]]
    start: NotRequired[str]
    end: NotRequired[str]
    sort: NotRequired[list[dict[str, str]]]
    offset: NotRequired[int]
    length: NotRequired[int]


class RequestInfo(TypedDict):
    """Request information echoed back by the API."""

    command: str
    params: RequestParams | dict[str, Any]


# Response models


class ErrorResponse(TypedDict):
    """Error response from the API."""

    error: str
    code: NotRequired[int]


# Data endpoint models


class DataRecord(TypedDict, total=False):
    """
    A single data record. Structure varies by dataset.

    Common fields include period, value, and various dimension identifiers.
    All fields are optional except period.
    """

    period: str
    value: NotRequired[float | int | str | None]
    # Additional fields vary by dataset and are accessed via dict syntax


class DataResponseBody(TypedDict):
    """Response body for data endpoint requests."""

    total: int
    data: list[dict[str, Any]]
    dateFormat: NotRequired[str]
    frequency: NotRequired[str]
    description: NotRequired[str]
    copyright: NotRequired[str]
    startPeriod: NotRequired[str]
    endPeriod: NotRequired[str]


class DataResponse(TypedDict):
    """Complete typed response for data endpoint."""

    response: DataResponseBody
    request: RequestInfo
    apiVersion: NotRequired[str]


# Facet endpoint models


class FacetItem(TypedDict):
    """A single facet value with its identifier and name."""

    id: str
    name: NotRequired[str]
    alias: NotRequired[str]


class FacetResponseBody(TypedDict):
    """Response body for facet endpoint requests."""

    facets: list[FacetItem]
    total: NotRequired[int]
    description: NotRequired[str]


class FacetResponse(TypedDict):
    """Complete typed response for facet endpoint."""

    response: FacetResponseBody
    request: RequestInfo
    apiVersion: NotRequired[str]


# Route/metadata endpoint models


class RouteInfo(TypedDict, total=False):
    """Information about an available API route."""

    id: str
    name: NotRequired[str]
    description: NotRequired[str]
    frequency: NotRequired[list[str]]
    facets: NotRequired[list[str]]
    data: NotRequired[dict[str, Any]]
    startPeriod: NotRequired[str]
    endPeriod: NotRequired[str]
    defaultDateFormat: NotRequired[str]
    defaultFrequency: NotRequired[str]


class RouteResponseBody(TypedDict, total=False):
    """Response body for route/metadata endpoint requests."""

    id: NotRequired[str]
    name: NotRequired[str]
    description: NotRequired[str]
    frequency: NotRequired[list[str]]
    facets: NotRequired[list[str]]
    routes: NotRequired[list[RouteInfo]]
    data: NotRequired[dict[str, Any]]
    startPeriod: NotRequired[str]
    endPeriod: NotRequired[str]
    defaultDateFormat: NotRequired[str]
    defaultFrequency: NotRequired[str]


class RouteResponse(TypedDict):
    """Complete typed response for route/metadata endpoint."""

    response: RouteResponseBody
    request: RequestInfo
    apiVersion: NotRequired[str]


# Series ID lookup response (legacy compatibility)


class SeriesIDResponseBody(TypedDict, total=False):
    """Response body for series ID lookup."""

    seriesId: str
    name: NotRequired[str]
    units: NotRequired[str]
    frequency: NotRequired[str]
    data: list[dict[str, Any]]
    description: NotRequired[str]
    copyright: NotRequired[str]
    source: NotRequired[str]
    iso3166: NotRequired[str]
    geography: NotRequired[str]
    start: NotRequired[str]
    end: NotRequired[str]
    lastUpdated: NotRequired[str]


class SeriesIDResponse(TypedDict):
    """Complete typed response for series ID endpoint."""

    response: SeriesIDResponseBody
    request: RequestInfo
    apiVersion: NotRequired[str]
