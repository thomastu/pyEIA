# Configuration

You can configure pyeia with your API key either at runtime.

- Declare `EIA_APIKEY="myapikey"` in a `.env` file
- Set an environment variable explicitly, `export EIA_APIKEY="myapikey"`
- If you are using dynaconf, you can include an `[eia]` environment in your `settings.toml` file (or any other configured settings files.)

```toml
[eia]
apikey = "my apikey"
```

# About

The U.S. Energy Information Adminsitration provides an API for access to commonly used datasets for policy makers
and researchers. See the [EIA API documentation](http://www.eia.gov/opendata/commands.cfm) for more information.

Warning : This package is a work in progress!  A substantial update is expected in January 2020, with a published version on PyPi.  The author took a break from this domain area, but is returning!  Hoping to have a similar or identical R interface/API as well, but that may be much farther down the pipeline.

# Basic Usage

Since this package is still under active development, it has not been pushed to PyPi. That said, I believe it is
stable and reliable enough for immediate use.  You can install this via git+https, i.e. :

```bash
pip install pyeia
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

myapikey = ""  # Register here : www.eia.gov/opendata/register.cfm

# Make a call to the Category endpoint
category = api.Category(myapikey)
category.query()

# Make a call to the Series endpoint
series = api.Series(
    "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
    "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
    api_key=myapikey,
)
series.to_dict()  # Export data from its json response
# Make the same query, but get results as a pandas DataFrame
series.to_dataframe()

# Make a call to the Geoset endpoint
geoset = api.Geoset("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL", "USA-MN", api_key=myapikey)
geoset.to_dict()
geoset.query_df()

# Make a call to the SeriesCategory endpoint

seriescategory = api.SeriesCategory(
    "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
    "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
    api_key=myapikey,
)
seriescategory.to_dict()

# Make a call to the Updates endpoint

updates = api.Updates(
    category_id=2102358,
    rows=0,
    firstrow="currently_not_used",
    deep=False,
    api_key=myapikey,
)
updates.to_dict()

# Make a call to the Search endpoint
search = api.Search(api_key=myapikey)

# Make a series_id search
search.to_dict("series_id", "EMI_CO2_COMM_NA_CL_NA_NA_MILLMETNCO2.A", "all")

# Make a name search
search.to_dict("name", "crude oil", 25)

# Make a date-range search
# Dates can be input as a list/tuple of any valid pd.to_datetime argument
search.to_dict("last_updated", ["Dec. 1st, 2014", "06/14/2015 3:45PM"])
```
