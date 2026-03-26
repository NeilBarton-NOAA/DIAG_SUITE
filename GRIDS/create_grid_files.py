#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse
import matplotlib.pyplot as plt
import shutil
import xarray as xr

####################################
parser = argparse.ArgumentParser( description = "Adds forecast hour to CICE netcdf files")
parser.add_argument('-f', '--file', action = 'store', nargs = 1, \
        help="file to read")
parser.add_argument('-o', '--outfile', action = 'store', nargs = 1, \
        help="file to write")
args = parser.parse_args()
f = args.file[0]
f_write = args.outfile[0]
ds = xr.open_dataset(f)
mask = ds['ice_conc'].squeeze()
mask = mask.where(mask.isnull(), 1, drop=False)
mask = mask.fillna(0)
ds['mask'] = (mask.dims, mask.values)   
ds = ds[['lat','lon','Polar_Stereographic_Grid','mask']]
print('WRITING file')
encoding = {
    var: {"zlib": True, "complevel": 6}  # Compression level 1–9
    for var in ds.data_vars
}
f_temp = f_write + '_temp'
ds.to_netcdf(f_temp, format="NETCDF4", encoding=encoding)
shutil.move(f_temp, f_write)
print('WROTE:', f_write)
print('SUCCESSFUL')
