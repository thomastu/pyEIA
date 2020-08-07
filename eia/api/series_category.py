import asyncio
import pandas as pd

from typing import List

from .base import BaseQuery, yield_chunks
from .series import Series


class SeriesCategory(Series):
    """
    The SeriesCategory endpoint returns all categories that a given series id belongs to.

    Example:

        .. code-block::python

            from eia.api import SeriesCategory

            SeriesCategory(
                "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
                "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A"
            ).to_dataframe()

    Note:
        Many times, there will be multiple paths to get to a single category.
        A single child series can have multiple nearly identical parents that
        differ on how a user has traversed to that category. This could be useful for
        collecting all relevant "tags" or descriptive data on a series.
    """

    endpoint = "series/categories"

    def to_dict(self) -> List[dict]:
        """Return the input series as a list of dictionaries.
        """
        return asyncio.run(self.parse(key="series_categories"))

    def to_dataframe(self) -> pd.DataFrame:
        """
        Return all category ids and category names associated with each series id as a DataFrame.
        """
        data = self.to_dict()
        return pd.concat(
            [
                pd.DataFrame(series["categories"]).assign(series_id=series["series_id"])
                for series in data
            ],
            ignore_index=True,
        )
