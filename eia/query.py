import requests
import pandas as pd
import numpy as np
import sys
import re
from string import ascii_uppercase as abc

api_key = ''

class BaseQuery:
    """
    Query containing methods for making requests to the EIA API.
    """

    host = "http://api.eia.gov"
    base_skeleton = '{host}/{queryType}/?api_key={api_key}'
    api_key = api_key

    def __init__(self):
        """
        """
        self.request = None
        self.url = None
        self.history = {}

    def make_get_request(self, url):
        if url not in self.history:
            r = requests.get(url)
            self.history.update({url : r.json()})
        return self.history.get(url)

    def make_post_request(self, url, data):
        r = requests.post(url, data = data)
        return r.json()

class CategoryQuery(BaseQuery):

    base_url = base_skeleton.format(host = host, queryType = 'category', 
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
        return self.make_post_request(self.base_url, data)

class SeriesQuery(BaseQuery):

    base_url = base_skeleton.format(host = host, queryType = 'series', 
        api_key = api_key)

    def make_url(self, series_id):
        url_skelton = '{base}&series_id={id}'
        url = url_skeleton.format(base = self.base_url, id = series_id)
        self.url = url 
        return url

    def get(self, identifier):
        url = self.make_url(identifier)
        r = self.make_get_request(url)
        return r 

    def post(self, data):
        return self.make_post_request(self.base_url, data)
