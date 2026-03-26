from datetime import datetime, timedelta
import copernicusmarine
import glob
import pandas as pd
import xarray as xr
import os
import sys


class cm(object):
    md = {'sst': {'dsetID_NRT':'METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2',
                  'dsetID':'METOFFICE-GLO-SST-L4-REP-OBS-SST',
                 'vNames':['analysed_sst']},
          'sss': {'dsetID_NRT':'cmems_obs-mob_glo_phy-sss_nrt_multi_P1D',
                 'vNames':['sos', 'dos'] }
         }
    @classmethod
    def grab(cls):
        print(cls.var, cls.dtg)
        start_date = cls.dtg
        var_name = cls.md[cls.var]['vNames']
        two_years_ago = datetime.now() - timedelta(days=2*365)
        if datetime.strptime(str(start_date).replace('-',''), '%Y%m%d') < two_years_ago:
            dataset_id = cls.md[cls.var]['dsetID']
        else:
            dataset_id = cls.md[cls.var]['dsetID_NRT']
        dat = copernicusmarine.open_dataset(
                dataset_id = dataset_id,
                variables = var_name,
                start_datetime=start_date+"T00:00:00",
                end_datetime=start_date+"T23:59:59",
          )
        return dat

