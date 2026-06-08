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
path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.getenv("PYTHON_TOOLS")) if 'slurm' in path else sys.path.append(path)
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Calculates Integrated Ice Extent Error Between Runs and Observations")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', help="model files to calc iiee")
parser.add_argument('-o', '--output_file', action = 'store', nargs = 1, help="output file to save")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', help="directory to observations to use")
args = parser.parse_args()
files = args.files
output_file = args.output_file[0]
obs_calc = args.obs + ['persistence', 'analysis']
var = 'aice'
EXP = output_file[0:-3].split('_')[-1]
poles = ['NH', 'SH']

########################
# Loop through data to calc iiee (TODO 24 hour forecasts is likely too hard coded)
if not os.path.exists(output_file) or npb.utils.FORCE_CALC():
    ########################
    # climatology data
    print("Reading Climatology Data for IIEE Calc")
    clim = {}
    npb.iceobs.sic.directory = [item for item in obs_calc if 'climatology' in item][0]
    for p in poles:
        npb.iceobs.sic.pole = p
        ds = npb.iceobs.sic.grab()
        ds = ds.isel(time = 1)
        ds = ds.drop_vars('time')
        clim[p] = ds
    ########################
    # loop through files
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
        anal_files = []
        f_prefix = f.split('/')[-1]
        f_prefix = f_prefix.split(f_prefix[-13::])[0]
        for dtg in dtgs:
            file_search = os.path.dirname(f) + '/' + f_prefix + dtg + '*.nc'
            anal_f = glob.glob(file_search)
            if len(anal_f) == 1:
                anal_files.append(anal_f[0])
        anal = xr.open_mfdataset(anal_files)
        anal = anal.isel(forecast_hour = 0)
        anal = anal.drop_vars('forecast_hour')
        anal = anal[['aice','time', 'lat', 'lon', 'tarea']]
        anal = npb.utils.add_forecast_hour(anal, (anal['time'].shape[0] - 1) * 24.0)
        anal = anal.reindex_like(model_ds)
        ####################################
        # now calc iiee
        obs_data = []
        for ob in obs_calc:
            print(os.path.basename(ob))
            pole_data = []
            for p in poles:
                ########################
                # comes from model data
                if ob in ['persistence', 'analysis']:
                    lat_mask = model_ds['lat'] > 0 if p == 'NH' else model_ds['lat'] < 0 
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
                    npb.iceobs.sic.directory = ob
                    if 'climatology' in ob:
                        obs = clim[p]
                        time_coords = pd.to_datetime(dtgs, format="%Y%m%d")
                        obs = obs.sel(dayofyear=time_coords.dayofyear).assign_coords(time=time_coords)
                        obs['ice_con'] = (('time','y','x'), obs['ice_con'].values)
                        obs = obs.drop_dims('dayofyear')
                    else:
                        npb.iceobs.sic.pole = p
                        obs = npb.iceobs.sic.grab()
                    obs = npb.utils.add_forecast_hour(obs, model_ds['forecast_hour'].max().values)
                    npb.icecalc.iiee.ds_obs = obs
                    npb.icecalc.iiee.grid = obs.grid
                ds = npb.icecalc.iiee.calc()
                pole_data.append(ds.expand_dims({'pole' : [p]}))
            ds = xr.concat(pole_data, dim = 'pole')
            obs_data.append(ds.expand_dims({"obs_type" : [ob]}))
        ds = xr.concat(obs_data, dim = 'obs_type')
        time_data.append(ds)
    ds_time = xr.concat(time_data, dim = 'time')
    ########################
    # Remove some dimensions for variables that don't need them
    for v in ds_time.variables:
        if v[0:3] in ['lat', 'lon'] and v not in ['lat', 'lon']:
            hem = 0 if v[3:5] == 'NH' else 1
            ds_time[v] = ds_time[v].isel(time = 0, pole = hem, obs_type = 0)
        if v != 'diff' and v[0:4] == 'diff':
            ds_time[v] = ds_time[v].sel(pole = v[4:6])
    ds_time.attrs['experiment_name'] = EXP
    default_compression = {"zlib": True, "complevel": 6}
    compress_encoding = {var_name: default_compression for var_name in ds_time.data_vars}
    ds_time.to_netcdf(output_file)
    print("WROTE:", output_file)
print('CALC_iiee.py SUCCESSFUL')

