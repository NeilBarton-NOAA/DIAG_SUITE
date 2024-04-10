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
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to parse")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
var = args.var[0]
save_dir = args.figuredir[0]
obs_types = ['climatology', 'cdr_seaice_conc', 'cdr_seaice_conc_persistence']
#'nsidc_nt_seaice_conc', 
#'nsidc_bt_seaice_conc', 
#'cdr_seaice_conc_persistence', 
#'nsidc_nt_seaice_conc_persistence', 
#'nsidc_bt_seaice_conc_persistence'] 

####################################
# grab data
DAT = []
for i, e in enumerate(exps):
    e = e.replace(',','').strip()
    f = tdir + '/' + e + '/iiee.nc'
    dat = xr.open_dataset(f)
    dat['tau'] = dat['tau'] / 24.0
    dat = dat.assign_attrs({'test_name' : e})
    DAT.append(dat)

####################################
# Get Same Times of Data Sets
if len(DAT) > 1:
    for i, ds in enumerate(DAT):
        c_time = ds['time']
        print(c_time)
        if i == 0: 
            a_time = c_time
        else: 
            times = np.array(list(set(c_time.values) & set(a_time.values)))
else:
    times = DAT[0]['time']

####################################
# plot iiee
npb.plot.iiee.save_dir = save_dir
npb.plot.iiee.DATS = DAT
npb.plot.iiee.OBS_TYPES = obs_types 
for pole in ['north', 'south']:
    print('IIEE Plot: ' , pole)
    npb.plot.iiee.pole = pole
    npb.plot.iiee.times = times 
    npb.plot.iiee.title = 'All Times'
    npb.plot.iiee.create()     
    # plot for each time
    if (len(times) < 20):
        for t in times:
            npb.plot.iiee.times = t
            npb.plot.iiee.title = np.datetime_as_string(t, timezone='UTC')[0:10]
            npb.plot.iiee.create()
    # plot by month
    months = np.unique(DAT[0]['time'].sel(time = times).dt.month)
    for m in months:
        m_times = times.isel(time = times.dt.month.isin([m]))
        npb.plot.iiee.times = m_times 
        npb.plot.iiee.title = calendar.month_abbr[m].upper() 
        npb.plot.iiee.create() 
    # plot winter and summer cases
    m_times = times.isel(time = times.dt.month.isin([1,2,12]))
    npb.plot.iiee.times = m_times 
    npb.plot.iiee.title = 'Winter' 
    npb.plot.iiee.create() 
    m_times = times.isel(time = times.dt.month.isin([6,7,8]))
    npb.plot.iiee.times = m_times 
    npb.plot.iiee.title = 'Summer' 
    npb.plot.iiee.create() 
    # if all months exist
    #if len(months) == 12: 
#       iiee_min_per_month.create() 
#        ####################################
#        # plot imshow plot of cat with lowest IIEE value (month versus tau)
#        fig = plt.figure(figsize=(8, 6))
#        ax = fig.add_subplot(1,1,1)
#        cmap = plt.get_cmap('jet')
#        cmaplist = [cmap(i) for i in range(cmap.N)]
#        for ii, ob in enumerate(obs_types):
#            jj = int(ii/(len(obs_types) - 1) * len(cmaplist))
#            if jj != 0:
#                jj = jj - 1
#            cmaplist[jj] = mpl.colors.hex2color(colors[ii])
#            if jj not in [0, 255]:
#                for jjj in [1,2,3,4,5]:
#                    # pad colors to work
#                    cmaplist[jj-jjj] = mpl.colors.hex2color(colors[ii])
#                    cmaplist[jj+jjj] = mpl.colors.hex2color(colors[ii])
#        cmap = mpl.colors.LinearSegmentedColormap.from_list('mcm',cmaplist, cmap.N)
#        im = ax.imshow(ob_type_month, cmap = cmap,
#                        vmin = 0, vmax = len(obs_types)-1,
#                        aspect = 'auto',
#                        interpolation = 'none')
#        taus = np.arange(np.min(data['tau'].values), np.max(data['tau'].values) + 1)
#        plt.xticks(np.arange(taus.size)[::3], taus[::3].astype('int'))
#        for ii, ob in enumerate(obs_types):
#            c = cmap(ii/(len(obs_types) - 1))
#            if 'ice_con' in ob:
#                tt = 'GEFS/EP4'
#            else:
#                tt = ob.capitalize()
#            plt.text(np.max(taus) + 2 , 4 + ii, tt, color = c, fontsize = 16, fontweight = 'bold')
#        plt.yticks(np.arange(12), y_label)
#        ax.set_xlabel('Forecast Day')
#        ax.set_title(t + ': Min IIEE', fontsize = 16, fontweight = 'bold')
#        plt.tight_layout()
#        fig_name = save_dir + '/' + pole[0].upper() + 'H_PER_MONTH_IIEE.png'
#        print(fig_name)
#        plt.savefig(fig_name, bbox_inches = 'tight')
#        plt.close()
