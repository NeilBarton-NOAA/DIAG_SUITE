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
import glob
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
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
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
var = 'aice'
save_dir = args.figuredir[0]
obs_types = ['cdr_seaice_conc', 'cdr_seaice_conc_persistence', 'cdr_seaice_conc_climatology']
#obs_types = ['cdr_seaice_conc', 'cdr_seaice_conc_persistence'] #, 'cdr_seaice_conc_climatology']
#'nsidc_nt_seaice_conc', 
#'nsidc_bt_seaice_conc', 
#'cdr_seaice_conc_persistence', 
#'nsidc_nt_seaice_conc_persistence', 
#'nsidc_bt_seaice_conc_persistence'] 

####################################
# grab data
DAT = []
for i, e in enumerate(exps):
    print(e)
    e = e.replace(',','').strip()
    f = tdir + '/' + e + '/iiee.nc'
    dat = xr.open_dataset(f)
    dat = dat.assign_attrs({'test_name' : e})
    DAT.append(dat)

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
# line plots of iiee
npb.plot.iiee.save_dir = save_dir
npb.plot.iiee.DATS = DAT
npb.plot.iiee.OBS_TYPES = obs_types 
for pole in ['north', 'south']:
    # plot winter and summer cases
    print('IIEE Plot: ' , pole)
    npb.plot.iiee.pole = pole
    npb.plot.iiee.times = times 
    npb.plot.iiee.title = 'All Times'
    npb.plot.iiee.create()     
    # plot for each time
    if (len(times) < 60):
        for t in times:
            npb.plot.iiee.times = t
            npb.plot.iiee.title = np.datetime_as_string(t, timezone='UTC')[0:10]
            npb.plot.iiee.create()
    m_times = times.isel(time = times.dt.month.isin([4]))
    if m_times.size > 5:
        npb.plot.iiee.times = m_times 
        npb.plot.iiee.title = 'Retro 3 and 4' 
        npb.plot.iiee.create() 
    m_times = times.isel(time = times.dt.month.isin([11,12]))
    if m_times.size > 5:
        npb.plot.iiee.times = m_times 
        npb.plot.iiee.title = 'Retro 5,7,8' 
        npb.plot.iiee.create() 
    # plot by month
    #months = np.unique(DAT[0]['time'].sel(time = times).dt.month)
    #for m in months:
    #    m_times = times.isel(time = times.dt.month.isin([m]))
    #    npb.plot.iiee.times = m_times 
    #    npb.plot.iiee.title = calendar.month_abbr[m].upper() 
    #    npb.plot.iiee.create() 
    ## plot winter and summer cases
    #m_times = times.isel(time = times.dt.month.isin([1,2,12]))
    #if m_times.size > 5:
    #    npb.plot.iiee.times = m_times 
    #    npb.plot.iiee.title = 'Winter' 
    #    npb.plot.iiee.create() 
    #m_times = times.isel(time = times.dt.month.isin([6,7,8]))
    #if m_times.size > 5:
    #    npb.plot.iiee.times = m_times 
    #    npb.plot.iiee.title = 'Summer' 
    #    npb.plot.iiee.create() 

if len(np.unique(times.dt.month)) == 12:
    for i, D in enumerate(DAT):
        # min iiee plots
        npb.plot.iiee_min_imshow.save_dir = save_dir
        npb.plot.iiee_min_imshow.DAT = D
        npb.plot.iiee_min_imshow.OBS_TYPES = obs_types 
        pole = 'north'
        npb.plot.iiee_min_imshow.create()
        pole = 'south'
        npb.plot.iiee_min_imshow.create()
        # differnce iiee plots
        if i > 0:
            D.attrs['save_dir'] = save_dir
            npb.plot.monthdiff_imshow(D.sel(obs_type = obs_types[0]), DAT[i-1].sel(obs_type = obs_types[0]), 
                                        var = 'iiee', pole = 'north')
            npb.plot.monthdiff_imshow(D.sel(obs_type = obs_types[0]), DAT[i-1].sel(obs_type = obs_types[0]), 
                                        var = 'iiee', pole = 'south')
