#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
# check platform
import platform
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
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
args = parser.parse_args()
tdir = args.dirs[0]
var = 'aice'
obs_dir = args.obsdir[0]
obs = args.obs

########################
# get model results
files = glob.glob(tdir + '/' + var + '*.nc')
files.sort()
npb.iceobs.sic.top_dir = obs_dir

########################
# obs grid
ds_model = xr.open_dataset(files[0])
dtg = ds_model.time.dt.strftime('%Y%m%d').values[0]
npb.iceobs.sic.dtg = dtg
obs.append('climatology')
ds_obs = []
for ob in obs:
    if ob != 'analysis':
        print(ob)
        npb.iceobs.sic.ob_name = ob
        for p in ['NH', 'SH']:
            npb.iceobs.sic.pole = p
            ds_obs.append(npb.iceobs.sic.grab())

########################
# loop through files
for f in files:
    print(f)
    ds_model = xr.open_dataset(f)
    ds_model = ds_model.assign_attrs({'file_name' : f }) 
    npb.icecalc.interp(ds_model, ds_obs, var = var, force_calc = False)
