import asyncio
import pandas as pd

from typing import List

from .base import BaseQuery, yield_chunks


class Series(BaseQuery):
    """Retrieve one or more series from the series API.

    Example:

        .. code-block::python

            from eia.api import Series
            
            S = Series(
                "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A", 
                "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
            )
            S.to_dataframe()
    """

    endpoint = "series"

    def __init__(self, *series_ids: str, apikey: str = None):
        super().__init__(apikey)
        self.series_ids = [
            ";".join(chunk) for chunk in yield_chunks(filter(None, series_ids), 100)
        ]

    async def _get_data(self):
        """Send a request for each batch of series ids and await their results.
        """
        coros = []
        results = []
        for series_ids in self.series_ids:
            response = self._post(data={"series_id": series_ids})
            coros.append(response)
            if len(coros) == 5:  # throttle at 5
                _ = await asyncio.gather(*coros)
                results.extend(_)
                coros = []  # Reset accumulator
        if coros:
            results.extend(await asyncio.gather(*coros))

        return filter(None, results)

    async def parse(self, key) -> List[dict]:
        """
        Collect one dict per series and drop request metadata.
        """
        data = await self._get_data()
        output = []
        for group in data:
            for series in group.get(key, []):
                output.append(series)
        return output

    def to_dict(self) -> List[dict]:
        """Return the input series as a list of dictionaries.
        """
        return asyncio.run(self.parse(key="series"))

    def to_dataframe(self, include_metadata: bool = True) -> pd.DataFrame:
        """Return the input series as a dataframe.
        """
        # Get all our data first with async
        # Note that all our pandas work will tax CPU so we wouldn't expect any
        # performance gains from doing the data parsing as a callback
        records = self.to_dict()
        data = []
        for series in records:
            df = pd.DataFrame(series.pop("data"), columns=["period", "value"])
            if include_metadata:
                df = df.assign(**series)
            data.append(df)
        return pd.concat(data, ignore_index=True)

