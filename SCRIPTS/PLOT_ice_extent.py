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
args = parser.parse_args()
tdir = args.dirs[0]
exps = args.exps
var = args.var[0]

####################################
# grab ice extent from models
DAT = []
for exp in exps:
    exp = exp.replace(',','').strip()
    print(exp)
    D = xr.open_dataset( tdir + '/' + exp + '/ice_extent.nc')
    D = D.assign_attrs({'save_dir' : '/scratch2/NCEPDEV/stmp3/Neil.Barton/FIGURES'})
    DAT.append(D)

####################################
# grab ice extent observations
EXT = []
EXT.append(npb.iceobs.get_extentobs_NASA())
EXT.append(npb.iceobs.get_extentobs_bootstrap())

####################################
# plot month and sea ice extent 
npb.plot.ice_extent_per_month(DAT, EXT)

############
# plot monthly per tau bias heat plots
#   to add colorbar limits 
#       attrs = {'DMIN': -5.0, 'DMAX': 5.0}
#       CTL = CTL.assign_attrs(attrs)
#       RPL = RPL.assign_attrs(attrs)
for d in DAT:
    for obs in EXT:
        
        npb.plot.ice_extent_imshowdiff(d, obs, pole = 'north')
        npb.plot.ice_extent_imshowdiff(d, obs, pole = 'south')

