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

parser = argparse.ArgumentParser( description = "Calculates Ice Extent from Observational Datasets")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
args = parser.parse_args()
obs_dir = args.obsdir[0]

########################
# get observations
SAMPLE = npb.iceobs.get_extentobs_NASA(obs_dir)
print(SAMPLE)
print(' ')
print(' ')
print(' ')

variables = ['nsidc_nt_seaice_conc', 'nsidc_bt_seaice_conc', 'cdr_seaice_conc']
for v in variables:
    OBS = npb.iceobs.get_extentobs_CDR(obs_dir, v)

