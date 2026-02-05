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
import shutil
import sys
import xarray as xr

parser = argparse.ArgumentParser( description = "Adds forecast hour to CICE netcdf files")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', \
        help="files to add forecast hour")
parser.add_argument('-m', '--model', action = 'store', nargs = 1, \
        help="variable to keep")
parser.add_argument('-v', '--vars', action = 'store', nargs = '+', \
        help="variable to keep")
parser.add_argument('-o', '--output_file', action = 'store', nargs = 1, \
        help="variable to keep")
args = parser.parse_args()
files = args.files
model = args.model[0]
var = args.vars
f_write = args.output_file[0]

########################
# CICE has an IC file under a name
files.sort()
for f in files:
    if ".ic.nc" in f:
        ic=f
        files.remove(ic)

#######################
if model == 'ice':
    vars_keep = ['tarea', 'tmask']
    var = var + vars_keep
    ########################
    # open IC file
    ic_ds = xr.open_dataset(f)
    ic_ds = ic_ds[var]

########################
# open files
print('OPENING FILES')
ds = xr.open_mfdataset(files, coords='minimal', compat='override', parallel=True)
# edit names with the suffix
rename_map = {name: name[:-2] for name in ds.variables if name.endswith('_h') or name.endswith('_d')}
ds = ds.rename(rename_map)
ds = ds[var]
# concat data sets
ds = xr.concat([ic_ds,ds], dim='time')
print('CREATED XARRAY DataSet')

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

ds = ds.drop_vars('ELON', errors='ignore')
ds = ds.drop_vars('ELAT', errors='ignore')
ds = ds.drop_vars('NLON', errors='ignore')
ds = ds.drop_vars('NLAT', errors='ignore')

print('WRITING file')
encoding = {
    var: {"zlib": True, "complevel": 6}  # Compression level 1–9
    for var in ds.data_vars
}
f_temp = f_write + '_temp'
ds.to_netcdf(f_temp, format="NETCDF4", encoding=encoding)
shutil.move(f_temp, f_write)
print('WROTE:', f_write)
print('PARSE_output.py SUCCESSFUL')
