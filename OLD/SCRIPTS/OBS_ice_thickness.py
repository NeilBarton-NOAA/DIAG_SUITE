#!/usr/bin/env python3 
# plot sea ice thickness observations
import argparse
import os
import sys
import glob 
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Map Sea Ice Thicknesses")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
parser.add_argument('-fd', '--figuredir', action = 'store', nargs = 1, \
        help="directory of figures")
args = parser.parse_args()
obs_dir = args.obsdir[0] + '/ice_thickness'
save_dir = args.figuredir[0]

npb.maps.OBS_ICETHICKNESS.obs_dir = obs_dir
npb.maps.OBS_ICETHICKNESS.save_dir = save_dir
npb.maps.OBS_ICETHICKNESS.vmin = 0 
npb.maps.OBS_ICETHICKNESS.vmax = 5 

npb.maps.OBS_ICETHICKNESS.start_date = "2024-11-16" 
npb.maps.OBS_ICETHICKNESS.end_date = "2025-01-16"
npb.maps.OBS_ICETHICKNESS.title = "CryoSat-2 Ice Thickness"
npb.maps.OBS_ICETHICKNESS.create()

