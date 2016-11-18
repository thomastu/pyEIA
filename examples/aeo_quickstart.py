# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""
Quick start example for using the ``Browser`` client.

Equivalent of clicking through the EIA browser as follows :

1. Clicking all the way to http://www.eia.gov/opendata/qb.php?category=2102635
2. Downloading the series data

This particular example probably contains more boilerplate than is worth it.

See ``examples/aeo_marginal_values.py`` for a slightly more pratical use-case.
"""

from eia import browser

if __name__ == '__main__':
    # YOU WILL NEED TO CHANGE THE APIKEY BELOW
    APIKEY = "http://www.eia.gov/opendata/register.cfm"
    aeo = browser.AEO(APIKEY)

    # Get Residential Sector Key indicators and consumption :
    # http://www.eia.gov/opendata/qb.php?category=2102635
    datapath = ["Annual Energy Outlook 2016",
                "Reference",
                "Residential Sector",
                "Residential Sector Key Indicators and Consumption"
                ]

    for _ in aeo.browse_path(datapath):
        aeo.flag_re(
            'CNSM_NA_RES_NA_OFU_NA_USA_QBTU.A', # Flag a series for export
            'series_id', # indicate which field you're flagging on
            # Attach any meta information associated with business logic
            meta={"scenario" : "Reference", "sector" : "Residential"})

    # Calling the ``export`` method on a ``Browser`` instance returns data as a
    # pandas DataFrame directly from the API using the ``Series`` API endpoint
    data = aeo.export()
    # >>> print(data.head(1))
    #   period     value                   updated   end  \
    # 0   2040  0.004012  2016-06-24T23:58:00-0400  2040
    #
    #                                          description  f  \
    # 0  Data for years 2014 and prior may be model res...  A
    #
    #                                            series_id start  units  \
    # 0  AEO.2016.REF2016.CNSM_NA_RES_NA_OFU_NA_USA_QBTU.A  2013  quads
    #
    #   lastHistoricalPeriod                                           name  \
    # 0                 2014  Residential : Other Fuels, Reference, AEO2016
    #
    #     scenario       sector
    # 0  Reference  Residential
