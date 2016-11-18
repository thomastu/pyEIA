# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from eia import browser

"""
One common operation between different branches of what is essentially the
same data is to look strictly at "marginal" values.  In this example, we pull
all residential sector usage of "Other Fuels" from every AEO 2016 scenario.

From there, it's trivial to create a marginal dataset using the pandas library.
"""

from eia import browser

if __name__ == '__main__':
    # YOU WILL NEED TO CHANGE THE APIKEY BELOW
    APIKEY = "http://www.eia.gov/opendata/register.cfm"
    aeo = browser.AEO(APIKEY)

    # Get Residential Sector Key indicators and consumption :
    # http://www.eia.gov/opendata/qb.php?category=2102635
    datapath = ["Annual Energy Outlook 2016",
                ".*", # Datapaths are Regex powered
                "Residential Sector",
                "Residential Sector Key Indicators and Consumption"
                ]

    for _ in aeo.browse_path(datapath):
        # This loop iterates through every possible endpoint following
        # the regular expression path above.  i.e.
        # AEO 2016 > {AEO SCENARIO} > ... > Residential Sector Key Indicators
        meta = {
            # Browser subclasses contain special attributes specific to the
            # EIA defined datasets they represent.  For AEO, we always have
            # some notion of a "scenario".
            "scenario" : aeo.scenario,
            "sector" : "Residential"
            }
        aeo.flag_re(
            'CNSM_NA_RES_NA_OFU_NA_USA_QBTU.A', # Flag a series for export
            'series_id', # indicate which field you're flagging on
            meta)  # Attach any meta information associated with business logic

    # Calling the export method on a browser instance retrieves data using the
    # series API.  Per the docs, every 100 series are exported using a single
    # request to save on API calls.
    data = aeo.export()

    # Now we can compute a quick marginal value against the "Reference Case"
    data.set_index(['scenario', 'period'], inplace=True)
    reference = data.loc['Reference']
    delta = data.groupby(level = 0, as_index=False).apply(
        lambda x : x['value'] - reference['value']
        ).reset_index(level=0, drop=True)
    data['delta_reference'] = delta
