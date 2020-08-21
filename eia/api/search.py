import re
import httpx
import pandas as pd

from math import ceil
from typing import List

from .base import BaseQuery


def _quotify(value: str):
    """Add literal quotes around a string to format search terms correctly for the search API.
    """
    value = value.strip('"')
    if not re.match(re.escape(f'^"{value}"$'), value):
        value = f'"{value}"'
    return value


def _make_date_range(date_range: List):
    """Create a SOLR friendly date range from pandas-parseable datetimes.
    """
    assert len(date_range) == 2, "Must specify only a begin and end date."
    begin, end = date_range
    eia_date_fmt = "%Y-%m-%dT%H:%M:%SZ"
    daterange = map(
        lambda x: x.strftime(eia_date_fmt), map(pd.to_datetime, (begin, end))
    )
    return f'[{" TO ".join(daterange)}]'


search_term_cleaners = {
    "series_id": _quotify,
    "name": _quotify,
    "last_updated": _make_date_range,
}
"""Registry of cleaning functions to apply to individual search terms.
"""


class Search(BaseQuery):

    endpoint = "search"

    def __init__(self, apikey: str = None):
        super().__init__(apikey)

    def _send_search_query(
        self, search_term, search_value, num_rows: int = 0, chunksize: int = 5000
    ):
        """
        """
        assert (
            search_term in search_term_cleaners
        ), f"Invalid search term {search_term} not in {', '.join(search_term_cleaners.keys())}"
        # Clean search value
        search_value = search_term_cleaners[search_term](search_value)
        if not num_rows:
            # Retrieve actual rows per page
            response = httpx.get(
                self.url,
                params={
                    "rows_per_page": 1,
                    "page_num": 1,
                    "search_value": search_value,
                    "search_term": search_term,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            num_rows = response.json()["response"]["numFound"]
        pages = ceil(num_rows / chunksize)
        search_results = []
        for page in range(pages):
            offset = page * chunksize
            pagesize = chunksize
            if offset + chunksize > num_rows:
                pagesize = num_rows - offset
            params = {
                "page_num": page,
                "rows_per_page": chunksize,
                "search_term": search_term,
                "search_value": search_value,
            }
            results = httpx.get(self.url, params=params, timeout=10.0)
            results.raise_for_status()
            yield results.json()["response"]["docs"]

    def to_dict(self, *args, **kwargs):
        return list(self._send_search_query(*args, **kwargs))

    def to_dataframe(self, *args, **kwargs):
        return pd.concat((chunk for chunk in self._send_search_query(*args, **kwargs)))
