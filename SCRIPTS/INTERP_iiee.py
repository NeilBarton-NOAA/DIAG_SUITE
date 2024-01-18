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
parser.add_argument('-e', '--exps', action = 'store', nargs = '+', \
        help="experiments to calc ice extent. Also name of directory under -d")
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to parse")
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
var = args.var[0]

########################
# get observations
OBS = []
#OBS = ['persistence']
#OBS.extend(npb.iceobs.get_icecon_daily_climatology())
OBS.extend(npb.iceobs.get_icecon_nt())
#OBS.extend(npb.iceobs.get_icecon_bs())
#OBS.extend(npb.iceobs.get_icecon_nsidc0051())
#OBS.extend(npb.iceobs.get_icecon_cdr())

########################
# get model results
for exp in exps:
    files = glob.glob(tdir + '/' + exp + '/' + var + '*.nc')
    files.sort()
    for f in files:
        print(f)
        DAT = xr.open_dataset(f)
        DAT = DAT.assign_attrs({'file_name' : f }) 
        npb.icecalc.interp(DAT, OBS, var = var, force_calc = False)

