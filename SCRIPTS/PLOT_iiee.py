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

print('NPB: redo this similar to ice extent plots')
exit(1)
save_dir = '/scratch2/NCEPDEV/stmp3/Neil.Barton/FIGURES'

obs_types = ['climatology', 'cdr_seaice_conc', 'cdr_seaice_conc_persistence', 'persistence']
obs_types = ['climatology', 'cdr_seaice_conc', 'persistence']
####################################
# plot iiee
for pole in ['north', 'south']:
    print('IIEE Plot: ' , pole)
    for i, e in enumerate(exps):
        e = e.replace(',','').strip()
        f = tdir + '/' + e + '/iiee.nc'
        dat = xr.open_dataset(f)
        dat['tau'] = dat['tau'] / 24.0
        ob_type_month, y_label = [], []
        for month in np.arange(1,13):
            y_label.append(calendar.month_abbr[month])
            if month < 12:
                c_time = dat['time'].isel(time = dat['time'].dt.month.isin([month]))
                title = 'IIEE: ' + calendar.month_abbr[month].upper() + ' ' + e 
                fig_name = save_dir + '/' + pole[0].upper() + 'H_' + calendar.month_abbr[month].upper() + '_IIEE.png'
            else:
                c_time = dat['time']
                title = 'IIEE: ' + e 
                fig_name = save_dir + '/' + pole[0].upper() + 'H_ALL_TIMES_IIEE.png'
            #obs_types = dat['obs_type'].values
            if (c_time.size > 0):
                # save data for comparison
                min_ob_type = []
                for ob in obs_types:
                    print(ob)
                    if 'ice_con' in ob:
                        label = 'GEFS/EP4'
                    else:
                        label = ob.capitalize()
                    #label = ob.replace('_seaice_conc','')
                    #label = label.replace('_','-')
                    data = dat['iiee'].sel(obs_type = ob, pole = pole, time = c_time).mean('time')
                    if 'member' in data.dims:
                        plt.plot(data['tau'].values, data.mean('member').values, linewidth = 2.0, label = label )
                        plt.fill_between(data['tau'].values, data.min('member').values, data.max('member').values, alpha = 0.5)
                        min_ob_type.append(data.mean('member').values)
                    else:
                        data.plot(linewidth = 2.0, label = label)
                        min_ob_type.append(data.values)
                    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
                    #ax = kwargs.pop('ax', plt.gca())
                    #base_line, = ax.plot(x, y, **kwargs)
                    #print(base_line.get_color())
                ob_type_month.append(np.argmin(np.array(min_ob_type), axis = 0))
                if pole == 'north':
                    t = 'Arctic '
                elif pole == 'south':
                    t = 'Antarctic '
                plt.title(t + title)
                plt.ylabel('IIEE')
                plt.xlabel('Forecast Day')
                plt.legend(frameon = False)
                #plt.show()
                print(fig_name)
                plt.savefig(fig_name, bbox_inches = 'tight')
                plt.close()
        ####################################
        # plot imshow plot of cat with lowest IIEE value (month versus tau)
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(1,1,1)
        cmap = plt.get_cmap('jet')
        cmaplist = [cmap(i) for i in range(cmap.N)]
        for ii, ob in enumerate(obs_types):
            jj = int(ii/(len(obs_types) - 1) * len(cmaplist))
            if jj != 0:
                jj = jj - 1
            cmaplist[jj] = mpl.colors.hex2color(colors[ii])
            if jj not in [0, 255]:
                for jjj in [1,2,3,4,5]:
                    # pad colors to work
                    cmaplist[jj-jjj] = mpl.colors.hex2color(colors[ii])
                    cmaplist[jj+jjj] = mpl.colors.hex2color(colors[ii])
        cmap = mpl.colors.LinearSegmentedColormap.from_list('mcm',cmaplist, cmap.N)
        im = ax.imshow(ob_type_month, cmap = cmap,
                        vmin = 0, vmax = len(obs_types)-1,
                        aspect = 'auto',
                        interpolation = 'none')
        taus = np.arange(np.min(data['tau'].values), np.max(data['tau'].values) + 1)
        plt.xticks(np.arange(taus.size)[::3], taus[::3].astype('int'))
        for ii, ob in enumerate(obs_types):
            c = cmap(ii/(len(obs_types) - 1))
            if 'ice_con' in ob:
                tt = 'GEFS/EP4'
            else:
                tt = ob.capitalize()
            plt.text(np.max(taus) + 2 , 4 + ii, tt, color = c, fontsize = 16, fontweight = 'bold')
        plt.yticks(np.arange(12), y_label)
        ax.set_xlabel('Forecast Day')
        ax.set_title(t + ': Min IIEE', fontsize = 16, fontweight = 'bold')
        plt.tight_layout()
        fig_name = save_dir + '/' + pole[0].upper() + 'H_PER_MONTH_IIEE.png'
        print(fig_name)
        plt.savefig(fig_name, bbox_inches = 'tight')
        plt.close()
