#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse, os, sys, shutil
import numpy as np
from pathlib import Path
import xarray as xr
from . import icecalc, interp

def gfs_to_zarr(files, config):
    ########################
    # determine model and variables
    model = 'ice' if 'ice' in files[0].as_posix() else 'ocn'
    var = config['variables'][model]
    # add mask and area if cice output
    var = var + ['tarea', 'tmask'] if model == 'ice' else var
    
    ########################
    # CICE has an IC file under a name
    files.sort()
    f_ic = next(f for f in files if ".ic.nc" in f.name)
    files.remove(f_ic)
    ic_ds = xr.open_dataset(f_ic)[var]

    ########################
    # open files
    print('OPENING FILES')
    ds = xr.open_mfdataset(files, coords='minimal', compat='override', parallel=True, data_vars='all')
    # remove suffixes from variable names
    rename_map = {name: name[:-2] for name in ds.variables if name.endswith('_h') or name.endswith('_d')}
    ds = ds.rename(rename_map)
    ds = ds[var]
    # combine IC ds and forecast ds
    ds = xr.concat([ic_ds,ds], dim='time')
    
    ########################
    # Change Time Dimension to forecast time
    print('ADDING FORECAST TIME to DataSet')
    ds['time_start'] = ds['time'].values[0]
    if ds['time_start'].dt.hour not in [0,6,12,18]:
        t = ds['time'].values[0] + np.timedelta64(3,'h') 
    else:
        t= ds['time'].values[0]
    ds = ds.rename({'time': 'forecast_hour'})
    ds = ds.expand_dims({'time': [np.datetime64(t)]}, axis = 0)
    ds['forecast_time'] = ds['forecast_hour']
    ds['forecast_time'].attrs['long_name'] = 'valid_time_of_forecast'
    ds['forecast_hour'] = (('forecast_hour',) , (ds['forecast_time'].values - np.datetime64(t)) / np.timedelta64(1,'h'))
    ds['forecast_hour'].attrs['long_name'] = 'valid_hour_of_forecast'

    ####################################
    print('Calculating Ice Extent')
    icecalc.extent.ds = ds
    icecalc.extent.var = 'aice'
    ds['extent'] = icecalc.extent.calc()

    ####################################
    # remove time from tarea variable and write
    ds.update({v: ds[v].isel(forecast_hour=0, time=0, drop=True).squeeze() for v in ['tarea', 'tmask']})
    
    ####################################
    if config['parse']['interpolate']['perform']:
        print('Interpolating ice concentrations')
        ds_model = ds.copy()
        ds_model = ds_model[['aice', 'tmask', 'tarea']]
        ds_model = ds_model.rename({'TLAT': 'lat', 'TLON': 'lon'})
        ds_model['mask'] = ds_model['tmask']
        ds_model['aice'] = ds_model['aice'].where(ds_model['mask'] == 1, drop = False)
        for grid in config['parse']['interpolate']['grid_files']:
            DES = xr.open_dataset(grid)
            grid_name = Path(grid).stem
            DES = DES.assign_attrs({'grid' : grid_name }) 
            DAT = interp(ds_model, DES) #, var = var)
            if '25' in grid_name:
                DAT = DAT.rename_dims({'y': 'y' + grid_name, 'x': 'x' + grid_name})
            else:
                DAT = DAT.rename_dims({'yc': 'y' + grid_name, 'xc': 'x' + grid_name})
            new_var = 'aice' + Path(grid).stem
            print('Adding to Dataset', new_var)
            ds['lat' + grid_name ] = (DAT['mask'].dims, DES['lat'].values)
            ds['lon' + grid_name ] = (DAT['mask'].dims, DES['lon'].values)
            ds[new_var] = (DAT['aice'].dims, DAT['aice'].values)
            del DAT
   
    ds = ds.drop_vars('ELON', errors='ignore')
    ds = ds.drop_vars('ELAT', errors='ignore')
    ds = ds.drop_vars('NLON', errors='ignore')
    ds = ds.drop_vars('NLAT', errors='ignore')
    
    ds = ds.expand_dims({"experiment": [e]})
    if os.path.exists(config['zarr_file']):
        ds.to_zarr(config['zarr_file'], append_dim = 'time')
    else:
        ds.to_zarr(config['zarr_file'])
    
    if config['delete_files']:
        for f in files + f_ic:
            f_path = Path(f)
            f_path.unlink(missing_ok=True)
    
    print('PARSE_output.py SUCCESSFUL')

if __name__ == "__main__":
    main()

