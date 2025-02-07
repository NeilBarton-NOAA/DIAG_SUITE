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
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Plot Integrated Ice Extent Error Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-e', '--exps', action = 'store', nargs = '+', \
        help="experiments to calc ice extent. Also name of directory under -d")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
save_dir = args.figuredir[0]
obs_dir = args.obsdir[0]
var = 'aice'

####################################
# grab ice extent from models
DAT = []
for exp in exps:
    exp = exp.replace(',','').strip()
    print(exp)
    D = xr.open_dataset( tdir + '/' + exp + '/ice_extent.nc')
    D = D.assign_attrs({'test_name' : exp})
    DAT.append(D)

####################################
# Get Same Times of Data Sets
if len(DAT) > 1:
    for i, ds in enumerate(DAT):
        c_time = ds['time']
        if i == 0: 
            a_time = c_time
        else: 
            times = np.array(list(set(c_time.values) & set(a_time.values)))
    times = DAT[0]['time'].sel(time = times)
else:
    times = DAT[0]['time']

####################################
# grab ice extent observations
OBS = []
OBS.append(npb.iceobs.get_extentobs_NASA(obs_dir))
OBS.append(npb.iceobs.get_extentobs_bootstrap(obs_dir))

####################################
# plot month and sea ice extent 
npb.plot.ice_extent.save_dir = save_dir
npb.plot.ice_extent.dats = DAT
npb.plot.ice_extent.obss = OBS
for pole in ['north', 'south']:
    npb.plot.ice_extent.pole = pole
    npb.plot.ice_extent.times = times 
    npb.plot.ice_extent.title = 'All Times'
    npb.plot.ice_extent.create()
    # plot for each time
    if (len(times) < 20):
        for t in times:
            npb.plot.ice_extent.times = t
            npb.plot.ice_extent.title = np.datetime_as_string(t, timezone='UTC')[0:10]
            npb.plot.ice_extent.create()
    # plot by month
    months = np.unique(DAT[0]['time'].sel(time = times).dt.month)
    for m in months:
        m_times = times.isel(time = times.dt.month.isin([m]))
        npb.plot.ice_extent.times = m_times 
        npb.plot.ice_extent.title = calendar.month_abbr[m].upper() 
        npb.plot.ice_extent.create() 
    # plot winter and summer cases
    m_times = times.isel(time = times.dt.month.isin([1,2,12]))
    npb.plot.ice_extent.times = m_times 
    npb.plot.ice_extent.title = 'Winter' 
    npb.plot.ice_extent.create() 
    m_times = times.isel(time = times.dt.month.isin([6,7,8]))
    npb.plot.ice_extent.times = m_times 
    npb.plot.ice_extent.title = 'Summer' 
    npb.plot.ice_extent.create() 

############
# plot monthly per tau bias heat plots
#   to add colorbar limits 
#       attrs = {'DMIN': -5.0, 'DMAX': 5.0}
#       CTL = CTL.assign_attrs(attrs)
#       RPL = RPL.assign_attrs(attrs)
if len(months) == 12:
    for d in DAT:
        for obs in EXT:
            npb.plot.ice_extent_imshowdiff(d, obs, pole = 'north')
            npb.plot.ice_extent_imshowdiff(d, obs, pole = 'south')
