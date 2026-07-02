import glob
import os
import numpy as np
import pandas as pd
import xarray as xr

def sfs_to_zarr(e, dir_ymd, config):
    ds_ocn, ds_ice = [], []
    mems = len(glob.glob(dir_ymd + "/00/mem*/products/ocean/netcdf/1p00/"))
    for mem in range(mems):
        print("  member: ", mem)
        #print(e + d)
        # MOM6 output
        d = dir_ymd + "/00/mem" + str(mem).zfill(3) + \
            "/products/ocean/netcdf/1p00/sfs.ocean*monthly_avg*nc"
        files = glob.glob(d)
        if len(files) == 0:
            print('  WARNING: no files found in ', d.split('/00/mem')[0])
            return
        ds = xr.open_mfdataset(files)
        vars_month = ['ocnheat', 'dt20c']
        for v in vars_month:
            d = dir_ymd + "/00/mem" + str(mem).zfill(3) + \
                "/products/ocean/netcdf/1p00/sfs." + v + "*monthly_avg*nc"
            files = glob.glob(d)
            dd = xr.open_mfdataset(files)
            ds[v] = (ds['SST'].dims, dd[v].values)
        time_strings = ds.time.dt.strftime("%Y-%m-01")
        ds = ds.assign_coords(time=pd.to_datetime(time_strings))
        ds_ocn.append(ds.expand_dims({'member' : [mem]}))
        # CICE output
        d = dir_ymd + "/00/mem" + str(mem).zfill(3) + \
            "/products/ice/netcdf/native/sfs.*monthly_avg*nc"
        files = glob.glob(d)
        ds = xr.open_mfdataset(files)
        rename_map = {name: name[:-2] for name in ds.variables if name.endswith('_h') or name.endswith('_d')}
        ds = ds.rename(rename_map)
        ds = ds.assign_coords(time=pd.to_datetime(time_strings))
        ds_ice.append(ds.expand_dims({'member' : [mem]}))
    ds_ocn = xr.concat(ds_ocn, dim = 'member')
    ds_ocn = ds_ocn.expand_dims({'component' : ['ocn']})
    ds_ice = xr.concat(ds_ice, dim = 'member')
    ds_ice = ds_ice.expand_dims({'component' : ['ice']})
    ds = xr.concat([ds_ocn, ds_ice], dim = 'component')
    ds = ds.expand_dims({'experiment': [e] })
    ########################
    # Change Time Dimension to forecast month
    ds['forecast_time'] = ds['time']
    ds['time_start'] = ds['time'].values[0]
    t = ds['time'].values[0]
    ds = ds.rename({'time': 'forecast_month'})
    ds = ds.expand_dims({'time': [np.datetime64(t)]}, axis = 0)
    n_months = (ds['forecast_time'].values.astype("datetime64[M]") - np.datetime64(t).astype("datetime64[M]")).astype(int) + 1
    ds['forecast_month'] = (('forecast_month',), np.asarray(n_months).ravel())
    ds['forecast_time'].attrs['long_name'] = 'valid_month_of_forecast'
    ds['forecast_month'].attrs['long_name'] = 'month_of_forecast'
    # Save Data
    ds = ds.drop_vars('time_bnds', errors='ignore')
    ds = ds.chunk({"time": 24, "experiment": -1, "component": -1, "member": 1, "forecast_month": -1,
                   "z_l": -1, "latitude": 180, "longitude": 360, "nj": 200, "ni": 200,})
    for var in ds.variables:
        if 'chunks' in ds[var].encoding:
            del ds[var].encoding['chunks']
    
    if os.path.exists(config['zarr_file']):
        ds.to_zarr(config['zarr_file'], append_dim = 'time')
    else:
        ds.to_zarr(config['zarr_file'])   

