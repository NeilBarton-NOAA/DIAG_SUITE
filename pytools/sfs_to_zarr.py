import glob
import os
import numpy as np
import shutil
import pandas as pd
import xarray as xr
from . import utils
import dask
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="dask")
warnings.filterwarnings("ignore", category=UserWarning, module="xarray")
warnings.filterwarnings("ignore", message=".*PerformanceWarning.*")
warnings.filterwarnings("ignore", message=".*Slicing is producing a large chunk.*")
warnings.filterwarnings("ignore", message=".*Increasing number of chunks.*")
# Configure Dask to handle large chunk slicing automatically
dask.config.set({"array.slicing.split_large_chunks": True})

def sfs_to_zarr(e, dir_ymd, config):
    ds_ocn, ds_ice = [], []
    if config["n_members"] == 'all':
        mems = len(glob.glob(dir_ymd + "/00/mem*/products/ocean/netcdf/1p00/"))
    else:
        mems = config["n_members"]
    if mems == 0: 
        print('No files found for', dir_ymd)
        return
    for mem in range(mems):
        print("  member: ", mem)
        # MOM6 output
        d = dir_ymd + "/00/mem" + str(mem).zfill(3) + \
            "/products/ocean/netcdf/1p00/sfs.ocean*monthly_avg*nc"
        files = glob.glob(d)
        print(files)
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
        ds = utils.ds_addvar(ds, 'ice_extent')
        ds = utils.ds_addvar(ds, 'ice_volume')
        ds = utils.ds_addvar(ds, 'snow_volume')
        ds_ice.append(ds.expand_dims({'member' : [mem]}))
    ds_ocn = xr.concat(ds_ocn, dim = 'member')
    ds_ocn = ds_ocn.expand_dims({'component' : ['ocn']})
    ds_ice = xr.concat(ds_ice, dim = 'member')
    ds_ice = ds_ice.expand_dims({'component' : ['ice']})
    ds_ocn = ds_ocn.chunk({'member': -1})
    ds_ice = ds_ice.chunk({'member': -1})
    ds = xr.concat([ds_ocn, ds_ice], dim = 'component', data_vars = 'minimal', coords='minimal', compat='override')
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
    # Get Ready to Save Data
    zarr_chunks = {"time": 1, "experiment": -1, "component": -1, "member": 1, "forecast_month": -1, 
                   "z_l": -1, "latitude": -1, "longitude": -1, "nj": -1, "ni": -1}
    ds = ds.drop_vars('time_bnds', errors='ignore')
    ds = ds.chunk(zarr_chunks)
    for slim_v in ['cell_area', 'tmask']: 
        ds[slim_v] = ds[slim_v].isel(time = 0, experiment = 0, member = 0, forecast_month = 0, 
                                     drop = True).sel(component = 'ice')
    for var in ds.variables: ds[var].encoding.clear()
    # Save Data
    if not os.path.exists(config['zarr_file']):
        ds = ds.chunk(zarr_chunks)
        ds.to_zarr(config['zarr_file'], consolidated=True)
    else:
        ds_existing = xr.open_zarr(config['zarr_file'])
        existing_mems = ds_existing.coords['member'].values
        incoming_mems = ds['member'].values
        ds_existing.close()
        all_mems = np.union1d(existing_mems, incoming_mems)
        if len(incoming_mems) == len(existing_mems):
            ds.to_zarr(config['zarr_file'], append_dim = 'time', consolidated=True)
        elif len(incoming_mems) < len(existing_mems):
            print("latest ds has fewer members than expected")
            ds = ds.reindex(member=existing_mems)
            ds = ds.chunk(zarr_chunks)
            ds.to_zarr(config['zarr_file'], append_dim='time', consolidated=True)
        else:
            print("latest ds has more members than expected")
            ds_existing_reindexed = xr.open_zarr(config['zarr_file']).chunk(zarr_chunks).reindex(member=all_mems)
            ds_reindexed = ds.chunk(zarr_chunks).reindex(member=all_mems)
            combined_ds = xr.concat([ds_existing_reindexed, ds_reindexed], dim='time')  
            for slim_v in ['cell_area', 'tmask']: 
                combined_ds[slim_v] = combined_ds[slim_v].isel(time = 0)
            for var in combined_ds.variables:
                combined_ds[var].encoding.clear()
            # Write lazily to temporary store
            tmp_zarr = str(config['zarr_file']) + ".tmp"
            if os.path.exists(tmp_zarr): shutil.rmtree(tmp_zarr)
            combined_ds.to_zarr(tmp_zarr, mode='w', consolidated=True)
            shutil.rmtree(config['zarr_file'])
            os.rename(tmp_zarr, config['zarr_file'])

