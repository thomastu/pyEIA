# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from eia import browser

if __name__ == '__main__':

    # Collect Data
    APIKEY = "http://www.eia.gov/opendata/register.cfm"
    aeo = browser.AEO(APIKEY)
    datapath = ["2016", # Regex powered browsing!
                ".*", # Go through each scenario
                "Residential Sector",
                "Residential Sector Key Indicators and Consumption"
                ]

    for a in aeo.browse_path(datapath):
        # You can attach meta information to the final output
        # All relevant fields from the Series API are included as well
        meta = {'scenario' : a.scenario, 'foo' : 'bar'}
        a.flag_re('CNSM_NA_RES_NA_OFU_NA_USA_QBTU.A', 'series_id', meta)

    data = a.export()
    # This is a DataFrame whose columns are the output fields of the Series API
    # as well as any additional meta information you may have attached.

    # Get a quick delta between AEO scenarios against the reference case
    data.set_index(['scenario', 'period'], inplace=True)
    reference = data.loc['Reference']
    delta = data.groupby(level = 0, as_index=False).apply(
        lambda x : x['value'] - reference['value']
        ).reset_index(level=0, drop=True)
        )
    data['delta_reference'] = delta
