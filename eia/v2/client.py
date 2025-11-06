"""
Modern, fully-typed EIA API v2 client with sync and async support.

This client provides a clean, type-safe interface to the EIA API v2 with
support for bulk data ingestion and integration with modern data tools.

Uses only standard library types for zero-overhead performance.
"""

from typing import Any
from urllib.parse import urljoin

import httpx

from eia.v2.exceptions import EIAAPIError, EIAValidationError
from eia.v2.models import (
    DataResponse,
    FacetResponse,
    RouteResponse,
    SeriesIDResponse,
    ErrorResponse,
    FrequencyType,
    SortDirection,
)


class BaseEIAClient:
    """Base client with shared configuration and utility methods."""

    BASE_URL = "https://api.eia.gov/v2/"
    DEFAULT_TIMEOUT = 60.0
    MAX_ROWS = 5000

    def __init__(
        self,
        api_key: str,
        timeout: float | None = None,
        base_url: str | None = None,
    ) -> None:
        """
        Initialize the EIA API client.

        Args:
            api_key: Your EIA API key (get one at https://www.eia.gov/opendata/register.php)
            timeout: Request timeout in seconds (default: 60.0)
            base_url: Base URL for the API (default: https://api.eia.gov/v2/)
        """
        if not api_key:
            raise EIAValidationError("API key is required")

        self.api_key = api_key
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.base_url = base_url or self.BASE_URL

    def _build_url(self, route: str) -> str:
        """Build the full URL for a given route."""
        # Ensure route starts with / for proper joining
        if not route.startswith("/"):
            route = f"/{route}"
        return urljoin(self.base_url, route.lstrip("/"))

    def _build_params(
        self,
        frequency: FrequencyType | str | None = None,
        data: list[str] | None = None,
        facets: dict[str, list[str] | str] | None = None,
        start: str | None = None,
        end: str | None = None,
        sort: list[tuple[str, SortDirection | str]] | None = None,
        offset: int | None = None,
        length: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Build query parameters for API requests.

        Args:
            frequency: Data frequency (hourly, daily, weekly, monthly, quarterly, annual)
            data: List of data columns to retrieve
            facets: Dictionary of facet filters {facet_name: [values]}
            start: Start period (format depends on frequency)
            end: End period (format depends on frequency)
            sort: List of (column, direction) tuples for sorting
            offset: Pagination offset
            length: Number of rows to return (max 5000)
            **kwargs: Additional parameters

        Returns:
            Dictionary of query parameters
        """
        params: dict[str, Any] = {"api_key": self.api_key}

        if frequency:
            params["frequency"] = frequency

        if data:
            for i, col in enumerate(data):
                params[f"data[{i}]"] = col

        if facets:
            for facet_name, values in facets.items():
                if isinstance(values, str):
                    values = [values]
                for i, value in enumerate(values):
                    params[f"facets[{facet_name}][{i}]"] = value

        if start:
            params["start"] = start

        if end:
            params["end"] = end

        if sort:
            for i, (column, direction) in enumerate(sort):
                params[f"sort[{i}][column]"] = column
                params[f"sort[{i}][direction]"] = direction

        if offset is not None:
            params["offset"] = offset

        if length is not None:
            if length > self.MAX_ROWS:
                raise EIAValidationError(
                    f"Length cannot exceed {self.MAX_ROWS} rows per request"
                )
            params["length"] = length

        # Add any additional parameters
        params.update(kwargs)

        return params

    @staticmethod
    def _handle_error_response(response: httpx.Response) -> None:
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            if "error" in error_data:
                raise EIAAPIError(
                    error_data["error"], error_data.get("code", response.status_code)
                )
        except Exception as e:
            if isinstance(e, EIAAPIError):
                raise
            # If we can't parse the error, raise a generic one
            raise EIAAPIError(
                f"API request failed with status {response.status_code}: {response.text}",
                response.status_code,
            )


class EIAClient(BaseEIAClient):
    """
    Synchronous client for EIA API v2.

    Example:
        >>> client = EIAClient(api_key="your_api_key")
        >>> response = client.get_data(
        ...     route="electricity/retail-sales",
        ...     data=["price", "revenue"],
        ...     frequency="annual",
        ...     facets={"sectorid": ["RES", "COM"]},
        ... )
        >>> print(f"Retrieved {response['response']['total']} records")
        >>> for record in response['response']['data']:
        ...     print(record)
    """

    def __init__(
        self,
        api_key: str,
        timeout: float | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize synchronous EIA API client."""
        super().__init__(api_key, timeout, base_url)
        self._client: httpx.Client | None = None

    def __enter__(self) -> "EIAClient":
        """Context manager entry."""
        self._client = httpx.Client(timeout=self.timeout)
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        if self._client:
            self._client.close()
            self._client = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def get_data(
        self,
        route: str,
        frequency: FrequencyType | str | None = None,
        data: list[str] | None = None,
        facets: dict[str, list[str] | str] | None = None,
        start: str | None = None,
        end: str | None = None,
        sort: list[tuple[str, SortDirection | str]] | None = None,
        offset: int | None = None,
        length: int | None = None,
        **kwargs: Any,
    ) -> DataResponse:
        """
        Get data from a specific route.

        Args:
            route: API route (e.g., "electricity/retail-sales")
            frequency: Data frequency
            data: List of data columns to retrieve
            facets: Dictionary of facet filters
            start: Start period
            end: End period
            sort: List of (column, direction) tuples for sorting
            offset: Pagination offset
            length: Number of rows to return
            **kwargs: Additional parameters

        Returns:
            DataResponse with typed data

        Example:
            >>> response = client.get_data(
            ...     route="electricity/retail-sales",
            ...     data=["price"],
            ...     frequency="monthly",
            ...     facets={"stateid": ["CA", "NY"]},
            ...     start="2023-01",
            ...     end="2023-12",
            ... )
        """
        url = self._build_url(f"{route}/data")
        params = self._build_params(
            frequency=frequency,
            data=data,
            facets=facets,
            start=start,
            end=end,
            sort=sort,
            offset=offset,
            length=length,
            **kwargs,
        )

        client = self._get_client()
        response = client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    def get_facet(
        self,
        route: str,
        facet: str,
        **kwargs: Any,
    ) -> FacetResponse:
        """
        Get available values for a specific facet.

        Args:
            route: API route (e.g., "electricity/retail-sales")
            facet: Facet name (e.g., "sectorid", "stateid")
            **kwargs: Additional parameters

        Returns:
            FacetResponse with available facet values

        Example:
            >>> response = client.get_facet(
            ...     route="electricity/retail-sales",
            ...     facet="sectorid",
            ... )
            >>> for item in response['response']['facets']:
            ...     print(f"{item['id']}: {item.get('name', '')}")
        """
        url = self._build_url(f"{route}/facet/{facet}")
        params = {"api_key": self.api_key, **kwargs}

        client = self._get_client()
        response = client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    def get_route(
        self,
        route: str = "",
        **kwargs: Any,
    ) -> RouteResponse:
        """
        Get metadata and available child routes for a specific route.

        Args:
            route: API route (e.g., "electricity", "electricity/retail-sales")
                   Empty string returns root routes
            **kwargs: Additional parameters

        Returns:
            RouteResponse with route metadata and child routes

        Example:
            >>> # Get root routes
            >>> response = client.get_route()
            >>> for route in response['response'].get('routes', []):
            ...     print(f"{route['id']}: {route.get('name', '')}")
            >>>
            >>> # Get specific route metadata
            >>> response = client.get_route("electricity/retail-sales")
            >>> print(response['response'].get('description', ''))
        """
        url = self._build_url(route) if route else self.base_url
        params = {"api_key": self.api_key, **kwargs}

        client = self._get_client()
        response = client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    def get_series(
        self,
        series_id: str,
        **kwargs: Any,
    ) -> SeriesIDResponse:
        """
        Get data by series ID (legacy v1 compatibility).

        Args:
            series_id: Series ID from API v1
            **kwargs: Additional parameters

        Returns:
            SeriesIDResponse with series data

        Example:
            >>> response = client.get_series("ELEC.GEN.ALL-99.A")
            >>> print(response['response'].get('name', ''))
        """
        url = self._build_url(f"seriesid/{series_id}")
        params = {"api_key": self.api_key, **kwargs}

        client = self._get_client()
        response = client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    def get_all_data(
        self,
        route: str,
        frequency: FrequencyType | str | None = None,
        data: list[str] | None = None,
        facets: dict[str, list[str] | str] | None = None,
        start: str | None = None,
        end: str | None = None,
        sort: list[tuple[str, SortDirection | str]] | None = None,
        max_rows: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Get all data with automatic pagination for bulk ingestion.

        This method automatically handles pagination to retrieve all available
        data, making it ideal for bulk data ingestion into systems like
        DuckDB or Iceberg.

        Args:
            route: API route
            frequency: Data frequency
            data: List of data columns to retrieve
            facets: Dictionary of facet filters
            start: Start period
            end: End period
            sort: List of (column, direction) tuples for sorting
            max_rows: Maximum total rows to retrieve (None for all)
            **kwargs: Additional parameters

        Returns:
            List of all data records as dictionaries

        Example:
            >>> records = client.get_all_data(
            ...     route="electricity/retail-sales",
            ...     data=["price", "revenue"],
            ...     frequency="monthly",
            ...     max_rows=10000,
            ... )
            >>> # Can be easily loaded into DuckDB:
            >>> # import duckdb
            >>> # duckdb.query("SELECT * FROM records").show()
        """
        all_data: list[dict[str, Any]] = []
        offset = 0
        length = self.MAX_ROWS

        while True:
            response = self.get_data(
                route=route,
                frequency=frequency,
                data=data,
                facets=facets,
                start=start,
                end=end,
                sort=sort,
                offset=offset,
                length=length,
                **kwargs,
            )

            all_data.extend(response["response"]["data"])

            # Check if we've reached the end or hit max_rows limit
            if max_rows and len(all_data) >= max_rows:
                return all_data[:max_rows]

            if len(response["response"]["data"]) < length:
                # We've gotten all the data
                break

            if offset + length >= response["response"]["total"]:
                # We've reached the total
                break

            offset += length

        return all_data

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None


class AsyncEIAClient(BaseEIAClient):
    """
    Asynchronous client for EIA API v2.

    Example:
        >>> async with AsyncEIAClient(api_key="your_api_key") as client:
        ...     response = await client.get_data(
        ...         route="electricity/retail-sales",
        ...         data=["price"],
        ...         frequency="annual",
        ...     )
        ...     print(f"Retrieved {response['response']['total']} records")
    """

    def __init__(
        self,
        api_key: str,
        timeout: float | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize asynchronous EIA API client."""
        super().__init__(api_key, timeout, base_url)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsyncEIAClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_data(
        self,
        route: str,
        frequency: FrequencyType | str | None = None,
        data: list[str] | None = None,
        facets: dict[str, list[str] | str] | None = None,
        start: str | None = None,
        end: str | None = None,
        sort: list[tuple[str, SortDirection | str]] | None = None,
        offset: int | None = None,
        length: int | None = None,
        **kwargs: Any,
    ) -> DataResponse:
        """
        Asynchronously get data from a specific route.

        See EIAClient.get_data for full documentation.
        """
        url = self._build_url(f"{route}/data")
        params = self._build_params(
            frequency=frequency,
            data=data,
            facets=facets,
            start=start,
            end=end,
            sort=sort,
            offset=offset,
            length=length,
            **kwargs,
        )

        client = self._get_client()
        response = await client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    async def get_facet(
        self,
        route: str,
        facet: str,
        **kwargs: Any,
    ) -> FacetResponse:
        """
        Asynchronously get available values for a specific facet.

        See EIAClient.get_facet for full documentation.
        """
        url = self._build_url(f"{route}/facet/{facet}")
        params = {"api_key": self.api_key, **kwargs}

        client = self._get_client()
        response = await client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    async def get_route(
        self,
        route: str = "",
        **kwargs: Any,
    ) -> RouteResponse:
        """
        Asynchronously get metadata and available child routes.

        See EIAClient.get_route for full documentation.
        """
        url = self._build_url(route) if route else self.base_url
        params = {"api_key": self.api_key, **kwargs}

        client = self._get_client()
        response = await client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    async def get_series(
        self,
        series_id: str,
        **kwargs: Any,
    ) -> SeriesIDResponse:
        """
        Asynchronously get data by series ID.

        See EIAClient.get_series for full documentation.
        """
        url = self._build_url(f"seriesid/{series_id}")
        params = {"api_key": self.api_key, **kwargs}

        client = self._get_client()
        response = await client.get(url, params=params)

        if response.status_code != 200:
            self._handle_error_response(response)

        return response.json()  # type: ignore

    async def get_all_data(
        self,
        route: str,
        frequency: FrequencyType | str | None = None,
        data: list[str] | None = None,
        facets: dict[str, list[str] | str] | None = None,
        start: str | None = None,
        end: str | None = None,
        sort: list[tuple[str, SortDirection | str]] | None = None,
        max_rows: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Asynchronously get all data with automatic pagination.

        See EIAClient.get_all_data for full documentation.
        """
        all_data: list[dict[str, Any]] = []
        offset = 0
        length = self.MAX_ROWS

        while True:
            response = await self.get_data(
                route=route,
                frequency=frequency,
                data=data,
                facets=facets,
                start=start,
                end=end,
                sort=sort,
                offset=offset,
                length=length,
                **kwargs,
            )

            all_data.extend(response["response"]["data"])

            # Check if we've reached the end or hit max_rows limit
            if max_rows and len(all_data) >= max_rows:
                return all_data[:max_rows]

            if len(response["response"]["data"]) < length:
                break

            if offset + length >= response["response"]["total"]:
                break

            offset += length

        return all_data

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
