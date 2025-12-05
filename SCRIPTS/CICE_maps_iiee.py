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
import os
import glob
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
parser.add_argument('-p', '--pole', action = 'store', nargs = 1, \
        help="pole to plot")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
args = parser.parse_args()
tdir = args.dirs[0]
exp = args.exp[0]
pole = args.pole[0]
obs = args.obs[0]
save_dir = args.figuredir[0]

########################
# get model results
print(exp)
f = tdir + '/iiee.nc'
DAT = xr.open_dataset(f)
DAT = DAT.sel(obs_type = obs, pole = pole[0].upper() + 'H')
if obs == 'osi_saf':
    suffix = pole[0].upper() + 'H10'
    npb.maps.IIEE.var = 'diff' + suffix
    npb.maps.IIEE.lon = DAT['lon' + suffix]
    npb.maps.IIEE.lat = DAT['lat' + suffix]
elif obs == 'analysis':
    #suffix = pole[0].upper() 
    npb.maps.IIEE.var = 'diff'
    npb.maps.IIEE.lon = DAT['TLON']
    npb.maps.IIEE.lat = DAT['TLAT']
else:
    print(DAT)
    print('diff var is unknown for ', obs)
    exit(1)
#######################
times = DAT['time']
npb.maps.IIEE.obs = obs
npb.maps.IIEE.save_dir = save_dir
npb.maps.IIEE.dat = DAT
npb.maps.IIEE.pole = pole
npb.maps.IIEE.times = times
FIRST_TAUS = DAT['forecast_hour'][0:2].values

########################
# all times
TAUS = np.append(FIRST_TAUS, DAT['forecast_hour'].max().values)
for t in TAUS:
    npb.maps.IIEE.tau = t
    npb.maps.IIEE.title = exp + ' for All Times: Forecast Day ' + str(t/24.0)
    npb.maps.IIEE.create()

############
# through each time step
if (len(times) < npb.utils.N_TIMES()):
    for t in times:
        npb.maps.IIEE.times = t
        for tau in TAUS:
            npb.maps.IIEE.tau = tau
            npb.maps.IIEE.title = exp + ' DIFF for ' + \
                np.datetime_as_string(t, timezone='UTC')[0:10] + \
                ': Forecast Day ' + str(tau/24)
            npb.maps.IIEE.create()

# plot by month
months = np.unique(DAT['time'].sel(time = times).dt.month)
for m in months:
    m_times = times.isel(time = times.dt.month.isin([m]))
    npb.maps.IIEE.times = m_times
    for tau in TAUS:
        npb.maps.IIEE.tau = tau
        npb.maps.IIEE.title = exp + ' for ' + \
                calendar.month_abbr[m].upper() + \
                ': Forecast Day ' + str(tau/24)
        npb.maps.IIEE.create()

# plot winter and summer cases
m_times = times.isel(time = times.dt.month.isin([1,2,12]))
if m_times.size > 5:
    npb.maps.IIEE.times = m_times
    for tau in TAUS:
        npb.maps.IIEE.tau = tau
        npb.maps.IIEE.title = exp + ' for Winter' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.IIEE.create()

m_times = times.isel(time = times.dt.month.isin([6,7,8]))
if m_times.size > 5:
    npb.maps.IIEE.times = m_times
    for tau in TAUS:
        npb.maps.IIEE.tau = tau
        npb.maps.IIEE.title = exp + ' for Summer' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.IIEE.create()

debug = npb.utils.debug(True)
