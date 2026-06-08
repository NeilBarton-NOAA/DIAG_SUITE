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
p = os.getenv("pydiag_tools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pydiag_tools as diag_tools

def main():
    ########################
    # set up arguments
    parser = argparse.ArgumentParser( description = "osi_saf file to calc extent and make files smaller")
    parser.add_argument('-f', '--files', action = 'store', nargs = '+', \
        help="files to add forecast hour")
    args = parser.parse_args()
    files = args.files
    
    ########################
    # 
    for f in files:
        print(f)
        ds = xr.open_mfdataset(f) #, data_vars='all', compat='no_conflicts', join='outer', coords='different') 
        ds['time'] = ds['time'] - np.timedelta64(12, 'h')
        grid = int(abs(ds['xc'][1] - ds['xc'][0]))
        ds['ice_con'] = (ds['ice_conc'].dims, ds['ice_conc'].values / 100.0)
        land_mask = ds['ice_con'][0]
        land_mask = land_mask.where(land_mask.isnull(), 1, drop=False)
        land_mask = land_mask.fillna(0)
        ds['land_mask'] = (land_mask.dims, land_mask.values)    
        ds['ice_con'] = ds['ice_con'].where(land_mask == 1, drop = False)
        pole='SH'
        ds = ds.assign_attrs({'grid' : pole + str(grid)})
        ds = ds.assign_attrs({'name': 'osi_saf'})
        ds = ds.assign_attrs({'file_name': f }) 
        vars_keep = set(['ice_con', 'land_mask', 'lat', 'lon', 'time', 'Polar_Stereographic_Grid'])
        vars_to_drop = [key for key in ds.data_vars if key not in vars_keep]
        ds = ds.drop_vars(vars_to_drop)
        diag_tools.icecalc.extent.ds = ds
        diag_tools.icecalc.extent.var = 'ice_con'
        ds['extent'] = diag_tools.icecalc.extent.calc()
        ds = ds.assign_attrs({'name': 'osi_saf'})
        ds = ds.assign_attrs({'pole': pole})
        ds = ds.assign_attrs({'grid_area' : grid**2.})
        ds = ds.assign_attrs({'pole': pole})
        diag_tools.utils.ds_to_netcdf(ds, 'test.nc')
    
    #model = 'ice' if 'ice' in files[0] else 'ocn'
    #var = config['variables'][model]
    ## add mask and area if cice output
    #var = var + ['tarea', 'tmask'] if model == 'ice' else var
    
    ########################
    # CICE has an IC file under a name
    #files.sort()
    #f_ic = next(f for f in files if ".ic.nc" in f)
    #files.remove(f_ic)
    #ic_ds = xr.open_dataset(f_ic)[var]
#
    ########################
    # open files
    #print('OPENING FILES')
    #ds = xr.open_mfdataset(files, coords='minimal', compat='override', parallel=True, data_vars='all')
    ## remove suffixes from variable names
    #rename_map = {name: name[:-2] for name in ds.variables if name.endswith('_h') or name.endswith('_d')}
    #ds = ds.rename(rename_map)
    #ds = ds[var]
    ## combine IC ds and forecast ds
    #ds = xr.concat([ic_ds,ds], dim='time')
    
    ########################
    # Change Time Dimension to forecast time
    #print('ADDING FORECAST TIME to DataSet')
    #ds['time_start'] = ds['time'].values[0]
    #if ds['time_start'].dt.hour not in [0,6,12,18]:
    #    t = ds['time'].values[0] + np.timedelta64(3,'h') 
    #else:
    #    t = ds['time_start'].values[0]
    #ds = ds.rename({'time': 'forecast_hour'})
    #ds = ds.expand_dims({'time': [np.datetime64(t)]}, axis = 0)
    #ds['forecast_time'] = ds['forecast_hour']
    #ds['forecast_time'].attrs['long_name'] = 'valid_time_of_forecast'
    #ds['forecast_hour'] = (('forecast_hour',) , (ds['forecast_time'].values - np.datetime64(t)) / np.timedelta64(1,'h'))
    #ds['forecast_hour'].attrs['long_name'] = 'valid_hour_of_forecast'

    ####################################
    #print('Calculating Ice Extent')

    
    
    
    print('PARSE_osi_saft.py SUCCESSFUL')

if __name__ == "__main__":
    main()

