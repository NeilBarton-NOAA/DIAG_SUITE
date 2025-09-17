#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse
import calendar
import os
import glob
import pandas as pd
import numpy as np
import sys
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Compares Sea Ice Extent Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-e', '--exp', action = 'store', nargs = '+', \
        help="experiment name")
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to parse")
parser.add_argument('-p', '--pole', action = 'store', nargs = 1, \
        help="pole to plot")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
args = parser.parse_args()
tdir = args.dirs[0]
exp = args.exp[0]
var = args.var[0]
pole = args.pole[0]
save_dir = args.figuredir[0]
obs_dir = args.obsdir[0]
obs = args.obs 
if 'analysis' in obs:
    obs.remove('analysis')
p = 0 if pole == 'north' else 1
########################
# names of variables, may want to move someplace else
long_name = {
'aice'    : 'Sea Ice Concentrations',
'Tsfc'    : 'Snow/Ice Surface Temp',
'hi'      : 'Ice Thickness',
'hs'      : 'Snow Depth',
'snow'    : 'Snowfall Rate'
}

########################
# get model results
print(exp)
file_search = tdir + '/INTERP_' + var + '*.nc' if var == 'aice' else tdir + '/' + var + '*.nc'
files = sorted(glob.glob(file_search))
DAT = xr.open_mfdataset(files)
if 'member' in DAT.dims: DAT = DAT.mean('member')
DAT['forecast_hour'] = DAT['forecast_hour'].where(DAT['forecast_hour'] >= 0, 0)
taus = DAT['forecast_hour'].values
times = DAT['time']

########################
# grab observations based on time and forecast tau
dtgs = DAT['time'].dt.strftime('%Y%m%d').values.tolist()
deltas = np.arange(24, int(DAT['forecast_hour'].max()) + 24, 24, dtype = 'timedelta64[h]')
dtgs = dtgs + pd.to_datetime(DAT['time'].values[-1] + deltas).strftime('%Y%m%d').tolist()
npb.iceobs.sic.top_dir = obs_dir
npb.iceobs.sic.ob_name = obs[0]
npb.iceobs.sic.dtg = dtgs
npb.iceobs.sic.pole = pole[0].upper() + 'H'
OBS = npb.iceobs.sic.grab() 
#######################
npb.maps.CICE.save_dir = save_dir
npb.maps.CICE.dat = DAT
npb.maps.CICE.obs = OBS
npb.maps.CICE.var_name = var
npb.maps.CICE.pole = pole
npb.maps.CICE.times = times
if var == 'hi': npb.maps.CICE.vmin, npb.maps.CICE.vmax = 0, 5
TAUS = [DAT['forecast_hour'].min().values, DAT['forecast_hour'].max().values]
TAUS = [DAT['forecast_hour'].max().values]

for t in TAUS:
    npb.maps.CICE.tau = t
    npb.maps.CICE.title = exp + ' for All Times: Forecast Day ' + str(t/24)
    npb.maps.CICE.create()
# plot for each time
if (len(times) < 90):
    for t in times:
        npb.maps.CICE.times = t
        for tau in TAUS:
            npb.maps.CICE.tau = tau
            npb.maps.CICE.title = exp + ' for ' + \
                np.datetime_as_string(t, timezone='UTC')[0:10] + \
                ': Forecast Day ' + str(tau/24)
            npb.maps.CICE.create()

# plot by month
months = np.unique(DAT['time'].sel(time = times).dt.month)
for m in months:
    m_times = times.isel(time = times.dt.month.isin([m]))
    npb.maps.CICE.times = m_times
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for ' + \
                calendar.month_abbr[m].upper() + \
                ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()
# plot winter and summer cases
m_times = times.isel(time = times.dt.month.isin([1,2,12]))
if times.size > 5:
    npb.maps.CICE.times = m_times
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for Winter' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()
m_times = times.isel(time = times.dt.month.isin([6,7,8]))
if m_times.size > 5:
    npb.maps.CICE.times = m_times
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for Summer' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()

debug = npb.utils.debug(True)

