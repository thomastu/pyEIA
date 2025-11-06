"""Base HTTP client for EIA API v2."""

from __future__ import annotations

from urllib.parse import urljoin

import httpx

from eia.config import EIAConfig
from eia.v2.models import DataResponseDict, RoutesResponseDict


class V2HttpClient:
    """HTTP client for EIA API v2 with proper parameter formatting.

    Handles the array notation parameters required by v2 API.
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the v2 HTTP client.

        Args:
            config: EIA API configuration
        """
        self.config = config
        self.base_url = urljoin(config.base_url, "v2/")

    async def get_routes_async(
        self,
        route: str,
        params: dict[str, str | int] | None = None,
    ) -> RoutesResponseDict:
        """Make an async GET request to get routes.

        Args:
            route: API route (e.g., "electricity")
            params: Query parameters (will add api_key automatically)

        Returns:
            Routes response dictionary
        """
        url = urljoin(self.base_url, route.lstrip("/"))
        request_params: dict[str, str | int] = {"api_key": self.config.api_key}

        if params:
            request_params.update(params)

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    def get_routes_sync(
        self,
        route: str,
        params: dict[str, str | int] | None = None,
    ) -> RoutesResponseDict:
        """Make a sync GET request to get routes.

        Args:
            route: API route (e.g., "electricity")
            params: Query parameters (will add api_key automatically)

        Returns:
            Routes response dictionary
        """
        url = urljoin(self.base_url, route.lstrip("/"))
        request_params: dict[str, str | int] = {"api_key": self.config.api_key}

        if params:
            request_params.update(params)

        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    async def get_data_async(
        self,
        route: str,
        params: dict[str, str | int | list[str] | list[int]] | None = None,
    ) -> DataResponseDict:
        """Make an async GET request to get data.

        Args:
            route: API route (e.g., "electricity/retail-sales/data")
            params: Query parameters (will add api_key automatically)

        Returns:
            Data response dictionary
        """
        url = urljoin(self.base_url, route.lstrip("/"))
        request_params: dict[str, str | int | list[str] | list[int]] = {
            "api_key": self.config.api_key
        }

        if params:
            request_params.update(params)

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    def get_data_sync(
        self,
        route: str,
        params: dict[str, str | int | list[str] | list[int]] | None = None,
    ) -> DataResponseDict:
        """Make a sync GET request to get data.

        Args:
            route: API route (e.g., "electricity/retail-sales/data")
            params: Query parameters (will add api_key automatically)

        Returns:
            Data response dictionary
        """
        url = urljoin(self.base_url, route.lstrip("/"))
        request_params: dict[str, str | int | list[str] | list[int]] = {
            "api_key": self.config.api_key
        }

        if params:
            request_params.update(params)

        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.get(url, params=request_params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    def build_facet_params(self, facets: dict[str, list[str] | str]) -> list[tuple[str, str]]:
        """Build facet parameters in v2 array notation format.

        Args:
            facets: Dictionary of facet key to value(s)

        Returns:
            List of (key, value) tuples for httpx params

        Examples:
            >>> client.build_facet_params({"stateid": ["CA", "TX"]})
            [("facets[stateid][]", "CA"), ("facets[stateid][]", "TX")]
        """
        params: list[tuple[str, str]] = []

        for facet_key, values in facets.items():
            if isinstance(values, list):
                for value in values:
                    params.append((f"facets[{facet_key}][]", str(value)))
            else:
                params.append((f"facets[{facet_key}][]", str(values)))

        return params

    def build_data_params(self, data_fields: list[str]) -> list[tuple[str, str]]:
        """Build data field parameters in v2 array notation.

        Args:
            data_fields: List of data fields to request

        Returns:
            List of (key, value) tuples for httpx params

        Examples:
            >>> client.build_data_params(["value", "price"])
            [("data[]", "value"), ("data[]", "price")]
        """
        return [("data[]", field) for field in data_fields]
