"""Series endpoint implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pandas as pd

from eia.client import BaseClient
from eia.config import MAX_SERIES_PER_REQUEST
from eia.models import SeriesData
from eia.utils import chunk_iterable

if TYPE_CHECKING:
    from eia.config import EIAConfig


class SeriesEndpoint:
    """Endpoint for retrieving time series data from the EIA API.

    Supports batch requests for multiple series with automatic chunking.

    Examples:
        >>> from eia import EIAConfig, SeriesEndpoint
        >>> config = EIAConfig.from_env()
        >>> endpoint = SeriesEndpoint(config)
        >>> # Async usage
        >>> data = await endpoint.get_series_async(
        ...     "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A"
        ... )
        >>> # Sync usage
        >>> data = endpoint.get_series("AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A")
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the series endpoint.

        Args:
            config: EIA API configuration
        """
        self._client = BaseClient(config, "series")

    async def get_series_async(self, *series_ids: str) -> list[SeriesData]:
        """Retrieve one or more series asynchronously.

        Args:
            series_ids: One or more series IDs to retrieve

        Returns:
            List of SeriesData objects

        Examples:
            >>> data = await endpoint.get_series_async(
            ...     "series1",
            ...     "series2",
            ... )
        """
        if not series_ids:
            return []

        # Filter out None/empty values and chunk into batches
        filtered_ids = [sid for sid in series_ids if sid]
        chunks = list(chunk_iterable(filtered_ids, MAX_SERIES_PER_REQUEST))

        # Create coroutines for each chunk
        tasks = [self._fetch_batch_async(chunk) for chunk in chunks]

        # Execute batches with throttling (max 5 concurrent)
        results: list[SeriesData] = []
        for i in range(0, len(tasks), 5):
            batch_tasks = tasks[i : i + 5]
            batch_results = await asyncio.gather(*batch_tasks)
            for chunk_results in batch_results:
                results.extend(chunk_results)

        return results

    async def _fetch_batch_async(self, series_ids: list[str]) -> list[SeriesData]:
        """Fetch a batch of series (internal helper)."""
        series_id_param = ";".join(series_ids)
        response = await self._client._post_async(data={"series_id": series_id_param})

        series_list = response.get("series", [])
        return [self._parse_series(s) for s in series_list]

    def get_series(self, *series_ids: str) -> list[SeriesData]:
        """Retrieve one or more series synchronously.

        Args:
            series_ids: One or more series IDs to retrieve

        Returns:
            List of SeriesData objects

        Examples:
            >>> data = endpoint.get_series("series1", "series2")
        """
        if not series_ids:
            return []

        # Filter out None/empty values and chunk into batches
        filtered_ids = [sid for sid in series_ids if sid]
        chunks = list(chunk_iterable(filtered_ids, MAX_SERIES_PER_REQUEST))

        # Fetch all chunks
        results: list[SeriesData] = []
        for chunk in chunks:
            chunk_results = self._fetch_batch_sync(chunk)
            results.extend(chunk_results)

        return results

    def _fetch_batch_sync(self, series_ids: list[str]) -> list[SeriesData]:
        """Fetch a batch of series synchronously (internal helper)."""
        series_id_param = ";".join(series_ids)
        response = self._client._post_sync(data={"series_id": series_id_param})

        series_list = response.get("series", [])
        return [self._parse_series(s) for s in series_list]

    def _parse_series(self, raw: dict[str, Any]) -> SeriesData:
        """Parse raw series data into SeriesData model."""
        return SeriesData(
            series_id=raw["series_id"],
            name=raw["name"],
            units=raw["units"],
            f=raw["f"],
            data=[(item[0], item[1]) for item in raw.get("data", [])],
            description=raw.get("description"),
            copyright=raw.get("copyright"),
            source=raw.get("source"),
            iso3166=raw.get("iso3166"),
            geography=raw.get("geography"),
            start=raw.get("start"),
            end=raw.get("end"),
            last_updated=raw.get("last_updated"),
            unitsshort=raw.get("unitsshort"),
            latestPeriod=raw.get("latestPeriod"),
        )

    async def get_dataframe_async(
        self, *series_ids: str, include_metadata: bool = True
    ) -> pd.DataFrame:
        """Retrieve series data as a pandas DataFrame asynchronously.

        Args:
            series_ids: One or more series IDs to retrieve
            include_metadata: Include series metadata columns (default: True)

        Returns:
            DataFrame with time series data and optional metadata

        Examples:
            >>> df = await endpoint.get_dataframe_async("series1", "series2")
        """
        series_data = await self.get_series_async(*series_ids)
        return self._to_dataframe(series_data, include_metadata)

    def get_dataframe(self, *series_ids: str, include_metadata: bool = True) -> pd.DataFrame:
        """Retrieve series data as a pandas DataFrame synchronously.

        Args:
            series_ids: One or more series IDs to retrieve
            include_metadata: Include series metadata columns (default: True)

        Returns:
            DataFrame with time series data and optional metadata

        Examples:
            >>> df = endpoint.get_dataframe("series1", "series2")
        """
        series_data = self.get_series(*series_ids)
        return self._to_dataframe(series_data, include_metadata)

    def _to_dataframe(
        self, series_data: list[SeriesData], include_metadata: bool
    ) -> pd.DataFrame:
        """Convert series data to DataFrame."""
        if not series_data:
            return pd.DataFrame()

        dataframes = []
        for series in series_data:
            df = pd.DataFrame(series.data, columns=["period", "value"])

            if include_metadata:
                df = df.assign(
                    series_id=series.series_id,
                    name=series.name,
                    units=series.units,
                    f=series.f,
                    description=series.description,
                    copyright=series.copyright,
                    source=series.source,
                    iso3166=series.iso3166,
                    geography=series.geography,
                    start=series.start,
                    end=series.end,
                    last_updated=series.last_updated,
                    unitsshort=series.unitsshort,
                )

            dataframes.append(df)

        return pd.concat(dataframes, ignore_index=True)
