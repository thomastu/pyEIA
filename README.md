# About

WIP

The U.S. Energy Information Adminsitration provides an API for access to commonly used datasets for policy makers
and researchers. See the [EIA API documentation](http://www.eia.gov/opendata/commands.cfm) for more information.

# Basic Usage


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
