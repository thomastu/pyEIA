# About

The U.S. Energy Information Adminsitration provides an API for access to commonly used datasets for policy makers
and researchers. See the [EIA API documentation](http://www.eia.gov/opendata/commands.cfm) for more information.

Warning : This package is a work in progress!  A substantial update is expected in January 2020, with a published version on PyPi.  The author took a break from this domain area, but is returning!  Hoping to have a similar or identical R interface/API as well, but that may be much farther down the pipeline.

# Basic Usage

Since this package is still under active development, it has not been pushed to PyPi. That said, I believe it is
stable and reliable enough for immediate use.  You can install this via git+https, i.e. :

```bash
pip install git+https://github.com/thomastu/pyEIA.git
pip show pyeia
```

There are two main strategies for interacting with this package.

## EIA Browser

[EIA provides a web-based data browser](http://www.eia.gov/opendata/qb.cfm)
Since most interactions for discovering data via the API will likely occur
through this browser, this motivated a programmatic version.

The general strategy is to traverse a datapath or multiple datapaths, and
when you arrive to the desired node, you flag one or more dataseries.  
There is also the ability to add in meta information as you flag a dataseries.

Running the `export` method on a Browser object will make a request to the
`Series` API to collect data you've flagged.

There's currently a separate class for each dataset which is mostly syntactic.
In the future, there will likely be methods and visualizations builtin that are
specific to the datasets described at the root category level from EIA.

1. [Browser Quickstart to Collect AEO data](examples/aeo_quickstart.py)
2. [Computing Marginal Values for AEO data](examples/aeo_marginal_values.py)

## Direct API usage

Each endpoint has a corresponding class in `eia.api`.  Every class has a `query` method that makes a call to EIA.
The returned result is always the response body.  Metadata about the request is dropped.  The `Series` and `Geoset`
classes have a special `query_df` method since their response bodies have a naturally tabular schema.


```python
from eia import api

myapikey = "" # Register here : www.eia.gov/opendata/register.cfm

# Make a call to the Category endpoint
category = api.Category(myapikey)
category.query()

# Make a call to the Series endpoint
series = api.Series(myapikey)
series.query("AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
            "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A")
# Make the same query, but get results as a pandas DataFrame
series.query_df("AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
            "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A")

# Make a call to the Geoset endpoint

geoset = api.Geoset(myapikey)
geoset.query("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL", "USA-MN")
geoset.query_df("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL", "USA-MN")

# Make a call to the SeriesCategory endpoint

seriescategory = api.SeriesCategory(myapikey)
seriescategory.query("AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
            "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A")

# Make a call to the Updates endpoint

updates = api.Updates(myapikey)
updates.query(category_id=2102358, rows=0, firstrow="currently_not_used", deep=False)

# Make a call to the Search endpoint
search = api.Search(myapikey)

# Make a series_id search
search.query("series_id", "EMI_CO2_COMM_NA_CL_NA_NA_MILLMETNCO2.A", "all")

# Make a name search
search.query("name", "crude oil", 25)

# Make a date-range search
# Dates can be input as a list/tuple of any valid pd.to_datetime argument
search.query("last_updated", ["Dec. 1st, 2014", "06/14/2015 3:45PM"])
```

# PENDING

This is a work in progress that has been motivated by data collection issues
that I happen to encounter.  It is pending tests, better documentation and a few
important optimizations for robust general purpose use.

This is recommended for people needing to quickly collect specific datasets off
of EIA.  The internal API presented is subject to change.  

- test coverage
- native plotting for common relationships between datasets
- performance improvements
- configuration options (e.g. modifying the requests_cache backend)
