#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
########################
import argparse
import fnmatch
import glob
import os
import sys
import re
import pandas as pd
import numpy as np
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Compares Sea Ice Extent Between Runs and Observations")
parser.add_argument('-d', '--dirs', action = 'store', nargs = 1, \
        help="top directory to find model output files")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
args = parser.parse_args()
tdir = args.dirs[0]
obs_dir = args.obsdir[0]
obs = args.obs
var = 'aice'

####################################
# model data
extent_file = tdir + '/ice_extent.nc'
poles = ['NH', 'SH']
Force_Calc = False
if not os.path.exists(extent_file) or Force_Calc == True:
    file_search = tdir + '/INTERP*' + var + '_*.nc'
    print(file_search)
    files = glob.glob(file_search)
    files.sort()
    time_data = []
    for i, f in enumerate(files):
        print(f)
        ds = xr.open_dataset(f)
        npb.icecalc.extent.ds = ds
        if i == 0:
            variables = fnmatch.filter(ds.variables, "aice*binary")
            variables = [var for var in variables if 'SH' not in var]
        var_data = []
        for j, v in enumerate(variables):
            print(' ',v)
            npb.icecalc.extent.var = v
            if v == 'aice_binary':
                dat = npb.icecalc.extent.calc()
                grid = 'tripole'
            else:
                pole_data = []
                for p in poles:
                    if p == 'SH':
                        v = v.replace('NH', 'SH')
                        print(' ',v)
                        npb.icecalc.extent.var = v
                        grid = v.split('SH')[1]
                        grid = grid.split('_')[0] + 'km'
                    EXT = npb.icecalc.extent.calc()
                    pole_data.append(EXT.expand_dims({"hemisphere" : [p]}))
                dat = xr.concat(pole_data, dim = 'hemisphere')
            var_data.append(dat.expand_dims({"grid" : [grid]}))
        time_data.append(xr.concat(var_data, dim = 'grid'))
    dat = xr.concat(time_data, dim = 'time')
    dat.to_netcdf(extent_file)
    print("WROTE:", extent_file)
    model_dat = dat
else:
    model_dat = xr.open_dataset(extent_file)

####################################
# Calc Extent for Climatology
file = obs_dir + '/ice_extent/climatology_ice_extent.nc'
if not os.path.exists(file):
    ob = 'climatology'
    print('CALC sea ice extent from', ob)
    npb.iceobs.sic.top_dir = obs_dir
    npb.iceobs.sic.ob_name = ob
    npb.icecalc.extent.var = 'ice_con'
    pole_data = []
    for p in poles:
        npb.iceobs.sic.pole = p
        dat = npb.iceobs.sic.grab()
        npb.icecalc.extent.ds = dat
        data = npb.icecalc.extent.calc()
        pole_data.append(data.expand_dims({"hemisphere" : [p]}))
    EXT = xr.concat(pole_data, dim = 'hemispheres')
    EXT.to_netcdf(file)
    print("WROTE:", file)

####################################
# obs data
start_date = model_dat['time'][0].values
end_date = model_dat['time'][-1].values + pd.Timedelta(hours = int(model_dat['forecast_hour'][-1].values))
time_coords = pd.date_range(start=start_date, end=end_date, freq='D')
obs.remove('analysis')
npb.iceobs.sic.top_dir = obs_dir
npb.icecalc.extent.var = 'ice_con'
for ob in obs:
    file = tdir + '/' + ob + '_ice_extent.nc'
    npb.iceobs.sic.ob_name = ob
    if not os.path.exists(file):
        time_data = []
        for i, t in enumerate(time_coords):
            npb.iceobs.sic.dtg = t.strftime('%Y%m%d')
            pole_data = []
            for p in poles:
                npb.iceobs.sic.pole = p
                dat = npb.iceobs.sic.grab()
                npb.icecalc.extent.ds = dat
                EXT = npb.icecalc.extent.calc()
                if EXT:
                    pole_data.append(EXT.expand_dims({"hemisphere" : [p]}))
            del EXT
            time_data.append(xr.concat(pole_data, dim = 'hemisphere'))
        EXT = xr.concat(time_data, dim = 'time')
        EXT = EXT.assign_attrs({'grid': dat.grid})
        EXT.to_netcdf(file)
        print("WROTE:", file)

