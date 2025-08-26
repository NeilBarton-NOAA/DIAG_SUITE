#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
# check platform
import platform
if 'hfe' in platform.uname()[1]:
    print('only run on an interactive node')
    print(platform.uname()[1])
    exit(1)
########################
import argparse
import calendar
import numpy as np
import os
import sys
import pandas as pd
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Plot Integrated Ice Extent Error Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-e', '--exps', action = 'store', nargs = '+', \
        help="experiments to calc ice extent. Also name of directory under -d")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
save_dir = args.figuredir[0]
obs = args.obs
var = 'aice'
os.makedirs(save_dir, exist_ok=True)
####################################
# grab ice extent from models
DATS = []
for exp in exps:
    exp = exp.replace(',','').strip()
    print('Experiment', exp)
    D = xr.open_dataset( tdir + '/' + exp + '/ice_extent.nc')
    DATS.append(D.expand_dims({"name" : [exp]}))
MODEL = xr.concat(DATS, dim = 'name')
if 'hemisphere' in MODEL.dims:
    MODEL = MODEL.rename({'hemisphere': 'pole'})

####################################
# grab ice extent observations
DATS = []
for ob in obs:
    print(  'obs', ob)
    if ob == 'analysis':
        D = MODEL.isel(forecast_hour = 0)
        D = D.drop_vars('forecast_hour')
        D = D.sel(grid = 'tripole')
        D = D.squeeze()
    else:
        D = xr.open_dataset( tdir + '/' + exp + '/' + ob + '_ice_extent.nc')
        if 'hemisphere' in D.dims:
            D = D.rename({'hemisphere': 'pole'})
    D = D.expand_dims({"name" : [ob]})
    DATS.append(D)
OBS = xr.concat(DATS, dim = 'name')

####################################
# if analysis, need to reduce time
if 'analysis' in OBS.name:
    end_date = MODEL['time'][-1].values + pd.Timedelta(hours = int(MODEL['forecast_hour'][-1].values))
    MODEL = MODEL.sel(time=slice(None, end_date))

####################################
# Give OBS forecast hours dimension
OBS = npb.iceobs.add_forecast_hour(OBS, MODEL['forecast_hour'][-1].values)

####################################
# grab only model output for same grid as obs
MODEL = MODEL.sel(grid = 'tripole')

####################################
# plot month and sea ice exten
times = MODEL['time']
npb.plot.ice_extent.save_dir = save_dir
npb.plot.ice_extent.MODEL = MODEL
npb.plot.ice_extent.OBS = OBS
for pole in ['NH', 'SH']:
    #times = times.isel(time = times.dt.month.isin([1,2,12]))
    npb.plot.ice_extent.pole = pole
    npb.plot.ice_extent.times = times 
    npb.plot.ice_extent.title = 'All Times'
    npb.plot.ice_extent.create()
    # plot for each time
    if (len(times) < 60):
        for t in times:
            npb.plot.ice_extent.times = t
            npb.plot.ice_extent.title = np.datetime_as_string(t, timezone='UTC')[0:10]
            npb.plot.ice_extent.create()
    # plot by month
    months = np.unique(MODEL['time'].sel(time = times).dt.month)
    for m in months:
        m_times = times.isel(time = times.dt.month.isin([m]))
        npb.plot.ice_extent.times = m_times 
        npb.plot.ice_extent.title = calendar.month_abbr[m].upper() 
        npb.plot.ice_extent.create() 
    # plot winter and summer cases
    #m_times = times.isel(time = times.dt.month.isin([1,2,12]))
    #if m_times.size > 5:
    #    npb.plot.ice_extent.times = m_times 
    #    npb.plot.ice_extent.title = 'Winter' 
    #    npb.plot.ice_extent.create() 
    #m_times = times.isel(time = times.dt.month.isin([6,7,8]))
    #if m_times.size > 5:
    #    npb.plot.ice_extent.times = m_times 
    #    npb.plot.ice_extent.title = 'Summer' 
    #    npb.plot.ice_extent.create() 

############
# plot monthly per tau bias heat plots
if len(np.unique(times.dt.month)) == 12:
    for i, d in enumerate(MODEL):
        d.attrs['save_dir'] = save_dir
        for obs in OBS:
            d.attrs['DMIN'], d.attrs['DMAX'] = -2.0, 2.0
            npb.plot.monthdiff_imshow(d, obs, var = 'extent', pole = 'north')
            d.attrs['DMIN'], d.attrs['DMAX'] = -6.0, 6.0
            npb.plot.monthdiff_imshow(d, obs, var = 'extent', pole = 'south')
        if i > 0:
            d.attrs['DMIN'], d.attrs['DMAX'] = -0.5, 0.5
            npb.plot.monthdiff_imshow(d, DAT[i-1], var = 'extent', pole = 'north')
            d.attrs['DMIN'], d.attrs['DMAX'] = -0.5, 0.5
            npb.plot.monthdiff_imshow(d, DAT[i-1], var = 'extent', pole = 'south')

