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

DAT = xr.open_mfdataset(tdir + file_search, combine = 'nested', concat_dim = 'time', decode_times = True)
#DAT = xr.open_mfdataset(file_search, combine = 'nested', concat_dim = 'time', decode_times = False)
if 'member' in DAT.dims:
    DAT = DAT.mean('member')
taus = DAT['tau'].values
times = DAT['time'].values
if all_exps:
    for e in all_exps:
        if e != exp:
            print('Comparing times and taus to', e)
            print(tdir + '/../' + e + file_search)
            DAT2 = xr.open_mfdataset(obs_dir + '/../' + e + file_search, combine = 'nested', concat_dim = 'time', decode_times = True)
            times = np.array(list(set(DAT2['time'].values) & set(times)))
            taus = np.array(list(set(DAT2['tau'].values) & set(taus)))
            del DAT2
taus = taus / 24.0
TAUS = [min(taus)] 
TAUS.append(max(taus)) 
DAT = DAT.sel(time = times)
times = DAT['time']
DAT['tau'] = DAT['tau'] / 24 

#######################
npb.maps.icecon.save_dir = save_dir
npb.maps.icecon.dat = DAT
npb.maps.icecon.obs = OBS[p]
npb.maps.icecon.var_name = var
npb.maps.icecon.pole = pole
npb.maps.icecon.times = times
for t in TAUS:
    npb.maps.icecon.tau = t
    npb.maps.icecon.title = exp + ' for All Times: Forecast Day ' + str(t)
    npb.maps.icecon.create()
# plot for each time
if (len(times) < 20):
    for t in times:
        npb.maps.icecon.times = t
        for tau in TAUS:
            npb.maps.icecon.tau = tau
            npb.maps.icecon.title = exp + ' for ' + \
                np.datetime_as_string(t, timezone='UTC')[0:10] + \
                ': Forecast Day ' + str(tau)
            npb.maps.icecon.create()
# plot by month
months = np.unique(DAT['time'].sel(time = times).dt.month)
for m in months:
    m_times = times.isel(time = times.dt.month.isin([m]))
    npb.maps.icecon.times = m_times
    for tau in TAUS:
        npb.maps.icecon.tau = tau
        npb.maps.icecon.title = exp + ' for ' + \
                calendar.month_abbr[m].upper() + \
                ': Forecast Day ' + str(tau)
        npb.maps.icecon.create()
# plot winter and summer cases
m_times = times.isel(time = times.dt.month.isin([1,2,12]))
if m_times.size > 5:
    npb.maps.icecon.times = m_times
    for tau in TAUS:
        npb.maps.icecon.tau = tau
        npb.maps.icecon.title = exp + ' for Winter' + \
            ': Forecast Day ' + str(tau)
        npb.maps.icecon.create()
m_times = times.isel(time = times.dt.month.isin([6,7,8]))
if m_times.size > 5:
    npb.maps.icecon.times = m_times
    for tau in TAUS:
        npb.maps.icecon.tau = tau
        npb.maps.icecon.title = exp + ' for Summer' + \
            ': Forecast Day ' + str(tau)
        npb.maps.icecon.create()
