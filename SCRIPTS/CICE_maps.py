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
import os
import glob
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
args = parser.parse_args()
tdir = args.dirs[0]
exp = args.exp[0]
var = args.var[0]
pole = args.pole[0]
save_dir = args.figuredir[0]
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
OBS = npb.iceobs.get_icecon_cdr() 
p = 0 if pole == 'north' else 1

########################
# get model results
print(exp)
file_search = tdir + '/interp_obs_grids_' + var + '*.nc'
DAT = xr.open_mfdataset(file_search, combine = 'nested', concat_dim = 'time', decode_times = True)
#DAT = xr.open_mfdataset(file_search, combine = 'nested', concat_dim = 'time', decode_times = False)
if 'member' in DAT.dims:
    DAT = DAT.mean('member')
DAT['tau'] = DAT['tau'] / 24.0
times = DAT['time']

########################
npb.maps.icecon.save_dir = save_dir
npb.maps.icecon.dat = DAT
npb.maps.icecon.obs = OBS[p]
npb.maps.icecon.var_name = var
npb.maps.icecon.pole = pole
npb.maps.icecon.times = times
npb.maps.icecon.tau = dat['tau'][0]
npb.maps.icecon.title = exp + ' for All Times: Forecast Day ' + str(dat['tau'][0])
npb.maps.icecon.create()
npb.maps.icecon.tau = DAT['tau'][-1]
npb.maps.icecon.title = exp + ' for All Times: Forecast Day ' + str(dat['tau'][-1])
npb.maps.icecon.create()
# plot for each time
if (len(times) < 20):
    for t in times:
    #        npb.plot.ice_extent.times = t
    #        npb.plot.ice_extent.title = np.datetime_as_string(t, timezone='UTC')[0:10]
    #        npb.plot.ice_extent.create()
    ## plot by month
    #months = np.unique(DAT[0]['time'].sel(time = times).dt.month)
    #for m in months:
    #    m_times = times.isel(time = times.dt.month.isin([m]))
    #    npb.plot.ice_extent.times = m_times 
    #    npb.plot.ice_extent.title = calendar.month_abbr[m].upper() 
    #    npb.plot.ice_extent.create() 
    ## plot winter and summer cases
    #m_times = times.isel(time = times.dt.month.isin([1,2,12]))
    #npb.plot.ice_extent.times = m_times 
    #npb.plot.ice_extent.title = 'Winter' 
    #npb.plot.ice_extent.create() 
    #m_times = times.isel(time = times.dt.month.isin([6,7,8]))
    #npb.plot.ice_extent.times = m_times 
    #npb.plot.ice_extent.title = 'Summer' 
    #npb.plot.ice_extent.create() 
#attrs = { 'MIN': 0.0, 'MAX': 1.0, 'DMIN': -1.0, 'DMAX': 1.0}
#print(pole)
#npb.maps.monthly(DAT, OBS[p], pole = pole)




