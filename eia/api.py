# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import requests
import requests_cache

import pandas as pd
import numpy as np

from urlparse import urljoin
from threading import Thread
from Queue import Queue

try:
    import simplejson as json
except ImportError:
    import json

__all__ = ['Series', 'Geoset', 'Relation', 'Category', 'SeriesCategory', 'Updates', 'Search', 'BaseQuery']

requests_cache.install_cache(backend="memory",
        expire_after = 600,
        ignored_parameters = "api_key")
# Monkey patch requests_cache, Ideally, we can make the backend
# user-configureable

def chunk(l, n):
    """Chunk a list into n parts."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

class BaseQuery(object):

    host = "https://api.eia.gov"
    endpoint = ""

    def __init__(self, api_key, output="json"):
        self.api_key = api_key
        self.default_params = {"api_key" : self.api_key, "out" : output}
        self.base_url = urljoin(self.host, self.endpoint)

    def get(self, **kwargs):
        params = dict(self.default_params)
        params.update(kwargs)
        r = requests.get(self.base_url, params = params)
        r.raise_for_status()
        return r.json()

    def post(self, **data):
        r = requests.post(self.base_url, params=self.default_params, data=data)
        r.raise_for_status()
        return r.json()

    def query(self, *args, **kwargs):
        raise NotImplementedError

class Series(BaseQuery):
    """

    Example
    -------

    .. code-block::python

        from eia.api import Series
        s = Series("MYAPIKEY")
        s.query_df("AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
            "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A")
    """

    endpoint = "series/"

    def parse(self, q, series_id, **kwargs):
        """Thread target to put results on a queue."""
        if len(series_id) + len(self.base_url) >= 1800:
            q.put(self.post(series_id = series_id, **kwargs))
        else:
            q.put(self.get(series_id=series_id, **kwargs))

    def query(self, *series_ids, **kwargs):
        q = Queue()
        threads = []
        for c in chunk(list(set(series_ids)), 100):
            t = Thread(target = self.parse,
                args = (q, ';'.join(c)), kwargs=kwargs)
            t.daemon = True
            t.start()
            threads.append(t)
        map(lambda x : x.join(), threads)
        data = filter(lambda x : 'series' in x, [q.get() for _ in threads])
        return [s for d in data for s in d['series']]

    def query_df(self, *series_ids, **kwargs):
        """Serialize query results to DataFrame."""
        data = self.query(*series_ids, **kwargs)
        o = []
        for d in data:
            df = pd.DataFrame(d.pop('data'), columns=['period', 'value'])
            # This is better for pandas >= 0.16.0
            # o.append(df.assign(**d))
            # However, do it this way for pandas < 0.16.0 support
            for k, v in d.items():
                df[k] = v
            o.append(df)
        return pd.concat(o, ignore_index=True)

class Geoset(BaseQuery):
    """

    Example
    -------

    .. code-block::python

        from eia.api import Geoset
        g = Geoset("MYAPIKEY")
        g.query_df("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL", "USA-MN")
    """

    endpoint = "geoset/"

    def query(self, geoset_id, *regions, **kwargs):
        data = self.get(geoset_id = geoset_id, regions = ','.join(regions),
            **kwargs)
        return data['geoset']

    def query_df(self, geoset_id, *regions, **kwargs):
        data = self.query(geoset_id, *regions, **kwargs)
        o = []
        for series in data.pop('series').values():
            df = pd.DataFrame(series.pop('data'), columns=['period', 'value'])
            for k, v in series.items():
                df[k] = v
            o.append(df)
        df = pd.concat(o, ignore_index=True)
        for k, v in data.items():
            df[k] = v
        return df

class Relation(BaseQuery):
    """Not implemented for now, this does not appear to be a valid endpoint."""
    # endpoint = "relation/"
    pass

class Category(BaseQuery):
    """
    category_id: optional, unique numerical id of the category to fetch.  If missing, the API's root category is fetched.
    """

    endpoint = "category/"

    def query(self, category_id=None, **kwargs):
        return self.get(category_id = category_id, **kwargs)['category']

class SeriesCategory(BaseQuery):

    endpoint = "series/categories/"

    def parse(self, q, series_id, **kwargs):
        """Thread target to put results on a queue."""
        # IMPROVEMENT : calculate dry-run url len
        if len(series_id) + len(self.base_url) >= 1800:
            q.put(self.post(series_id = series_id, **kwargs))
        else:
            q.put(self.get(series_id=series_id, **kwargs))

    def query(self, *series_ids, **kwargs):
        q = Queue()
        threads = []
        for c in chunk(list(set(series_ids)), 100):
            t = Thread(target = self.parse,
                args = (q, ';'.join(c)), kwargs=kwargs)
            t.daemon = True
            t.start()
            threads.append(t)
        map(lambda x : x.join(), threads)
        data = filter(lambda x : 'series_categories' in x, [q.get() for _ in threads])
        return [s for d in data for s in d['series_categories']]

    def query_df(self, *series_ids, **kwargs):
        results = self.query(*series_ids, **kwargs)
        output = pd.DataFrame()
        for r in results:
            df = pd.DataFrame(r['categories'])
            df['series_id'] = r['series_id']
            output = pd.concat([output, df], ignore_index=True)
        return output


class Updates(BaseQuery):

    endpoint = "updates/"

    def parse(self, q, **kwargs):
        q.put(self.get(**kwargs))

    def query(self, category_id = None, rows=50, firstrow=0, deep = False):

        poll = self.get(category_id = category_id,
                     deep=deep,
                     rows=1,
                     firstrow=0) # Check number of available rows
        n = rows or poll['data']['rows_available']
        pages = int(np.ceil(n / 10000.))
        params = {"category_id" : category_id,
                  "deep" : deep,
                  "rows" : 10000}
        q = Queue()
        threads = []
        for page in range(pages):
            page_params = dict(params)
            first = page*10000
            page_params.update({"firstrow" : first})
            if first + 10000 > rows:
                rows = rows - first
                page_params.update({"rows" : rows})
            t = Thread(target = self.parse,
                args = (q, ), kwargs=page_params)
            t.daemon = True
            t.start()
            threads.append(t)
        map(lambda x : x.join(), threads)
        data = filter(
            lambda x : ('updates' in x and isinstance(x['updates'][0], dict)),
            [q.get() for _ in threads])
        return [s for d in data for s in d['updates']]

    def query_df(self, *args, **kwargs):
        return pd.DataFrame(self.query(*args, **kwargs))


class Search(BaseQuery):

    endpoint = "search/"

    def query(self, search_term, search_value,
              rows_per_page=10, page_num=1, **kwargs):
        """
        search_term : str,
            one of ["series_id", "name", "last_updated"]

        search_value : str or iterable,
            - last_updated : "[YYYY-MM-DDTHH:MM:SSZ TO YYYY-MM-DDTHH:MM:SSZ]"
                Acceptable inputs:
                - ["12/01/2014", "12/01/2015 12:15:00"]
                - ["Dec. 1, 2014", "June 2nd, 2015"]
                - ["12/01/2014", "Nov 12th, 2016 1:15 PM"]
                In general, any other 2 valid ``pd.to_datetime`` arguments
                Otherwise, must be of the following form :
                - "[2015-01-01T00:00:00Z TO 2015-01-01T23:59:59Z]"
            - series_id, name : '"value"'
                e.g. '"PET.MB"', '"crude oil"' (note the double quote)
                Though handling is also provided for native python strings :
                e.g. "PET.MB" will be internally cleaned as '"PET.MB"'
            Some handling is provided for formating
        """
        t, v = self.clean_search_params(search_term, search_value)
        if (rows_per_page == 0) or (rows_per_page == 'all'):
            r = self.get(search_term = t, search_value = v, page_num=1, rows_per_page = 1, **kwargs)
            total = r['response']['numFound']
            # Chunk by 5000's for reliability/reasonable speed
            pages = int(np.ceil(total/5000.))
            results = []
            for page in range(0, pages):
                rows = 5000
                first = page*5000
                if first + 5000 > total:
                    rows = total - first
                try:
                    r = self.get(search_term = t, search_value = v, page_num=page, rows_per_page = rows, **kwargs)
                    results.extend(r['response']['docs'])
                except Exception as e:
                    print(e)
                    print(r)
                    print(page)
                    print(rows)
                    print(first)
        else: # limit search results, paginate elsewhere
            r = self.get(search_term = t, search_value = v, page_num=page_num, rows_per_page = rows_per_page, **kwargs)
            results = r['response']['docs']
        return results

    def clean_search_params(self, search_term, search_value):
        t, v = search_term, search_value # Alias for convenience
        assert t in ["series_id", "name", "last_updated"], "Invalid search term"

        if t in ["series_id", "name"]:
            if not re.match(re.escape('^"{}"$'.format(v.strip('"'))), v):
                v = '"{}"'.format(search_value)
        else: # search_term == "last_updated"
            if len(list(v)) == 2: # Assume it's a tuple, list, or iterable
                daterange = map(pd.to_datetime, list(v))
                strfdaterange = map(
                    lambda x : x.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    daterange)
                v = "[{}]".format(" TO ".join(strfdaterange))
            # else : assume user has read documentation and is feeding in
            # solr friendly query
        return t, v

    def query_df(self, *args, **kwargs):
        return pd.DataFrame(self.query(*args, **kwargs))
