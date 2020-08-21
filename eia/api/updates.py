"""
Note:
    This API might be under-documented because it doesn't seem all that useful in reality.
"""
import asyncio
import pandas as pd

from math import ceil

from .base import BaseQuery


class Updates(BaseQuery):
    """
    Used to poll for the most recent update date of all series belonging to a category.
    Results are by default ordered by the most recent update.

    Example:

        .. code-block:: python

            from eia.api import Updates
            Updates(category_id=711230).to_dict()
    """

    endpoint = "updates"

    def __init__(
        self, category_id: int = None, deep: bool = False, api_key: str = None,
    ):
        super().__init__(api_key)
        self.category_id = category_id
        self.deep = deep

    async def _get_data(self, rows: int = None):
        default_params = {
            "category_id": self.category_id,
            "deep": self.deep,
        }
        max_rows = 10000  # The Updates API will allow up to 10000 rows for each request
        # Figure out how many rows we want to get
        total_rows = (
            await self._get(data={**default_params, "rows": 1, "firstrow": 0})
        )["data"]["rows_available"]
        if rows:
            n_rows = min(rows, total_rows)
        else:
            n_rows = total_rows

        n_pages = int(ceil(n_rows / max_rows))

        coros = []
        for page in range(n_pages):
            page_nrows = min(
                n_rows, max_rows
            )  # Number of rows to collect for this page
            firstrow = page * page_nrows  # 0-indexed means this starts at 0
            page_params = {**default_params, "firstrow": firstrow}
            if firstrow + page_nrows > n_rows:
                page_nrows = n_rows - firstrow
            response = self._get(data={**page_params, "rows": page_nrows})
            coros.append(response)
            coros.append(
                asyncio.sleep(0.25)
            )  # Rate limit ourselves to 4 requests/second
        return await asyncio.gather(*coros)

    async def parse(self, rows: int = None):
        updates = []
        data = await self._get_data(rows)
        for response in filter(None, data):
            for datum in response.get("updates"):
                updates.append(datum)
        return updates

    def to_dict(self, rows: int = None):
        return asyncio.run(self.parse(rows))

    def to_dataframe(self, rows: int = None):
        return pd.DataFrame(self.to_dict(rows))
