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
import sys
import glob 
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Calculates Integrated Ice Extent Error Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
args = parser.parse_args()
tdir = args.dirs[0]
obs_dir = args.obsdir[0]
var = 'aice'
########################
# get observations
ICEOBS = []
#ICEOBS.extend(npb.iceobs.get_icecon_nt(obs_dir))
#ICEOBS.extend(npb.iceobs.get_icecon_bs(obs_dir))
ICEOBS.extend(npb.iceobs.get_icecon_cdr(obs_dir))
CLIMO = npb.iceobs.get_icecon_daily_climatology(obs_dir)

########################
# get model results
file_search = tdir + '/interp_obs_grids_' + var + '*.nc'
files = glob.glob(file_search)
files.sort()
iiee_file = tdir + '/iiee.nc'
if os.path.exists(iiee_file):
    print('Removing IIEE file')
    os.remove(iiee_file)
exp_dat = []
if os.path.exists(iiee_file) == False:
    for f in files:
        print(f)
        DAT = xr.open_dataset(f)
        # calc iiee scores
        temp = npb.icecalc.iiee(DAT, ICEOBS, CLIMO, var = var)
        exp_dat.append(temp)
    if (len(files) > 1 ):
        print('concating data')
        ds = xr.concat(exp_dat, dim = 'time')
        # save data
        ds.to_netcdf(iiee_file)
    else:
        temp.to_netcdf(iiee_file)
    print('SAVED: ', iiee_file)

