#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse
import glob 
import os
import shutil
import sys
import xarray as xr
path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.getenv("PYTHON_TOOLS")) if 'slurm' in path else sys.path.append(path)
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Interp data and writes fields in Ones and Zeros")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', \
        help="CICE files to interpolate")
parser.add_argument('-obs', '--observations', action = 'store', nargs = '+', \
        help="observations to interpolate aice to their grid")
parser.add_argument('-o', '--output_file', action = 'store', nargs = 1, \
        help="observations to use")
args = parser.parse_args()
files = args.files
obs = args.observations
f_out = args.output_file[0]
var = 'aice'

########################
# get obs grid
ds_model = xr.open_dataset(files[0])
dtg = ds_model.time.dt.strftime('%Y%m%d').values[0]
npb.iceobs.sic.dtg = dtg
GRIDS = []
for ob in obs:
    if ob != 'analysis':
        print(ob)
        npb.iceobs.sic.directory = ob
        for p in ['NH', 'SH']:
            npb.iceobs.sic.pole = p
            GRIDS.append(npb.iceobs.sic.grab())

########################
# loop through files
for f in files:
    print(f)
    ds_model = xr.open_dataset(f)
    ds_model = ds_model[[var] + ['tmask', 'tarea']]
    ds_model = ds_model.assign_attrs({'file_name' : f }) 
    if not os.path.exists(f_out) or npb.utils.FORCE_CALC():
        ############
        # CICE Data has TLAT instead of lat
        ds_model = ds_model.rename({'TLAT': 'lat', 'TLON': 'lon'})
        ds_model['mask'] = (ds_model['tmask'].dims, ds_model['tmask'].values)
        ds_model['aice'] = ds_model['aice'].where(ds_model['mask'] == 1, drop = False)
        ds_model = npb.utils.daily_taus(ds_model, 'aice')
        for GRID in GRIDS:
            grid = GRID.grid
            DAT = npb.utils.interp(ds_model, GRID) #, var = var)
            if GRID.grid[2:4] == '25':
                DAT = DAT.rename_dims({'y': 'y' + grid, 'x': 'x' + grid})
            else:
                DAT = DAT.rename_dims({'yc': 'y' + grid, 'xc': 'x' + grid})
            new_var = var + grid
            print('Adding to Dataset', new_var)
            ds_model['lat' + grid ] = (DAT['mask'].dims, GRID['lat'].values)
            ds_model['lon' + grid ] = (DAT['mask'].dims, GRID['lon'].values)
            ds_model[new_var] = (DAT[var].dims, DAT[var].values)
            del DAT
        ds_model = ds_model.drop_vars('ULON', errors='ignore')
        ds_model = ds_model.drop_vars('ULAT', errors='ignore')
        encoding = { var: {"zlib": True, "complevel": 6} for var in ds_model.data_vars }
        f_temp = f_out + '_temp'
        ds_model.to_netcdf(f_temp, format="NETCDF4", encoding=encoding)
        shutil.move(f_temp, f_out)
        print('WROTE:', f_out)
        print('INTERP_aice.py SUCCESSFUL')
        npb.utils.debug()
    else:
        print('FILE ALREADY PRESENT:', f_out)
