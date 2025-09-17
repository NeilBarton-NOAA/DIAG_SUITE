#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
# check platform
import platform
########################
import argparse
import calendar
import os
import glob
import numpy as np
import pandas as pd
import sys
import xarray as xr

parser = argparse.ArgumentParser( description = "Compares Sea Ice Extent Between Runs and Observations")
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to extract")
parser.add_argument('-e', '--exp', action = 'store', nargs = 1, \
        help="experiment name")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
args = parser.parse_args()
var = args.var[0]
exp = args.exp[0]
tdir = args.dirs[0]
vars_keep = ['tarea', 'tmask']
########################
# open files, ensemble support is needed
# ic file
f = glob.glob(tdir + '/*ic.nc')[0]
ic_ds = xr.open_dataset(f)
ic_ds = ic_ds.drop_vars([v for v in ic_ds.data_vars if v not in [var] + vars_keep])
# forecast files
files = sorted(glob.glob(tdir + '/*.nc'))
files = [f for f in files if "ic.nc" not in f]
ds = xr.open_mfdataset(files, coords='minimal', compat='override', parallel=True)
ds = ds.drop_vars([v for v in ds.data_vars if v not in [var] + vars_keep])
# concat data sets
ds = xr.concat([ic_ds,ds], dim='time')

########################
# Change Time Dimension to forecast time
# add time dimension and add tau (forecast hour) variable
ds['time_start'] = ds['time'].values[0]
if ds['time_start'].dt.hour not in [0,6,12,18]:
    t = ds['time'].values[0] + np.timedelta64(3,'h') 
else:
    t = ds['time_start'].values[0]
ds = ds.rename({'time': 'forecast_hour'})
ds = ds.expand_dims({'time': [np.datetime64(t)]}, axis = 0)
ds['forecast_time'] = ds['forecast_hour']
ds['forecast_time'].attrs['long_name'] = 'valid_time_of_forecast'
ds['forecast_hour'] = (('forecast_hour',) , (ds['forecast_time'].values - np.datetime64(t)) / np.timedelta64(1,'h'))
ds['forecast_hour'].attrs['long_name'] = 'valid_hour_of_forecast'
#ds['forecast_hour'] = ds['forecast_hour'].where(ds['forecast_hour'] >= 0, 0)
####################################
# remove time from tarea variable and write
for v in vars_keep:
    ds[v] = ds[v].isel(forecast_hour = 1)
    ds[v] = ds[v].squeeze()
v = var.split('_')[0]
ds = ds.rename({var : v })
f_write = tdir.split(exp)[0] + exp + '/' + v + '_' + ds['time'].dt.strftime('%Y%m%d%H').values[0] + '.nc'
encoding = {
    var: {"zlib": True, "complevel": 4}  # Compression level 1–9
    for var in ds.data_vars
}
ds.to_netcdf(f_write, format="NETCDF4", encoding=encoding)
print('WROTE:', f_write)

