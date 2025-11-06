"""Geoset endpoint implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from eia.client import BaseClient
from eia.models import GeosetRegion

if TYPE_CHECKING:
    from eia.config import EIAConfig


class GeosetEndpoint:
    """Endpoint for retrieving geographic series collections.

    Geosets provide time series data broken down by geographic regions.

    Examples:
        >>> from eia import EIAConfig, GeosetEndpoint
        >>> config = EIAConfig.from_env()
        >>> endpoint = GeosetEndpoint(config)
        >>> data = endpoint.get_geoset("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL")
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the geoset endpoint.

        Args:
            config: EIA API configuration
        """
        self._client = BaseClient(config, "geoset")

    async def get_geoset_async(self, geoset_id: str, *regions: str) -> list[GeosetRegion]:
        """Retrieve geoset data asynchronously.

        Args:
            geoset_id: The geoset identifier
            regions: One or more region identifiers

        Returns:
            List of GeosetRegion objects

        Examples:
            >>> data = await endpoint.get_geoset_async(
            ...     "ELEC.GEN.ALL-99.A",
            ...     "USA-CA",
            ...     "USA-FL",
            ... )
        """
        if not regions:
            regions = ()

        params = {
            "geoset_id": geoset_id,
            "regions": ",".join(regions) if regions else "",
        }

        response = await self._client._get_async(params=params)
        return self._parse_geoset(response)

    def get_geoset(self, geoset_id: str, *regions: str) -> list[GeosetRegion]:
        """Retrieve geoset data synchronously.

        Args:
            geoset_id: The geoset identifier
            regions: One or more region identifiers

        Returns:
            List of GeosetRegion objects

        Examples:
            >>> data = endpoint.get_geoset("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL")
        """
        if not regions:
            regions = ()

        params = {
            "geoset_id": geoset_id,
            "regions": ",".join(regions) if regions else "",
        }

        response = self._client._get_sync(params=params)
        return self._parse_geoset(response)

    def _parse_geoset(self, response: dict[str, Any]) -> list[GeosetRegion]:
        """Parse geoset response."""
        geoset_list = response.get("geoset", [])
        return [
            GeosetRegion(
                geoset_id=item["geoset_id"],
                region_id=item.get("region_id", ""),
                name=item["name"],
                data=[(point[0], point[1]) for point in item.get("data", [])],
                f=item["f"],
                units=item["units"],
                unitsshort=item.get("unitsshort"),
            )
            for item in geoset_list
        ]

    async def get_dataframe_async(self, geoset_id: str, *regions: str) -> pd.DataFrame:
        """Retrieve geoset data as DataFrame asynchronously.

        Args:
            geoset_id: The geoset identifier
            regions: One or more region identifiers

        Returns:
            DataFrame with geoset data

        Examples:
            >>> df = await endpoint.get_dataframe_async("ELEC.GEN.ALL-99.A", "USA-CA")
        """
        geoset_data = await self.get_geoset_async(geoset_id, *regions)
        return self._to_dataframe(geoset_data)

    def get_dataframe(self, geoset_id: str, *regions: str) -> pd.DataFrame:
        """Retrieve geoset data as DataFrame synchronously.

        Args:
            geoset_id: The geoset identifier
            regions: One or more region identifiers

        Returns:
            DataFrame with geoset data

        Examples:
            >>> df = endpoint.get_dataframe("ELEC.GEN.ALL-99.A", "USA-CA")
        """
        geoset_data = self.get_geoset(geoset_id, *regions)
        return self._to_dataframe(geoset_data)

    def _to_dataframe(self, geoset_data: list[GeosetRegion]) -> pd.DataFrame:
        """Convert geoset data to DataFrame."""
        if not geoset_data:
            return pd.DataFrame()

        dataframes = []
        for region in geoset_data:
            df = pd.DataFrame(region.data, columns=["period", "value"])
            df = df.assign(
                geoset_id=region.geoset_id,
                region_id=region.region_id,
                name=region.name,
                f=region.f,
                units=region.units,
                unitsshort=region.unitsshort,
            )
            dataframes.append(df)

        return pd.concat(dataframes, ignore_index=True)
