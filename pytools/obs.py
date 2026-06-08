# https://data.marine.copernicus.eu/products
# command line copernicusmarine describe --contains "Extent" --return-fields "dataset_id, dataset_name"

import copernicusmarine 
import pandas as pd
import numpy as np
import xarray as xr
obs_dict = {
            'ice_extent': {
                "dataset_id": "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
                "dataset_var": ["sea_ice_fraction", "mask"]},
            'SST': {
                "dataset_id": "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
                "dataset_var": ["analysed_sst", "sea_ice_fraction", "mask"]}
           }


class cm(object):
    @classmethod
    def grab(cls):
        ############
        start_date = pd.to_datetime(cls.start_dtg).to_pydatetime()
        end_date = pd.to_datetime(cls.end_dtg).to_pydatetime()
        ############
        ds = copernicusmarine.open_dataset(
                start_datetime = start_date,
                end_datetime = end_date,
                dataset_id = obs_dict[cm.var]['dataset_id'],
                variables = obs_dict[cm.var]['dataset_var'],
                credentials_file = "~/.copernicusmarine/.copernicusmarine-credentials"
                )
        ds = ds.resample(time='ME').mean()
        ds['time'] = pd.to_datetime(ds.time.values).strftime('%Y-%m-15').astype('datetime64[ns]')
        if cm.var in ['ice_extent']:
            R = 6371000  # Radius of Earth in meters
            d_lat = np.radians(0.05) # 1 degree in radians
            d_lon = np.radians(0.05) # 1 degree in radians
            area = (R**2) * d_lat * d_lon * np.cos(np.radians(ds['latitude']))
            sic, ds['cell_area'] = xr.broadcast(ds['sea_ice_fraction'], area)
            NH = ds['cell_area'].where((ds['latitude'] > 20) & (ds['sea_ice_fraction'] >= 0.15))\
                                .sum(dim = ['latitude', 'longitude']) / 1e12
            SH = ds['cell_area'].where((ds['latitude'] < -20) & (ds['sea_ice_fraction'] >= 0.15))\
                                .sum(dim = ['latitude', 'longitude']) / 1e12
            NH = NH.expand_dims({'hemisphere': ['NH']})
            SH = SH.expand_dims({'hemisphere': ['SH']})
            ds['ice_extent'] = xr.concat([NH, SH], dim = 'hemisphere')
            ds = ds['ice_extent']
        else:
            ds = ds[obs_dict[cm.var]['dataset_var'][0]]
            ds = ds.where(~ds.isnull())
            ds['longitude'] = ds['longitude'] + 180
            ds = ds - 273.15 if cm.var == 'SST' else ds
            #import matplotlib.pyplot as plt
            #plt.imshow(ds[0], origin='lower'); plt.colorbar(); plt.show(); exit(1)
        ds.attrs['title'] = 'L4 OSTIA'
        return ds


