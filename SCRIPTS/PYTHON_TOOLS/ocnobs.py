from datetime import datetime
import copernicusmarine
import glob
import pandas as pd
import xarray as xr
import os
import sys


class cm(object):
    variables = {'sst': {'dsetID':'METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2',
                     'vNames':['analysed_sst']
                    },
             'sss': {'dsetID':'cmems_obs-mob_glo_phy-sss_nrt_multi_P1D',
                     'vNames':['sos', 'dos']
                     }
            }
    @classmethod
    def grab(cls):
        print(cls.dtg)
        dat = copernicusmarine.open_dataset(
                dataset_id = dataset_id,
                variables = ['analysed_sst'],
                start_datetime=f"{start_date.isoformat()}T00:00:00",
                end_datetime=f"{end_date.isoformat()}T23:59:59",
          )
        return dat

