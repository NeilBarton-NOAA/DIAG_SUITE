# https://data.marine.copernicus.eu/products
# command line 
#   copernicusmarine describe --contains "Extent" --return-fields "dataset_id, dataset_name"
# copernicusmarine describe --product-id $ID_ON_WEBSITE  

import copernicusmarine 
from matplotlib.dates import TH
import pandas as pd
import numpy as np
import xarray as xr
from . import icecalc
from .utils import calc_cell_area

obs_dict = {
            'ice_extent_nh': {
                "dataset_id": "arctic_omi_si_extent_obs",
                "dataset_var": ["siextent"]},
            'ice_extent_sh': {
                "dataset_id": "antarctic_omi_si_extent_obs",
                "dataset_var": ["siextent"]},
            'ice_conc_nh': {
                "dataset_id": "osisaf_obs-si_glo_phy-sic-north_nrt_amsr2_l4_P1D-m",
                "dataset_var": ["ice_conc"]},
            'ice_conc_sh': {
                "dataset_id": "osisaf_obs-si_glo_phy-sic-south_nrt_amsr2_l4_P1D-m",
                "dataset_var": ["ice_conc"]},
            'ice_conc_nrt': {
                "dataset_id": "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
                "dataset_var": ["sea_ice_fraction", "mask"]},
            'SST': {
                "dataset_id": "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
                "dataset_var": ["analysed_sst", "sea_ice_fraction", "mask"]}
           }

cred_file = "~/.copernicusmarine/.copernicusmarine-credentials"

class cm(object):
    forecast_months = 12
    @classmethod
    def grab(cls):
        ############
        start_date = pd.to_datetime(cls.start_dtg).to_pydatetime()
        end_date = pd.to_datetime(cls.end_dtg).to_pydatetime() + pd.DateOffset(months = cls.forecast_months)
        if cm.var in ['ice_extent']:
            # grab extent data
            ds_extent = []
            for hem in ['nh', 'sh']:
                v = 'ice_extent_' + hem
                ds = copernicusmarine.open_dataset(start_datetime=start_date, end_datetime=None,
                    dataset_id=obs_dict[v]['dataset_id'], variables=obs_dict[v]['dataset_var'],
                    credentials_file=cred_file)
                ds[cm.var] = ds['siextent']
                ds = ds.drop_vars('siextent')
                ds_extent.append(ds.expand_dims({'hemisphere': [hem.upper()]}))
            ds_extent = xr.concat(ds_extent, dim='hemisphere')
            # grab concentrationd data and calc extent
            if end_date > pd.Timestamp(ds_extent['time'].max().item()):
                start_date_nrt = pd.Timestamp(ds_extent['time'].max().item()) + pd.DateOffset(months=1)
                ds_extent_nrt = []
                icecalc.extent.var = 'ice_conc'
                for hem in ['nh', 'sh']:
                    v = 'ice_conc_' + hem
                    ds = copernicusmarine.open_dataset(start_datetime=start_date_nrt, end_datetime=end_date,
                         dataset_id=obs_dict[v]['dataset_id'], variables=obs_dict[v]['dataset_var'],
                         credentials_file=cred_file)
                    ds['ice_conc'] = ds['ice_conc'] / 100.0
                    ds['ice_conc'] = ds['ice_conc'].where(ds.latitude <= 88, 1.0)
                    icecalc.extent.ds = ds
                    icecalc.extent.grid_size = calc_cell_area(ds)
                    extent = icecalc.extent.calc()
                    ds = ds.drop_vars('ice_conc')
                    ds = ds.drop_dims(['latitude', 'longitude'])
                    ds[cm.var] = extent
                    ds_extent_nrt.append(ds.expand_dims({'hemisphere': [hem.upper()]}))
                ds_extent_nrt = xr.concat(ds_extent_nrt, dim='hemisphere') 
            ds = xr.concat([ds_extent, ds_extent_nrt], dim='time')
            ds[cm.var] = ds[cm.var] / 1e6 # convert to million km2
            ds[cm.var].attrs['title'] = 'Obs'
        else:
            ds = ds[obs_dict[cm.var]['dataset_var'][0]]
            ds = ds.where(~ds.isnull())
            ds['longitude'] = ds['longitude'] + 180
            ds = ds - 273.15 if cm.var == 'SST' else ds
            ds[cm.var].attrs['title'] = 'L4 OSTIA'
        ##############################################
        # add forecast months
        lead_months = list(range(0, cls.forecast_months))
        ds_list = []
        for m in lead_months:
            # Shift data backwards so that time=t gets the value from time=t+m
            ds_m = ds.shift(time=-m).expand_dims(forecast_month=[m])
            # Attach valid_time coordinate
            valid_times = [pd.Timestamp(t) + pd.DateOffset(months=m) for t in ds['time'].values]
            ds_m = ds_m.assign_coords(valid_time=('time', valid_times))
            ds_list.append(ds_m)
        # Combine along forecast_month
        ds = xr.concat(ds_list, dim='forecast_month')
        return ds[cls.var]