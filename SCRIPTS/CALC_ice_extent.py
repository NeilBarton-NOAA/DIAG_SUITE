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
path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.getenv("PYTHON_TOOLS")) if 'slurm' in path else sys.path.append(path)
import PYTHON_TOOLS as npb
parser = argparse.ArgumentParser( description = "Calculates Sea Ice Extent of Model")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', help="model files to calc ice extent")
parser.add_argument('-o', '--output_file', action = 'store', nargs = 1, help="output file")
args = parser.parse_args()
files = args.files
output_file = args.output_file[0]
var = 'aice'
EXP = output_file[0:-3].split('_')[-1]

####################################
# model data
save_dir = os.path.dirname(files[0])
poles = ['NH', 'SH']
if not os.path.exists(output_file) or npb.utils.FORCE_CALC():
    time_data = []
    for i, f in enumerate(files):
        print(f)
        ds = xr.open_dataset(f)
        npb.icecalc.extent.ds = ds
        if i == 0:
            variables = fnmatch.filter(ds.variables, "aice*")
            variables = [var for var in variables if 'SH' not in var]
        var_data = []
        for j, v in enumerate(variables):
            print(' ',v)
            npb.icecalc.extent.var = v
            if v == 'aice':
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
                    pole_data.append(EXT.expand_dims({"pole" : [p]}))
                dat = xr.concat(pole_data, dim = 'pole')
            var_data.append(dat.expand_dims({"grid" : [grid]}))
        time_data.append(xr.concat(var_data, dim = 'grid'))
    dat = xr.concat(time_data, dim = 'time')
    dat = dat.to_dataset()
    dat.attrs['experiment_name'] = EXP
    default_compression = {"zlib": True, "complevel": 6}
    compress_encoding = {var_name: default_compression for var_name in dat.data_vars}
    dat.to_netcdf(output_file)
    print("WROTE:", output_file)

#####################################
## Calc Extent for Climatology
#file = obs_dir + '/ice_extent/climatology_ice_extent.nc'
#if not os.path.exists(file):
#    ob = 'climatology'
#    print('CALC sea ice extent from', ob)
#    npb.iceobs.sic.top_dir = obs_dir
#    npb.iceobs.sic.ob_name = ob
#    npb.icecalc.extent.var = 'ice_con'
#    pole_data = []
#    for p in poles:
#        npb.iceobs.sic.pole = p
#        dat = npb.iceobs.sic.grab()
#        npb.icecalc.extent.ds = dat
#        data = npb.icecalc.extent.calc()
#        pole_data.append(data.expand_dims({"hemisphere" : [p]}))
#    EXT = xr.concat(pole_data, dim = 'hemispheres')
#    EXT.to_netcdf(file)
#    print("WROTE:", file)

#####################################
## obs data 
#start_date = model_dat['time'][0].values
#end_date = model_dat['time'][-1].values + pd.Timedelta(hours = int(model_dat['forecast_hour'][-1].values))
#time_coords = pd.date_range(start=start_date, end=end_date, freq='D')
#npb.iceobs.sic.top_dir = obs_dir
#npb.icecalc.extent.var = 'ice_con'
#for ob in obs:
#    file = save_dir + '/' + ob + '_ice_extent.nc'
#    npb.iceobs.sic.ob_name = ob
#    if not os.path.exists(file):
#        time_data = []
#        for i, t in enumerate(time_coords):
#            npb.iceobs.sic.dtg = t.strftime('%Y%m%d')
#            pole_data = []
#            for p in poles:
#                npb.iceobs.sic.pole = p
#                dat = npb.iceobs.sic.grab()
#                npb.icecalc.extent.ds = dat
#                EXT = npb.icecalc.extent.calc()
#                #print(EXT)
#                #if EXT:
#                pole_data.append(EXT.expand_dims({"hemisphere" : [p]}))
#            del EXT
#            time_data.append(xr.concat(pole_data, dim = 'hemisphere'))
#        EXT = xr.concat(time_data, dim = 'time')
#        EXT = EXT.assign_attrs({'grid': dat.grid})
#        EXT.to_netcdf(file)
#        print("WROTE:", file)
print('CALC_ice_extent.py SUCCESSFUL')

