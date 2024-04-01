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

parser = argparse.ArgumentParser( description = "Compares Sea Ice Extent Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to parse")
args = parser.parse_args()
tdir = args.dirs[0]
var = args.var[0]
f = tdir + '/cice_area.nc'
area = xr.open_dataset(f)
print(tdir)
file_search = tdir + '/' + var + '_*.nc'
print(file_search)
D = xr.open_mfdataset(file_search, combine = 'nested', concat_dim = 'time', decode_times = True)
#D = xr.open_mfdataset(file_search) #, combine = 'nested', concat_dim = 'time', decode_times = False)
D['tau'] = D['tau'] / 24.0
D = D.assign_attrs({'data_dir' : tdir})
D = D.assign_attrs({'extent_file' : tdir + '/ice_extent.nc'})
D = npb.icecalc.extent(D, area, var = var)
