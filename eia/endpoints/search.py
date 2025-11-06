"""Search endpoint implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from eia.client import BaseClient
from eia.config import DEFAULT_SEARCH_ROWS
from eia.models import SearchField, SearchResult

if TYPE_CHECKING:
    from eia.config import EIAConfig


class SearchEndpoint:
    """Endpoint for searching the EIA database.

    Supports searches by series_id, name, or last_updated date.

    Examples:
        >>> from eia import EIAConfig, SearchEndpoint
        >>> config = EIAConfig.from_env()
        >>> endpoint = SearchEndpoint(config)
        >>> # Search by series ID
        >>> results = endpoint.search("series_id", "EMI_CO2*")
        >>> # Search by name
        >>> results = endpoint.search("name", "crude oil")
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the search endpoint.

        Args:
            config: EIA API configuration
        """
        self._client = BaseClient(config, "search")

    async def search_async(
        self,
        search_field: SearchField,
        search_value: str | tuple[str, str],
        rows_per_page: int = DEFAULT_SEARCH_ROWS,
    ) -> list[SearchResult]:
        """Search the EIA database asynchronously.

        Args:
            search_field: Field to search ("series_id", "name", or "last_updated")
            search_value: Value to search for (or tuple of dates for last_updated)
            rows_per_page: Number of results per page (default: 5000)

        Returns:
            List of SearchResult objects

        Examples:
            >>> # Search by series ID
            >>> results = await endpoint.search_async("series_id", "EMI_CO2*")
            >>> # Search by name
            >>> results = await endpoint.search_async("name", "crude oil")
            >>> # Search by date range
            >>> results = await endpoint.search_async(
            ...     "last_updated",
            ...     ("2020-01-01", "2020-12-31")
            ... )
        """
        # Build search term based on field
        if search_field == "last_updated" and isinstance(search_value, tuple):
            start_date, end_date = search_value
            search_term = f"[{start_date} TO {end_date}]"
        else:
            search_term = str(search_value)

        params = {
            "search_term": search_term,
            "search_value": search_field,
            "rows_per_page": rows_per_page,
        }

        response = await self._client._get_async(params=params)
        return self._parse_search(response)

    def search(
        self,
        search_field: SearchField,
        search_value: str | tuple[str, str],
        rows_per_page: int = DEFAULT_SEARCH_ROWS,
    ) -> list[SearchResult]:
        """Search the EIA database synchronously.

        Args:
            search_field: Field to search ("series_id", "name", or "last_updated")
            search_value: Value to search for (or tuple of dates for last_updated)
            rows_per_page: Number of results per page (default: 5000)

        Returns:
            List of SearchResult objects

        Examples:
            >>> # Search by series ID
            >>> results = endpoint.search("series_id", "EMI_CO2*")
            >>> # Search by name
            >>> results = endpoint.search("name", "crude oil")
        """
        # Build search term based on field
        if search_field == "last_updated" and isinstance(search_value, tuple):
            start_date, end_date = search_value
            search_term = f"[{start_date} TO {end_date}]"
        else:
            search_term = str(search_value)

        params = {
            "search_term": search_term,
            "search_value": search_field,
            "rows_per_page": rows_per_page,
        }

        response = self._client._get_sync(params=params)
        return self._parse_search(response)

    def _parse_search(self, response: dict[str, Any]) -> list[SearchResult]:
        """Parse search response."""
        docs = response.get("response", {}).get("docs", [])
        return [
            SearchResult(
                series_id=doc["series_id"],
                name=doc["name"],
                f=doc["f"],
                units=doc["units"],
                last_updated=doc["last_updated"],
                unitsshort=doc.get("unitsshort"),
                description=doc.get("description"),
                geography=doc.get("geography"),
                start=doc.get("start"),
                end=doc.get("end"),
            )
            for doc in docs
        ]

    async def search_dataframe_async(
        self,
        search_field: SearchField,
        search_value: str | tuple[str, str],
        rows_per_page: int = DEFAULT_SEARCH_ROWS,
    ) -> pd.DataFrame:
        """Search and return results as DataFrame asynchronously.

        Args:
            search_field: Field to search
            search_value: Value to search for
            rows_per_page: Number of results per page

        Returns:
            DataFrame with search results

        Examples:
            >>> df = await endpoint.search_dataframe_async("name", "crude oil")
        """
        results = await self.search_async(search_field, search_value, rows_per_page)
        return self._to_dataframe(results)

    def search_dataframe(
        self,
        search_field: SearchField,
        search_value: str | tuple[str, str],
        rows_per_page: int = DEFAULT_SEARCH_ROWS,
    ) -> pd.DataFrame:
        """Search and return results as DataFrame synchronously.

        Args:
            search_field: Field to search
            search_value: Value to search for
            rows_per_page: Number of results per page

        Returns:
            DataFrame with search results

        Examples:
            >>> df = endpoint.search_dataframe("name", "crude oil")
        """
        results = self.search(search_field, search_value, rows_per_page)
        return self._to_dataframe(results)

    def _to_dataframe(self, results: list[SearchResult]) -> pd.DataFrame:
        """Convert search results to DataFrame."""
        if not results:
            return pd.DataFrame()

        data = [
            {
                "series_id": r.series_id,
                "name": r.name,
                "f": r.f,
                "units": r.units,
                "last_updated": r.last_updated,
                "unitsshort": r.unitsshort,
                "description": r.description,
                "geography": r.geography,
                "start": r.start,
                "end": r.end,
            }
            for r in results
        ]
        return pd.DataFrame(data)
