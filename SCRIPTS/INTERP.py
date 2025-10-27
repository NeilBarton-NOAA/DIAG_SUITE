#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse
import glob 
import os
import sys
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Interp data and writes fields in Ones and Zeros")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', \
        help="CICE files to interpolate")
parser.add_argument('-od', '--obsdir', action = 'store', nargs = 1, \
        help="top directory for observations")
parser.add_argument('-obs', '--obs', action = 'store', nargs = '+', \
        help="observations to use")
args = parser.parse_args()
files = args.files
var = 'aice'
obs_dir = args.obsdir[0]
obs = args.obs

########################
# get model results
npb.iceobs.sic.top_dir = obs_dir

########################
# obs grid
ds_model = xr.open_dataset(files[0])
dtg = ds_model.time.dt.strftime('%Y%m%d').values[0]
npb.iceobs.sic.dtg = dtg
obs.append('climatology')
GRIDS = []
for ob in obs:
    if ob != 'analysis':
        print(ob)
        npb.iceobs.sic.ob_name = ob
        for p in ['NH', 'SH']:
            npb.iceobs.sic.pole = p
            GRIDS.append(npb.iceobs.sic.grab())

########################
# loop through files
for f in files:
    print(f)
    ds_model = xr.open_dataset(f)
    ds_model = ds_model.assign_attrs({'file_name' : f }) 
    file_save = os.path.dirname(ds_model.file_name) + '/INTERP_' + os.path.basename(ds_model.file_name) 
    if not os.path.exists(file_save) or npb.utils.FORCE_CALC():
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
        encoding = { var: {"zlib": True, "complevel": 6} for var in ds_model.data_vars }
        ds_model.to_netcdf(file_save, format="NETCDF4", encoding=encoding)
        print('WROTE:', file_save)
        npb.utils.debug()
