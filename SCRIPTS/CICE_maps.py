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
import glob
import sys
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Compares Sea Ice Extent Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-e', '--exps', action = 'store', nargs = '+', \
        help="experiments to calc ice extent. Also name of directory under -d")
parser.add_argument('-v', '--var', action = 'store', nargs = 1, \
        help="variable to parse")
parser.add_argument('-p', '--pole', action = 'store', nargs = 1, \
        help="pole to plot")
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
var = args.var[0]
pole = args.pole[0]

########################
# names of variables, may want to move someplace else
long_name = {
'aice'    : 'Sea Ice Concentrations',
'Tsfc'    : 'Snow/Ice Surface Temp',
'hi'      : 'Ice Thickness',
'hs'      : 'Snow Depth',
'snow'    : 'Snowfall Rate'
}

########################
# get observations
OBS = npb.iceobs.get_icecon_cdr() 
p = 0 if pole == 'north' else 1

########################
# get model results
for exp in exps:
    print(exp)
    file_search = tdir + '/' + exp + '/' + var + '*.nc'
    DAT = xr.open_mfdataset(file_search, combine = 'nested', concat_dim = 'time', decode_times = True)
    #DAT = xr.open_mfdataset(file_search, combine = 'nested', concat_dim = 'time', decode_times = False)
    if 'member' in DAT.dims:
        DAT = DAT.mean('member')
    DAT['tau'] = DAT['tau'] / 24.0
    DAT = DAT.assign_attrs({'test_name' : exp})
    DAT = DAT.assign_attrs({'save_dir' : '/scratch2/NCEPDEV/stmp3/Neil.Barton/FIGURES'})
    DAT = DAT.assign_attrs({'var_name' : str(var)})
    DAT = DAT.assign_attrs({'long_name' : long_name[str(var[:-2])]})
    ########################
    # plot per month of data available
    #attrs = { 'MIN': 0.0, 'MAX': 1.0, 'DMIN': -1.0, 'DMAX': 1.0}
    print(pole)
    npb.maps.monthly(DAT, OBS[p], pole = pole)




