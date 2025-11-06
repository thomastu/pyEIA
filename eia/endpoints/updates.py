"""Updates endpoint implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pandas as pd

from eia.client import BaseClient
from eia.config import MAX_UPDATES_ROWS
from eia.models import UpdateResult

if TYPE_CHECKING:
    from eia.config import EIAConfig


class UpdatesEndpoint:
    """Endpoint for polling recent data updates.

    Retrieves information about recently updated series.

    Examples:
        >>> from eia import EIAConfig, UpdatesEndpoint
        >>> config = EIAConfig.from_env()
        >>> endpoint = UpdatesEndpoint(config)
        >>> updates = endpoint.get_updates(category_id=371, rows=100)
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the updates endpoint.

        Args:
            config: EIA API configuration
        """
        self._client = BaseClient(config, "updates")

    async def get_updates_async(
        self,
        category_id: int | None = None,
        rows: int = 50,
        firstrow: int = 0,
        deep: bool = False,
    ) -> list[UpdateResult]:
        """Retrieve recent updates asynchronously.

        Args:
            category_id: Category to check for updates (None for all)
            rows: Number of results to retrieve (max 10000)
            firstrow: Starting row for pagination
            deep: Include updates from subcategories

        Returns:
            List of UpdateResult objects

        Examples:
            >>> updates = await endpoint.get_updates_async(category_id=371, rows=100)
        """
        if rows > MAX_UPDATES_ROWS:
            rows = MAX_UPDATES_ROWS

        params = {
            "rows": rows,
            "firstrow": firstrow,
            "deep": str(deep).lower(),
        }

        if category_id is not None:
            params["category_id"] = category_id

        response = await self._client._get_async(params=params)
        return self._parse_updates(response)

    def get_updates(
        self,
        category_id: int | None = None,
        rows: int = 50,
        firstrow: int = 0,
        deep: bool = False,
    ) -> list[UpdateResult]:
        """Retrieve recent updates synchronously.

        Args:
            category_id: Category to check for updates (None for all)
            rows: Number of results to retrieve (max 10000)
            firstrow: Starting row for pagination
            deep: Include updates from subcategories

        Returns:
            List of UpdateResult objects

        Examples:
            >>> updates = endpoint.get_updates(category_id=371, rows=100)
        """
        if rows > MAX_UPDATES_ROWS:
            rows = MAX_UPDATES_ROWS

        params = {
            "rows": rows,
            "firstrow": firstrow,
            "deep": str(deep).lower(),
        }

        if category_id is not None:
            params["category_id"] = category_id

        response = self._client._get_sync(params=params)
        return self._parse_updates(response)

    def _parse_updates(self, response: dict[str, Any]) -> list[UpdateResult]:
        """Parse updates response."""
        updates_list = response.get("updates", [])
        return [
            UpdateResult(
                series_id=item["series_id"],
                name=item["name"],
                f=item["f"],
                units=item["units"],
                updated=item["updated"],
                unitsshort=item.get("unitsshort"),
            )
            for item in updates_list
        ]

    async def get_all_updates_async(
        self,
        category_id: int | None = None,
        deep: bool = False,
        throttle_delay: float = 0.25,
    ) -> list[UpdateResult]:
        """Retrieve all updates using pagination asynchronously.

        Args:
            category_id: Category to check for updates (None for all)
            deep: Include updates from subcategories
            throttle_delay: Delay between requests in seconds (default: 0.25 for 4 req/sec)

        Returns:
            List of all UpdateResult objects

        Examples:
            >>> all_updates = await endpoint.get_all_updates_async(category_id=371)
        """
        all_results: list[UpdateResult] = []
        firstrow = 0

        while True:
            results = await self.get_updates_async(
                category_id=category_id,
                rows=MAX_UPDATES_ROWS,
                firstrow=firstrow,
                deep=deep,
            )

            if not results:
                break

            all_results.extend(results)
            firstrow += len(results)

            # Throttle to respect rate limits (4 requests/second)
            if len(results) == MAX_UPDATES_ROWS:
                await asyncio.sleep(throttle_delay)
            else:
                break  # Last page

        return all_results

    def get_all_updates(
        self,
        category_id: int | None = None,
        deep: bool = False,
    ) -> list[UpdateResult]:
        """Retrieve all updates using pagination synchronously.

        Args:
            category_id: Category to check for updates (None for all)
            deep: Include updates from subcategories

        Returns:
            List of all UpdateResult objects

        Examples:
            >>> all_updates = endpoint.get_all_updates(category_id=371)
        """
        all_results: list[UpdateResult] = []
        firstrow = 0

        while True:
            results = self.get_updates(
                category_id=category_id,
                rows=MAX_UPDATES_ROWS,
                firstrow=firstrow,
                deep=deep,
            )

            if not results:
                break

            all_results.extend(results)
            firstrow += len(results)

            if len(results) < MAX_UPDATES_ROWS:
                break  # Last page

        return all_results

    async def get_dataframe_async(
        self,
        category_id: int | None = None,
        rows: int = 50,
        firstrow: int = 0,
        deep: bool = False,
    ) -> pd.DataFrame:
        """Retrieve updates as DataFrame asynchronously.

        Args:
            category_id: Category to check for updates
            rows: Number of results to retrieve
            firstrow: Starting row for pagination
            deep: Include updates from subcategories

        Returns:
            DataFrame with update information

        Examples:
            >>> df = await endpoint.get_dataframe_async(category_id=371)
        """
        updates = await self.get_updates_async(category_id, rows, firstrow, deep)
        return self._to_dataframe(updates)

    def get_dataframe(
        self,
        category_id: int | None = None,
        rows: int = 50,
        firstrow: int = 0,
        deep: bool = False,
    ) -> pd.DataFrame:
        """Retrieve updates as DataFrame synchronously.

        Args:
            category_id: Category to check for updates
            rows: Number of results to retrieve
            firstrow: Starting row for pagination
            deep: Include updates from subcategories

        Returns:
            DataFrame with update information

        Examples:
            >>> df = endpoint.get_dataframe(category_id=371)
        """
        updates = self.get_updates(category_id, rows, firstrow, deep)
        return self._to_dataframe(updates)

    def _to_dataframe(self, updates: list[UpdateResult]) -> pd.DataFrame:
        """Convert updates to DataFrame."""
        if not updates:
            return pd.DataFrame()

        data = [
            {
                "series_id": u.series_id,
                "name": u.name,
                "f": u.f,
                "units": u.units,
                "updated": u.updated,
                "unitsshort": u.unitsshort,
            }
            for u in updates
        ]
        return pd.DataFrame(data)
