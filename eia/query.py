import requests
import pandas as pd
import numpy as np
import sys
import re
from string import ascii_uppercase as abc

api_key = ''

class baseQuery(object):
    """
    Container class that caches json response for a history on any
    get or post request. 
    """
    def __init__(self):
        """
        Sets initial parameters used for making requests to api.
        self.urlSkeleton should be formatted by child classes 
        """
        self.host = "http://api.eia.gov"
        self.urlSkeleton = '{host}/{queryType}/?api_key={api_key}'
        self.api_key = api_key
        self.request = None
        self.url = None
        self.history = {}

    def make_get_request(self, url):
        """
        Checks to see if desired url endpoint has been seen by self.history.
        If not, a new request is made, its json response is added to 
        self.history.  Returns the instance json response.  
        """
        if url not in self.history:
            r = requests.get(url)
            self.history.update({url : r.json()})
        return self.history[url]

    def make_post_request(self, url, data):
        """
        Simple wrapper around requests.post that returns json.  
        Results are not stored because there is no well defined identifier for a 
        given post request.  Useful for minimizing memory footprint.
        Every get request has an equivalent post request.
        """
        r = requests.post(url, data = data)
        return r.json()

class categoryQuery(baseQuery):

    def __init__(self):
        """
        Makes requests to the category api endpoint.  
        Queries are defined by specifying a category id which returns
        a list of all childcategories and childseries identifiers.

        Pseudo Example : 
        >>> x = categoryQuery()
        >>> x.get(471)
        {"childcategories" : ["Annual Energy Outlook", "State Energy System" ...], }
        """
        super(categoryQuery, self).__init__()
        self.base_url = self.urlSkeleton.format(host = self.host, queryType = 'category', 
            api_key = api_key)

    def make_url(self, category_id):
        url_skeleton = '{base}&category_id={id}'
        url = url_skeleton.format(base = self.base_url, id = category_id)
        self.url = url 
        return url 

    def get(self, identifier):
        url = self.make_url(identifier)
        r = self.make_get_request(url)
        return r

    def post(self, data):
        """
        ---------- Post parameters ----------
        category_id : int or str, integer or integer-as-string that corresponds
            to an EIA category.
        """
        return self.make_post_request(self.base_url, data)

class seriesQuery(baseQuery):

    def __init__(self):
        """
        Creates a query to the series api endpoint.  Returns time series data 
        from requested series ids.  Accepts up to 100 series ids per request. 
        """
        super(categoryQuery, self).__init__()
        base_url = urlSkeleton.format(host = self.host, queryType = 'series', 
            api_key = api_key)

    def make_url(self, series_id):
        """
        Builds the URL endpoint for a series query. 
        """
        url_skelton = '{base}&series_id={id}'
        url = url_skeleton.format(base = self.base_url, id = series_id)
        self.url = url 
        return url

    def get(self, identifier):
        url = self.make_url(identifier)
        r = self.make_get_request(url)
        return r 

    def post(self, data):
        """
        ---------- Post Parameters ----------
        :series_id: str, semi-colon delimited list-as-string of series ids.
        Example : 
        data = {'series_id' : 'series1_id;series_2_id;series_3_id;'}
        self.post(data)
        """
        return self.make_post_request(self.base_url, data)

class searchQuery(baseQuery):

    def __init__(self):
        super(categoryQuery, self).__init__()
        self.base_url = urlSkeleton.format(host=self.host, queryType='search',
            api_key=self.api_key)

    def make_url(self, search_term, search_value, page_num=None, rows_per_page=None):
        url_skeleton= '{base}&search_term={term}&search_value="{value}"'
        url = url_skeleton.format(base=self.base_url,term=search_term,value=search_value)       
        if page_num:
            url += "&page_num={0}".format(str(page_num))
        if rows_per_page : 
            url += "&rows_per_page={0}".format(str(rows_per_page))
        return url 

    def get(self, search_term, search_value, page_num=None, rows_per_page=None):
        url = self.make_url(search_term, search_value, page_num, rows_per_page)
        r = self.make_get_request(url)
        return r 

