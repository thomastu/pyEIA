"""SeriesCategory endpoint implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from eia.client import BaseClient
from eia.config import MAX_SERIES_PER_REQUEST
from eia.models import SeriesCategoryResult
from eia.utils import chunk_iterable

if TYPE_CHECKING:
    from eia.config import EIAConfig


class SeriesCategoryEndpoint:
    """Endpoint for finding categories associated with series.

    Retrieves all category IDs that a series belongs to.

    Examples:
        >>> from eia import EIAConfig, SeriesCategoryEndpoint
        >>> config = EIAConfig.from_env()
        >>> endpoint = SeriesCategoryEndpoint(config)
        >>> results = endpoint.get_series_categories("series1", "series2")
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the series category endpoint.

        Args:
            config: EIA API configuration
        """
        self._client = BaseClient(config, "series/categories")

    async def get_series_categories_async(
        self, *series_ids: str
    ) -> list[SeriesCategoryResult]:
        """Retrieve categories for series asynchronously.

        Args:
            series_ids: One or more series IDs

        Returns:
            List of SeriesCategoryResult objects

        Examples:
            >>> results = await endpoint.get_series_categories_async("series1", "series2")
        """
        if not series_ids:
            return []

        # Filter and chunk series IDs
        filtered_ids = [sid for sid in series_ids if sid]
        chunks = list(chunk_iterable(filtered_ids, MAX_SERIES_PER_REQUEST))

        # Fetch all chunks
        all_results: list[SeriesCategoryResult] = []
        for chunk in chunks:
            chunk_results = await self._fetch_batch_async(chunk)
            all_results.extend(chunk_results)

        return all_results

    async def _fetch_batch_async(self, series_ids: list[str]) -> list[SeriesCategoryResult]:
        """Fetch a batch of series categories (internal helper)."""
        series_id_param = ";".join(series_ids)
        response = await self._client._post_async(data={"series_id": series_id_param})
        return self._parse_series_categories(response)

    def get_series_categories(self, *series_ids: str) -> list[SeriesCategoryResult]:
        """Retrieve categories for series synchronously.

        Args:
            series_ids: One or more series IDs

        Returns:
            List of SeriesCategoryResult objects

        Examples:
            >>> results = endpoint.get_series_categories("series1", "series2")
        """
        if not series_ids:
            return []

        # Filter and chunk series IDs
        filtered_ids = [sid for sid in series_ids if sid]
        chunks = list(chunk_iterable(filtered_ids, MAX_SERIES_PER_REQUEST))

        # Fetch all chunks
        all_results: list[SeriesCategoryResult] = []
        for chunk in chunks:
            chunk_results = self._fetch_batch_sync(chunk)
            all_results.extend(chunk_results)

        return all_results

    def _fetch_batch_sync(self, series_ids: list[str]) -> list[SeriesCategoryResult]:
        """Fetch a batch of series categories synchronously (internal helper)."""
        series_id_param = ";".join(series_ids)
        response = self._client._post_sync(data={"series_id": series_id_param})
        return self._parse_series_categories(response)

    def _parse_series_categories(self, response: dict[str, Any]) -> list[SeriesCategoryResult]:
        """Parse series categories response."""
        series_categories = response.get("series_categories", [])
        return [
            SeriesCategoryResult(
                series_id=item["series_id"],
                categories=item.get("categories", []),
            )
            for item in series_categories
        ]

    async def get_dataframe_async(self, *series_ids: str) -> pd.DataFrame:
        """Retrieve series categories as DataFrame asynchronously.

        Args:
            series_ids: One or more series IDs

        Returns:
            DataFrame with series and their category IDs

        Examples:
            >>> df = await endpoint.get_dataframe_async("series1", "series2")
        """
        results = await self.get_series_categories_async(*series_ids)
        return self._to_dataframe(results)

    def get_dataframe(self, *series_ids: str) -> pd.DataFrame:
        """Retrieve series categories as DataFrame synchronously.

        Args:
            series_ids: One or more series IDs

        Returns:
            DataFrame with series and their category IDs

        Examples:
            >>> df = endpoint.get_dataframe("series1", "series2")
        """
        results = self.get_series_categories(*series_ids)
        return self._to_dataframe(results)

    def _to_dataframe(self, results: list[SeriesCategoryResult]) -> pd.DataFrame:
        """Convert series categories to DataFrame."""
        if not results:
            return pd.DataFrame()

        # Expand categories into separate rows
        data = []
        for result in results:
            if result.categories:
                for category_id in result.categories:
                    data.append({"series_id": result.series_id, "category_id": category_id})
            else:
                data.append({"series_id": result.series_id, "category_id": None})

        return pd.DataFrame(data)
