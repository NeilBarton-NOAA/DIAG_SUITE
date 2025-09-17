#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
########################
import argparse
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import glob 
import numpy as np
import pandas as pd
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Calculates Integrated Ice Extent Error Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
args = parser.parse_args()
tdir = args.dirs[0]
obs_dir = args.obsdir[0]
obs_calc = args.obs + ['persistence', 'climatology']
var = 'aice'
########################
# get model results
file_search = tdir + '/INTERP*' + var + '_*.nc'
print(file_search)
results_file = tdir + '/iiee.nc'
files = glob.glob(file_search)
files.sort()
poles = ['NH', 'SH']
Force_Calc = True
npb.iceobs.sic.top_dir = obs_dir

########################
# climatology data
if 'climatology' in obs_calc:
    print("Reading Climatology Data for IIEE Calc")
    clim = {}
    for p in poles:
        npb.iceobs.sic.ob_name = 'climatology'
        npb.iceobs.sic.pole = p
        ds = npb.iceobs.sic.grab()
        ds = ds.isel(time = 1)
        ds = ds.drop_vars('time')
        clim[p] = ds

########################
# Loop through data to calc iiee (TODO 24 is likely too hard coded)
if not os.path.exists(results_file) or Force_Calc == False:
    time_data = []
    for i, f in enumerate(files):
        print(f)
        model_ds = xr.open_dataset(f)
        model_ds['forecast_hour'] = model_ds['forecast_hour'].where(model_ds['forecast_hour'] >= 0, 0)
        forecast_days = range(int(model_ds['forecast_hour'].min().values), int(model_ds['forecast_hour'].max().values) + 24, 24)
        model_ds = model_ds.sel(forecast_hour = forecast_days)
        npb.icecalc.iiee.ds_model = model_ds
        ####################################
        # find dates to grab data for analysis  
        dtgs = [pd.to_datetime(model_ds['time']).strftime('%Y%m%d')[0]]
        for fh in range(24, int(model_ds['forecast_hour'].max().values) + 24, 24):
            dtgs.append(pd.to_datetime(model_ds['time'].values[0] + np.timedelta64(fh, 'h')).strftime('%Y%m%d'))
        npb.iceobs.sic.dtg = dtgs
        ####################################
        # get analysis if using for calculation 
        if 'analysis' in obs_calc:
            anal_files = []
            for dtg in dtgs:
                file_search = tdir + '/INTERP*' + var + '_*' + dtg + '00.nc'
                files = glob.glob(file_search)
                if len(files) == 1:
                    anal_files.append(files[0])
            anal = xr.open_mfdataset(anal_files)
            anal = anal.isel(forecast_hour = 0)
            for v in anal.variables:
                if v not in ['aice','time', 'TLAT', 'TLON', 'tarea']:
                    anal = anal.drop_vars(v)
            anal = npb.iceobs.add_forecast_hour(anal, (anal['time'].shape[0] - 1) * 24.0)
            anal = anal.reindex_like(model_ds)
        ####################################
        # now calc iiee
        obs_data = []
        for ob in obs_calc:
            print(ob)
            pole_data = []
            for p in poles:
                if ob in ['persistence', 'analysis']:
                    lat_mask = model_ds['TLAT'] > 0 if p == 'NH' else model_ds['TLAT'] < 0 
                    model = model_ds.copy()
                    model['aice'] = model['aice'].where(lat_mask)
                    npb.icecalc.iiee.ds_model = model
                    if ob == 'persistence':
                        obs = model_ds.isel(forecast_hour = 0 )
                        _, obs['aice'] = xr.broadcast(model_ds['aice'], obs['aice'])
                    elif ob == 'analysis':
                        obs = anal.copy()
                    obs['aice'] = obs['aice'].where(lat_mask)
                    npb.icecalc.iiee.grid = ''
                    npb.icecalc.iiee.ds_obs = obs
                else:
                    npb.iceobs.sic.ob_name = ob
                    if ob == 'climatology':
                        obs = clim[p]
                        time_coords = pd.to_datetime(dtgs, format="%Y%m%d")
                        obs = obs.sel(dayofyear=time_coords.dayofyear).assign_coords(time=time_coords)
                        obs['ice_con'] = (('time','y','x'), obs['ice_con'].values)
                        obs = obs.drop_dims('dayofyear')
                    else:
                        npb.iceobs.sic.pole = p
                        obs = npb.iceobs.sic.grab()
                    obs = npb.iceobs.add_forecast_hour(obs, model_ds['forecast_hour'].max().values)
                    npb.icecalc.iiee.ds_obs = obs
                    npb.icecalc.iiee.grid = obs.grid
                ds = npb.icecalc.iiee.calc()
                pole_data.append(ds.expand_dims({'hemisphere' : [p]}))
            ds = xr.concat(pole_data, dim = 'hemisphere')
            obs_data.append(ds.expand_dims({"obs_type" : [ob]}))
        ds = xr.concat(obs_data, dim = 'obs_type')
        time_data.append(ds)
    ds_time = xr.concat(time_data, dim = 'time')
    ########################
    # Remove some dimensions for variables that don't need them
    for v in ds_time.variables:
        if v[0:3] in ['lat', 'lon']:
            hem = 0 if v[3:5] == 'NH' else 1
            ds_time[v] = ds_time[v].isel(time = 0, hemisphere = hem, obs_type = 0)
        if v != 'diff' and v[0:4] == 'diff':
            ds_time[v] = ds_time[v].sel(hemisphere = v[4:6])
    ds_time['TLAT'] = (model_ds['TLAT'].dims, model_ds['TLAT'].values)
    ds_time['TLON'] = (model_ds['TLON'].dims, model_ds['TLON'].values)
    ds_time.to_netcdf(results_file)
    print("WROTE:", results_file)
