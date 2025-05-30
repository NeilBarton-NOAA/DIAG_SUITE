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
import glob 
import os
import sys
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Interp data and writes fields in Ones and Zeros")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
args = parser.parse_args()
tdir = args.dirs[0]
var = 'aice'
obs_dir = args.obsdir[0]

########################
# get observations
OBS = []
OBS.extend(npb.iceobs.get_icecon_nt(obs_dir))

########################
# get model results
files = glob.glob(tdir + '/' + var + '*.nc')
files.sort()
for f in files:
    print(f)
    DAT = xr.open_dataset(f)
    DAT = DAT.assign_attrs({'file_name' : f }) 
    npb.icecalc.interp(DAT, OBS, var = var, force_calc = False)
