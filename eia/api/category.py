import httpx
import pandas as pd

from .base import BaseQuery


class Category(BaseQuery):
    """The category endpoint serves to traverse relationships or tags of data from the EIA API.
    """

    endpoint = "category"

    def __init__(self, category_id: int = None, apikey: str = None):
        super().__init__(apikey)
        self.category_id = category_id

    def to_dict(self) -> dict:
        data = {**self._params}
        if self.category_id:
            data["category_id"] = self.category_id
        data = httpx.get(self.url, params=data).json()["category"]
        return data

    @property
    def childcategories(self):
        data = self.to_dict()
        return pd.DataFrame(data["childcategories"]).assign(
            parent_category_id=data["category_id"], parent_category_name=data["name"]
        )

    @property
    def childseries(self):
        data = self.to_dict()
        return pd.DataFrame(data["childseries"]).assign(
            category_id=data["category_id"],
            parent_category_id=data["parent_category_id"],
            category_name=data["name"],
        )

    def to_dataframe(self) -> pd.DataFrame:
        """The category endpoint does not contain any series data.
        """
        raise NotImplementedError

