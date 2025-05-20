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
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to parse")
parser.add_argument('-p', '--pole', action = 'store', nargs = 1, \
        help="pole to plot")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
parser.add_argument('-ae', '--allexps', action = 'store', nargs = '*', default = None, \
        help="all experiments being analyzed to make sure tau and time are the same")
args = parser.parse_args()
tdir = args.dirs[0]
exp = args.exp[0]
var = args.var[0]
pole = args.pole[0]
save_dir = args.figuredir[0]
obs_dir = args.obsdir[0]
all_exps = args.allexps
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
# get observations
OBS = npb.iceobs.get_icecon_cdr(obs_dir) 
p = 0 if pole == 'north' else 1

########################
# get model results
print(exp)
if var == 'aice':
    file_search = '/interp_obs_grids_' + var + '*.nc'
else:
    file_search = '/' + var + '*.nc'

files = sorted(glob.glob(tdir + file_search))
DAT = xr.open_mfdataset(files)

if 'member' in DAT.dims:
    DAT = DAT.mean('member')
taus = DAT['forecast_hour'].values
times = DAT['time'].values

if all_exps:
    for e in all_exps:
        if e != exp:
            search = tdir + '/../' + e + file_search
            print('Comparing times and taus to', e)
            print(search)
            files = sorted(glob.glob(search))
            DAT2 = xr.open_mfdataset(files, coords='minimal')
            times = np.array(list(set(DAT2['time'].values) & set(times)))
            taus = np.array(list(set(DAT2['forecast_hour'].values) & set(taus)))
            del DAT2
DAT = DAT.sel(time = times)
DAT['forecast_hour'] = DAT['forecast_hour'].where(DAT['forecast_hour'] >= 0, 0)
times = DAT['time']

#######################
npb.maps.CICE.save_dir = save_dir
npb.maps.CICE.dat = DAT
npb.maps.CICE.obs = OBS[p]
npb.maps.CICE.var_name = var
npb.maps.CICE.pole = pole
npb.maps.CICE.times = times

dim_search = DAT[var].dims[-2::]
index = (DAT[var].sel(time = times).isnull().all(dim = dim_search).any(dim = 'time') == False).values
valid_taus = DAT['forecast_hour'][index] 
TAUS = [int(min(valid_taus)), int(max(valid_taus))]
for t in TAUS:
    npb.maps.CICE.tau = t
    npb.maps.CICE.title = exp + ' for All Times: Forecast Day ' + str(t/24)
    npb.maps.CICE.create()
# plot for each time
if (len(times) < 60):
    for t in times:
        npb.maps.CICE.times = t
        index = (DAT[var].sel(time = t).isnull().all(dim = dim_search) == False).values
        valid_taus = DAT['forecast_hour'][index] 
        print(valid_taus)
        TAUS = [int(min(valid_taus)), int(max(valid_taus))]
        for tau in TAUS:
            npb.maps.CICE.tau = tau
            npb.maps.CICE.title = exp + ' for ' + \
                np.datetime_as_string(t, timezone='UTC')[0:10] + \
                ': Forecast Day ' + str(tau/24)
            npb.maps.CICE.create()

m_times = times.isel(time = times.dt.month.isin([4]))
if m_times.size > 5:
    npb.maps.CICE.times = m_times
    index = (DAT[var].sel(time = m_times).isnull().all(dim = dim_search).any(dim = 'time') == False).values
    valid_taus = DAT['forecast_hour'][index] 
    TAUS = [int(min(valid_taus)), int(max(valid_taus))]
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for Retro Tests 3 and 4' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()

m_times = times.isel(time = times.dt.month.isin([11,12]))
if m_times.size > 5:
    npb.maps.CICE.times = m_times
    index = (DAT[var].sel(time = m_times).isnull().all(dim = dim_search).any(dim = 'time') == False).values
    valid_taus = DAT['forecast_hour'][index] 
    TAUS = [int(min(valid_taus)), int(max(valid_taus))]
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for Retro Tests 5, 7, and 8' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()

print('NPB exit for retros')
exit(0)
# plot by month
months = np.unique(DAT['time'].sel(time = times).dt.month)
for m in months:
    m_times = times.isel(time = times.dt.month.isin([m]))
    npb.maps.CICE.times = m_times
    index = (DAT[var].sel(time = m_times).isnull().all(dim = dim_search).any(dim = 'time') == False).values
    valid_taus = DAT['forecast_hour'][index] 
    TAUS = [int(min(valid_taus)), int(max(valid_taus))]
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
    index = (DAT[var].sel(time = m_times).isnull().all(dim = dim_search).any(dim = 'time') == False).values
    valid_taus = DAT['forecast_hour'][index] 
    TAUS = [int(min(valid_taus)), int(max(valid_taus))]
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for Winter' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()
m_times = times.isel(time = times.dt.month.isin([6,7,8]))
if m_times.size > 5:
    npb.maps.CICE.times = m_times
    index = (DAT[var].sel(time = m_times).isnull().all(dim = dim_search).any(dim = 'time') == False).values
    valid_taus = DAT['forecast_hour'][index] 
    TAUS = [int(min(valid_taus)), int(max(valid_taus))]
    for tau in TAUS:
        npb.maps.CICE.tau = tau
        npb.maps.CICE.title = exp + ' for Summer' + \
            ': Forecast Day ' + str(tau/24)
        npb.maps.CICE.create()
