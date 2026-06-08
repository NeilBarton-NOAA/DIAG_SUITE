#!/usr/bin/env python3 
import datetime
import os
import sys
import requests
import matplotlib.pyplot as plt
import xarray as xr
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../SCRIPTS' )
import PYTHON_TOOLS as npb

var = sys.argv[1]
dtg = sys.argv[2]
output_dir = sys.argv[3] 
os.makedirs(output_dir, exist_ok = True)

########################
# interpolate onto CICE grid
mask_file = os.path.dirname(os.path.abspath(__file__)) + '/CICE_mx025.nc'
print(mask_file)
CICE_GRID = xr.open_dataset(mask_file)
CICE_GRID = CICE_GRID.rename({'TLAT': 'lat', 'TLON': 'lon'})
CICE_GRID['mask'] = (CICE_GRID['tmask'].dims, CICE_GRID['tmask'].values)
CICE_GRID = CICE_GRID.assign_attrs({'grid' : 'mx025'})

########################
# grab data
dtg = f"{dtg[0:4]}-{dtg[4:6]}-{dtg[6:]}"
f_save = output_dir + '/OSTIA_' + var + '_' + dtg + '.nc'
if not os.path.exists(f_save) or npb.utils.FORCE_CALC(): 
    npb.ocnobs.cm.dtg = dtg
    npb.ocnobs.cm.var = var
    dat = npb.ocnobs.cm.grab()
    dat = dat.assign_attrs({'file_name' : f_save})
    dat = npb.utils.interp(dat, CICE_GRID)
    dat['tmask'] = CICE_GRID['tmask']
    dat['tarea'] = CICE_GRID['tarea']
    encoding = { var: {"zlib": True, "complevel": 9} for var in dat.data_vars }
    dat.to_netcdf(f_save, format="NETCDF4", encoding=encoding)
    print("WROTE: ", f_save)
else:
    print('Already Produced', f_save)
