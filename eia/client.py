"""Base HTTP client for EIA API with async and sync support."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from eia.config import DEFAULT_OUTPUT_FORMAT, EIAConfig


class BaseClient:
    """Base HTTP client for EIA API endpoints.

    Provides both async and sync methods for making HTTP requests.
    """

    def __init__(self, config: EIAConfig, endpoint: str) -> None:
        """Initialize the client.

        Args:
            config: EIA API configuration
            endpoint: API endpoint path (e.g., "series", "category")
        """
        self.config = config
        self.endpoint = endpoint if endpoint.endswith("/") else f"{endpoint}/"
        self.url = urljoin(config.base_url, self.endpoint)
        self._default_params = {"api_key": config.api_key, "out": DEFAULT_OUTPUT_FORMAT}

    async def _get_async(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an async GET request.

        Args:
            params: Query parameters to include in request

        Returns:
            Response JSON as dictionary
        """
        request_params = {**self._default_params, **(params or {})}
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.get(self.url, params=request_params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    async def _post_async(
        self, data: dict[str, Any] | None = None, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an async POST request.

        Args:
            data: Form data to send in request body
            params: Query parameters to include in request

        Returns:
            Response JSON as dictionary
        """
        request_params = {**self._default_params, **(params or {})}
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(self.url, params=request_params, data=data or {})
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    def _get_sync(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a sync GET request.

        Args:
            params: Query parameters to include in request

        Returns:
            Response JSON as dictionary
        """
        request_params = {**self._default_params, **(params or {})}
        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.get(self.url, params=request_params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    def _post_sync(
        self, data: dict[str, Any] | None = None, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a sync POST request.

        Args:
            data: Form data to send in request body
            params: Query parameters to include in request

        Returns:
            Response JSON as dictionary
        """
        request_params = {**self._default_params, **(params or {})}
        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.post(self.url, params=request_params, data=data or {})
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
