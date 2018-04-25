# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import pandas as pd
from . import api

class BrowserError(Exception):
    """Generic Browser error."""

class Browser(object):
    """Dataset specific clients."""
    root_category = 371

    def __init__(self, api_key):
        for klass in api.BaseQuery.__subclasses__():
            setattr(self, klass.__name__, klass(api_key))
        self.browse()
        self.flags = {}

    def __repr__(self):
        return "<EIABrowser : {} : Children {} : Series {}>".format(
            self.name, len(self.childcategories), len(self.childseries)
        )

    @property
    def path(self):
        """Yields self until self gets to defined root category.

        First element is the immediate parent, not current category.
        """
        history = [self.category_id] # Remember current state
        yield self
        while int(self.category_id) != int(self.root_category):
            if len(set(history)) != len(history):
                raise BrowserError(
                    ("Recursive history detected.  You have likely run `goto`"
                     "outside the expected scope of category {}"
                    ).format(self.root_category))
            self.goto(self.parent_category_id)
            history.append(self.category_id)
            yield self
        self.goto(history[0]) # return to where we originally were


    @property
    def pathname(self):
        """Get full pathname as a single string."""
        path = map(lambda x: x.name, self.path)
        path.reverse()
        return path

    def browse(self, category_id=None):
        category_ids= self.parse_category_id(category_id)
        if len(category_ids) == 1:
            self.goto(category_ids[0])
        else:
            raise ValueError("Category id too vague, please be more specific.")

    def goto(self, category_id):
        category_id = category_id or self.root_category
        self.parse_category(self.Category.query(category_id))

    def browse_path(self, path, parent=None):
        self.goto(parent) # Implicitly used by parse_category_id
        path = list(path) # We need this to be mutable
        if len(path) == 1: # Base Case
            for node in self.parse_category_id(path[0]): # Goto each option
                self.goto(node)
                yield self # and yield
        else: # Non Base Case
            p = path.pop(0) # Remove the first element
            for node in self.parse_category_id(p): # Goto each option
                for i in self.browse_path(path, node): # Parse remaining path with each option as a parent
                    yield i # and yield recursively until we get to BaseCase

    def search(self, *args, **kwargs):
        return self.Search.query(*args, **kwargs)

    def parse_category(self, category_dict):
        self.name = category_dict["name"]
        self.childcategories = {d['name'] : d['category_id'] \
            for d in category_dict["childcategories"]}
        self.childseries = category_dict["childseries"]
        self.category_id = category_dict['category_id']
        self.parent_category_id = category_dict['parent_category_id']

    def parse_category_id(self, category_id):
        cat = category_id # >'.'<
        categories = []
        if not cat:
            categories = [self.root_category]
        elif category_id in self.childcategories.values():
            categories = [cat]
        elif category_id in self.childcategories:
            categories = [self.childcategories[cat]]
        if categories:
            return categories
        lookups = [
            # lambda x : self.childcategories[x] == cat,
            # lambda x : x == cat,
            lambda x : x.lower().startswith(cat.lower()),
            lambda x : re.search(cat, x, flags=re.I),
            ]
        for l in lookups:
            try:
                matches = filter(l, self.childcategories)
            except re.error:
                continue
            if len(matches) > 0:
                return [self.childcategories[m] for m in matches]

        raise ValueError("category_id argument must be in childcategories.")

    def _flag(self, series, meta=dict()):
        """Internal method to add to mark a series for export with some meta.

        Parameters
        ----------
        series : dict,
            an element of a childseries list from Series.query('...')

        Note
        ----
        Does not validate that series ids are valid.
        """
        meta = self._parse_meta(series, meta)
        self.flags[series['series_id']] = meta

    def flag_re(self, pat, field="name", meta=dict()):
        """
        Parameters
        ----------
        pat : str,
            Regular expression to search for
        field : str, defaults to "name"
            one of "f", "name", "series_id", "units", "updated"
        meta : dict,
            Custom metadata to pass along with data collection.
            Keys must be either str or callable.
            If str, values must be json-serializable.

        Example
        -------
        .. code-block:: python

            def parse_series_name(series_name):
                '''Example callable parsing the series name.

                Returns
                -------
                dict,
                    updates ``meta_dict``
                '''
                return {"meta_1" : series_name.lower(),
                        "meta_2" : series_name.upper()}

            meta = {
                parse_series_name : 'name', # Keys must be a valid fieldname
                "other" : "foo",
                }

            browser_instance.flag_re('capacity', 'name', meta=meta)
        """
        lookup = lambda x : re.search(pat, x[field], flags=re.I)
        results = filter(lookup, self.childseries)
        for r in results:
            self._flag(r, meta)

    def _parse_meta(self, series, meta):
        """Parses a meta-information dictionary with actual values.

        Parameters
        ----------
        meta : dict,
            dict of meta information associated with flagged series_id
        childseries :
            pass
        """
        meta = dict(meta) # Avoid side effects
        funcs = filter(callable, meta) # Get any callables
        valid_names = ["f", "name", "series_id", "units", "updated"]
        for f in funcs:
            fieldname = meta.pop(f)
            if fieldname not in valid_names:
                raise ValueError("Meta dict must take one of {}".format(
                    valid_names))
            m = f(series[fieldname]) # This should return a dictionary
            meta.update(m)
        return meta

    def export(self):
        """Export data as a pandas DataFrame."""
        data = self.Series.query_df(*self.flags.keys())
        output = data.merge(pd.DataFrame(self.flags).T,
            how="outer", left_on = "series_id", right_index=True)
        self.flush()
        return output

    def flush(self):
        self.flags = dict()

class Electricity(Browser):
    """Electricity Data."""

    root_category = 0

class SEDS(Browser):
    """State Energy Data System."""

    root_category = 40203

class Petroleum(Browser):
    """Petroleum Data."""

    root_category = 714755

class NaturalGas(Browser):
    """Natural Gas Data."""

    root_category = 714804

class TotalEnergy(Browser):
    """Total Energy Data."""

    root_category = 711224

class Coal(Browser):
    """Coal Data."""

    root_category = 717234

class STEO(Browser):
    """Short-Term Energy Outlook."""

    root_category = 829714

class AEO(Browser):
    """Annual Energy Outlook."""

    root_category = 964164

    @property
    def scenario(self):
        fullpath = self.pathname
        if len(fullpath) > 2: return fullpath[2]
        else: return 'Not currently within a scenario.'

    @property
    def aeoname(self):
        fullpath = self.pathname
        if len(fullpath) > 1 : return fullpath[1]
        else : return 'Not currently within a scenario'

class CrudeOil(Browser):
    """Crude Oil Imports."""

    root_category = 1292190

class InternationalEnergy(Browser):
    """International Energy Data."""

    root_category = 2134384

class USESOD(Browser):
    """U.S. Electric System Operating Data."""

    root_category = 2123635
