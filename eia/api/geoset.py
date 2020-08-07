import asyncio
import pandas as pd

from .base import BaseQuery


class Geoset(BaseQuery):
    """Endpoint to collect a set of series belonging to a geoset in a list of valid regions.

    Example:

        .. code-block:: python

            from eia.api import Geoset
            Geoset("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL", "USA-MN").to_dataframe()
    """

    endpoint = "geoset"

    def __init__(self, geoset_id: str, *regions: str, api_key: str = None):
        super().__init__(api_key)
        self.geoset_id = geoset_id
        self.regions = list(regions)

    async def _get_data(self):
        """Send a request for each batch of series ids and await their results.
        """
        data = {"geoset_id": self.geoset_id, "regions": ",".join(self.regions)}
        return await self._get(data=data)

    def to_dict(self) -> dict:
        """Return the raw geoset response as a python dictionary.
        """
        return asyncio.run(self._get_data())["geoset"]

    def to_dataframe(self, include_metadata: bool = True) -> pd.DataFrame:
        """Return the geoset data as a dataframe.

        Note:
            
            Only metadata at the series level can be dropped. Geoset-level metadata
            will always be included.
        """
        data = asyncio.run(self._get_data())["geoset"]
        series_data = data.pop("series")
        geoset_meta = dict(data)
        accumulator = []
        for series in series_data.values():
            df = pd.DataFrame(series.pop("data"), columns=["period", "value"])
            if include_metadata:
                df = df.assign(**series)
            accumulator.append(df)
        df = pd.concat(accumulator, ignore_index=True)
        # Reattach the geoset-level data.
        df = df.assign(**geoset_meta)
        return df

