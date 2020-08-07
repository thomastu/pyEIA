import asyncio
import pandas as pd

from .base import BaseQuery


class Relation(BaseQuery):
    """DEPRECATED: This API endpoint does not appear to be accurately documented by EIA.

    It is unclear what this API is supposed to accept or return.

    Example:

        .. code-block::python

            from eia.api import Relation
            Relation("ELEC.GEN.ALL-99.A", "USA-AK",).to_dataframe()
    """

    endpoint = "relation"

    def __init__(self, geoset_id, *regions, api_key: str = None):
        super().__init__(api_key)
        self.geoset_id = geoset_id
        self.regions = list(regions)

    async def _get_data(self):
        data = {"relation_id": self.geoset_id, "region": ",".join(self.regions)}
        return await self._get(data=data)

    def to_dict(self) -> dict:
        """Return the raw geoset response as a python dictionary.
        """
        return asyncio.run(self._get_data())

    def to_dataframe(self, include_metadata: bool = True) -> pd.DataFrame:
        """Return the relation data as a dataframe.
        """
        raise NotImplementedError
