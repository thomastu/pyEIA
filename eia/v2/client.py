"""Main EIA API v2 client with route navigation and data queries."""

from __future__ import annotations

import pandas as pd

from eia.config import EIAConfig
from eia.v2.http_client import V2HttpClient
from eia.v2.models import (
    DataPointDict,
    DataResponse,
    DataResponseDict,
    PaginatedData,
    RouteInfo,
    RouteInfoDict,
)


class EIAClient:
    """Main client for EIA API v2.

    Provides route-based navigation and data querying with facet support.

    Examples:
        >>> # Initialize client
        >>> from eia import EIAConfig
        >>> from eia.v2 import EIAClient
        >>> config = EIAConfig.from_env()
        >>> client = EIAClient(config)

        >>> # Get route information
        >>> routes = client.get_routes("electricity")
        >>> print(routes)

        >>> # Query data with facets
        >>> data = client.get_data(
        ...     route="electricity/retail-sales",
        ...     facets={"stateid": ["CA"], "sectorid": ["RES"]},
        ...     frequency="monthly",
        ...     start="2023-01",
        ...     end="2024-01"
        ... )

        >>> # Get as DataFrame
        >>> df = client.get_dataframe(
        ...     route="electricity/retail-sales",
        ...     facets={"stateid": ["CA", "TX"]},
        ...     frequency="annual"
        ... )
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the v2 client.

        Args:
            config: EIA API configuration
        """
        self.config = config
        self._http = V2HttpClient(config)

    # Sync methods

    def get_routes(self, parent_route: str = "") -> list[RouteInfo]:
        """Get available child routes for a parent route.

        Args:
            parent_route: Parent route path (empty for root routes)

        Returns:
            List of available child routes

        Examples:
            >>> # Get root routes
            >>> routes = client.get_routes()

            >>> # Get electricity sub-routes
            >>> routes = client.get_routes("electricity")
        """
        route = parent_route.rstrip("/") if parent_route else ""
        response = self._http.get_routes_sync(route)

        # Parse routes from response
        routes_data = response["response"]["routes"]
        return [self._parse_route_info(r) for r in routes_data]

    def get_data(
        self,
        route: str,
        facets: dict[str, list[str] | str] | None = None,
        frequency: str | None = None,
        data_fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        offset: int = 0,
        length: int = 5000,
    ) -> DataResponse:
        """Query data from a route with optional filtering.

        Args:
            route: Data route (e.g., "electricity/retail-sales")
            facets: Facet filters (e.g., {"stateid": ["CA"], "sectorid": ["RES"]})
            frequency: Data frequency (daily, monthly, annual, etc.)
            data_fields: Fields to include in response (default: ["value"])
            start: Start period (format depends on frequency)
            end: End period
            offset: Pagination offset
            length: Number of rows to fetch (max 5000)

        Returns:
            DataResponse with query results

        Examples:
            >>> data = client.get_data(
            ...     route="electricity/retail-sales",
            ...     facets={"stateid": ["CA"]},
            ...     frequency="monthly",
            ...     start="2023-01"
            ... )
        """
        # Build data route
        data_route = f"{route.rstrip('/')}/data/"

        # Build parameters
        params: list[tuple[str, str | int]] = []

        # Add data fields
        if data_fields is None:
            data_fields = ["value"]
        for field in data_fields:
            params.append(("data[]", field))

        # Add facets
        if facets:
            for facet_key, values in facets.items():
                if isinstance(values, list):
                    for value in values:
                        params.append((f"facets[{facet_key}][]", str(value)))
                else:
                    params.append((f"facets[{facet_key}][]", str(values)))

        # Add sort
        params.extend([
            ("sort[0][column]", "period"),
            ("sort[0][direction]", "desc"),
        ])

        # Add optional parameters
        if frequency:
            params.append(("frequency", frequency))
        if start:
            params.append(("start", start))
        if end:
            params.append(("end", end))

        params.extend([
            ("offset", offset),
            ("length", length),
        ])

        # Convert to dict (httpx handles duplicate keys properly)
        params_dict: dict[str, str | int | list[str] | list[int]] = {}
        for key, value in params:  # type: ignore[assignment]
            if key in params_dict:
                # For duplicate keys, convert to list
                current = params_dict[key]
                if not isinstance(current, list):
                    params_dict[key] = [current, value]  # type: ignore[assignment]
                else:
                    current.append(value)  # type: ignore[arg-type]
            else:
                params_dict[key] = value

        response = self._http.get_data_sync(data_route, params_dict)

        return self._parse_data_response(response)

    def get_all_data(
        self,
        route: str,
        facets: dict[str, list[str] | str] | None = None,
        frequency: str | None = None,
        data_fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        max_pages: int | None = None,
    ) -> PaginatedData:
        """Fetch all data with automatic pagination.

        Args:
            route: Data route
            facets: Facet filters
            frequency: Data frequency
            data_fields: Fields to include
            start: Start period
            end: End period
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            PaginatedData with all results combined

        Examples:
            >>> # Fetch all data (auto-pagination)
            >>> all_data = client.get_all_data(
            ...     route="electricity/retail-sales",
            ...     facets={"stateid": ["CA"]},
            ...     frequency="monthly"
            ... )
        """
        all_data: list[DataPointDict] = []
        offset = 0
        pages = 0
        total = 0
        freq = frequency
        date_fmt = None

        while True:
            response = self.get_data(
                route=route,
                facets=facets,
                frequency=frequency,
                data_fields=data_fields,
                start=start,
                end=end,
                offset=offset,
                length=5000,
            )

            all_data.extend(response.data)
            total = response.total
            pages += 1

            if freq is None:
                freq = response.frequency
            if date_fmt is None:
                date_fmt = response.date_format

            # Check if we've fetched everything
            if len(response.data) < 5000 or offset + len(response.data) >= total:
                break

            # Check max pages limit
            if max_pages and pages >= max_pages:
                break

            offset += 5000

        return PaginatedData(
            total=total,
            data=all_data,
            pages_fetched=pages,
            frequency=freq,
            date_format=date_fmt,
        )

    def get_dataframe(
        self,
        route: str,
        facets: dict[str, list[str] | str] | None = None,
        frequency: str | None = None,
        data_fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        auto_paginate: bool = True,
    ) -> pd.DataFrame:
        """Get data as a pandas DataFrame.

        Args:
            route: Data route
            facets: Facet filters
            frequency: Data frequency
            data_fields: Fields to include
            start: Start period
            end: End period
            auto_paginate: Automatically fetch all pages (default: True)

        Returns:
            DataFrame with query results

        Examples:
            >>> df = client.get_dataframe(
            ...     route="electricity/retail-sales",
            ...     facets={"stateid": ["CA", "TX"]},
            ...     frequency="annual"
            ... )
        """
        if auto_paginate:
            paginated = self.get_all_data(
                route=route,
                facets=facets,
                frequency=frequency,
                data_fields=data_fields,
                start=start,
                end=end,
            )
            data = paginated.data
        else:
            response = self.get_data(
                route=route,
                facets=facets,
                frequency=frequency,
                data_fields=data_fields,
                start=start,
                end=end,
            )
            data = response.data

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Convert period to datetime if present
        if "period" in df.columns:
            df["period"] = pd.to_datetime(df["period"], errors="coerce")

        # Convert value columns to numeric
        for col in df.columns:
            if col in ("value", "price"):
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Handle "NA" strings
        df = df.replace("NA", pd.NA)

        return df

    # Async methods

    async def get_routes_async(self, parent_route: str = "") -> list[RouteInfo]:
        """Get available child routes asynchronously.

        Args:
            parent_route: Parent route path

        Returns:
            List of available child routes
        """
        route = parent_route.rstrip("/") if parent_route else ""
        response = await self._http.get_routes_async(route)

        routes_data = response["response"]["routes"]
        return [self._parse_route_info(r) for r in routes_data]

    async def get_data_async(
        self,
        route: str,
        facets: dict[str, list[str] | str] | None = None,
        frequency: str | None = None,
        data_fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        offset: int = 0,
        length: int = 5000,
    ) -> DataResponse:
        """Query data asynchronously.

        Args:
            route: Data route
            facets: Facet filters
            frequency: Data frequency
            data_fields: Fields to include
            start: Start period
            end: End period
            offset: Pagination offset
            length: Number of rows

        Returns:
            DataResponse with results
        """
        data_route = f"{route.rstrip('/')}/data/"

        params: list[tuple[str, str | int]] = []

        if data_fields is None:
            data_fields = ["value"]
        for field in data_fields:
            params.append(("data[]", field))

        if facets:
            for facet_key, values in facets.items():
                if isinstance(values, list):
                    for value in values:
                        params.append((f"facets[{facet_key}][]", str(value)))
                else:
                    params.append((f"facets[{facet_key}][]", str(values)))

        params.extend([
            ("sort[0][column]", "period"),
            ("sort[0][direction]", "desc"),
        ])

        if frequency:
            params.append(("frequency", frequency))
        if start:
            params.append(("start", start))
        if end:
            params.append(("end", end))

        params.extend([
            ("offset", offset),
            ("length", length),
        ])

        # Convert to dict (httpx handles duplicate keys properly)
        params_dict: dict[str, str | int | list[str] | list[int]] = {}
        for key, value in params:  # type: ignore[assignment]
            if key in params_dict:
                # For duplicate keys, convert to list
                current = params_dict[key]
                if not isinstance(current, list):
                    params_dict[key] = [current, value]  # type: ignore[assignment]
                else:
                    current.append(value)  # type: ignore[arg-type]
            else:
                params_dict[key] = value

        response = await self._http.get_data_async(data_route, params_dict)

        return self._parse_data_response(response)

    async def get_dataframe_async(
        self,
        route: str,
        facets: dict[str, list[str] | str] | None = None,
        frequency: str | None = None,
        data_fields: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """Get data as DataFrame asynchronously.

        Args:
            route: Data route
            facets: Facet filters
            frequency: Data frequency
            data_fields: Fields to include
            start: Start period
            end: End period

        Returns:
            DataFrame with results
        """
        response = await self.get_data_async(
            route=route,
            facets=facets,
            frequency=frequency,
            data_fields=data_fields,
            start=start,
            end=end,
        )

        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)

        if "period" in df.columns:
            df["period"] = pd.to_datetime(df["period"], errors="coerce")

        for col in df.columns:
            if col in ("value", "price"):
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.replace("NA", pd.NA)

        return df

    # Helper methods

    def _parse_route_info(self, data: RouteInfoDict) -> RouteInfo:
        """Parse route information from API response."""
        return RouteInfo(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            frequency=data.get("frequency"),
            facets=data.get("facets"),
            data_columns=data.get("data"),
            start_period=data.get("startPeriod"),
            end_period=data.get("endPeriod"),
        )

    def _parse_data_response(self, response: DataResponseDict) -> DataResponse:
        """Parse data response from API."""
        resp_data = response["response"]

        return DataResponse(
            total=resp_data["total"],
            date_format=resp_data.get("dateFormat"),
            frequency=resp_data.get("frequency"),
            data=resp_data["data"],
            description=resp_data.get("description"),
            copyright=resp_data.get("copyright"),
            units=resp_data.get("units"),
        )
