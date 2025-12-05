#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse
import calendar
import numpy as np
import os
import sys
import pandas as pd
import xarray as xr
path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.getenv("PYTHON_TOOLS")) if 'slurm' in path else sys.path.append(path)
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Plot Ice Extent between Runs and Observations")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', \
        help="ice extent files")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
args = parser.parse_args()
files = args.files
obs = args.obs
save_dir = args.figuredir[0]
var = 'aice'
poles = ['NH', 'SH']
os.makedirs(save_dir, exist_ok=True)
####################################
# grab ice extent from models
DATS, exps = [], []
for f in files:
    print(f)
    D = xr.open_dataset(f)
    exp = D.attrs['experiment_name'] 
    exps.append(exp)
    DATS.append(D.expand_dims({"name" : [exp]}))

MODEL = xr.concat(DATS, dim = 'name')
dtgs = MODEL['time'].dt.strftime('%Y%m%d').values.tolist()
npb.iceobs.extent.dtgs = dtgs

####################################
# grab ice extent observations
DATS = []
grid = '10km'
#grid = '25km'
#grid = 'tripole'
analysis = False
for ob in obs:
    print(  'obs:', ob)
    if ob == 'analysis':
        D = MODEL.isel(forecast_hour = 0)
        D = D.drop_vars('forecast_hour')
        D = D.sel(grid = grid)
        D = D.squeeze()
        analysis = True
    else:
        file_extent = ob + '/ice_extent_' + dtgs[0] + '_to_' + dtgs[-1] + '.nc'
        npb.iceobs.extent.directory = ob
        D = npb.iceobs.extent.grab()

        print(file_extent)
        npb.utils.stop() 
        npb.iceobs.sic.directory = ob
        POLE = []
        for p in poles:
            print(p)
            npb.iceobs.sic.pole = p
            npb.icecalc.extent.ds = npb.iceobs.sic.grab()
            dat = npb.icecalc.extent.calc()
            POLE.append(dat.expand_dims({"pole" : [p]}))
        POLE = xr.concat(POLE, dim = 'pole')
        print(POLE)
        #POLE.to_netcdf(obs_name)
        npb.utils.stop() 
        #if 'hemisphere' in D.dims:
        #    D = D.rename({'hemisphere': 'pole'})
    if 'name' not in D.dims:
        D = D.expand_dims({"name" : [ob]})
    DATS.append(D)
OBS = xr.concat(DATS, dim = 'name')
####################################
# if analysis, need to reduce time
if analysis:
    end_date = MODEL['time'][-1].values + pd.Timedelta(hours = int(MODEL['forecast_hour'][-1].values))
    MODEL = MODEL.sel(time=slice(None, end_date))

####################################
# Give OBS forecast hours dimension
OBS = npb.utils.add_forecast_hour(OBS, MODEL['forecast_hour'][-1].values)
OBS = OBS.dropna(dim='time', how='any', subset=list(OBS))
new_names = ['analysis ' + n if n in exps else n for n in OBS['name'].values]
OBS['name'] = new_names

####################################
# grab only model output for same grid as obs
MODEL = MODEL.sel(grid = grid)
common_times = np.intersect1d(MODEL.time.values, OBS.time.values)
OBS = OBS.sel(time = common_times)
MODEL = MODEL.sel(time = common_times)

####################################
# plot month and sea ice exten
times = MODEL['time']
npb.plot.ice_extent.save_dir = save_dir
npb.plot.ice_extent.MODEL = MODEL
npb.plot.ice_extent.OBS = OBS
for pole in poles:
    npb.plot.ice_extent.pole = pole
    npb.plot.ice_extent.times = times 
    npb.plot.ice_extent.title = 'All Times'
    npb.plot.ice_extent.create()
    # plot for each time
    if (len(times) < 100):
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
    m_times = times.isel(time = times.dt.month.isin([1,2,12]))
    if m_times.size > 5:
        npb.plot.ice_extent.times = m_times 
        npb.plot.ice_extent.title = 'DJF' 
        npb.plot.ice_extent.create() 
    m_times = times.isel(time = times.dt.month.isin([6,7,8]))
    if m_times.size > 5:
        npb.plot.ice_extent.times = m_times 
        npb.plot.ice_extent.title = 'JJA' 
        npb.plot.ice_extent.create() 

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

debug = npb.utils.debug(True)
print('PLOT_ice_extent.py SUCCESSFUL')

