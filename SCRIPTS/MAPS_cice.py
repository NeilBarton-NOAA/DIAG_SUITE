#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse, os, sys, regionmask
import glob as glob
import numpy as np
import xarray as xr
import xesmf as xe
import holoviews as hv
import geoviews as gv
import geoviews.feature as gf
import cartopy.crs as crs
from holoviews.operation.datashader import rasterize
from holoviews.operation import contours as hv_contours 
from pathlib import Path
import matplotlib.pyplot as plt
import cartopy.feature as cfeature
p = os.getenv("pydiag_tools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pydiag_tools as diag_tools
gv.extension('bokeh')

####################################
def get_preprocessor(vars_to_keep, forecast_hours, time_slice = None):
    def inner_preprocess(ds):
        ds = ds[vars_to_keep].sel(forecast_hour = forecast_hours, method = "nearest")
        if time_slice:
            ds = ds.isel(time = (slice(0,None,time_slice)))
        return ds
    return inner_preprocess

def hv_map(ds, v):
    anal_ds = gv.Dataset(ds_analysis.sel(name = n.values), kdims=anal_dims, vdims=['aice'])
    anal_mesh = anal_ds.to(gv.QuadMesh, ['lon', 'lat'], 'aice', ['time', 'forecast_day'])
    ds_var = ds[v].sel(name=n).where(ds['aice'].sel(name=n) != 0 , drop = False)
    if v == 'aice':
        v_min, v_max = float(0.0), float(1.0)
    elif v == 'albsni':
        v_min, v_max = float(0.0), float(100.0)
    else:
        v_min, v_max = float(ds_var.min().values), float(ds_var.max().values)       
    all_dims = list(ds_var.dims)
    gv_ds = gv.Dataset(ds_var, kdims=all_dims, vdims=[v])
    mesh = gv_ds.to(gv.QuadMesh, ['lon','lat'], v, ['time', 'forecast_day'])
    for p in ['NH', 'SH']:
        label = str(ds.time.dt.year.values[0]) + '-' + str(ds.time.dt.month.values[0]).zfill(2)
        f_name = save_dir + '/' + label + '_' + str(n.values) + '_' + p + '_' + v + '.html'
        f = Path(f_name)
        if not f.is_file():
            print(n.values,v,p)
            grid_lines = gv.project(gv.feature.grid(), projection=p_options[p]['crs']).opts(
                                    line_color='gray', line_dash='dotted', line_width=2)
            projected = rasterize(gv.project(mesh, projection=p_options[p]['crs']))
            plot = projected.opts(gv.opts.Image(
                               projection=p_options[p]['crs'], 
                               cmap='viridis', colorbar=True,
                               width=700, height=650,
                               clim=(v_min, v_max),
                               tools=['hover'],
                               xlim=p_options[p]['x'],ylim=p_options[p]['y'],
                               global_extent=False,framewise=True)
                              ) * gf.coastline() * grid_lines
            if config['maps']['contour_sic_analysis']:
                anal_mesh = gv.project(anal_mesh, projection=p_options[p]['crs'])
                contours = hv_contours(anal_mesh, levels = [0.15]).opts(
                                   gv.opts.Contours(line_color='darkgrey',cmap=['darkgrey'],
                                   line_width=3.0,show_legend=False))
            plot = plot *contours
            print('SAVING ', f_name)
            hv.save(plot, f_name, fmt='html', resources='inline')
        else:
            print('Already Saved', f_name)
####################################
def main():
    ########################
    # parse and configuration
    parser = argparse.ArgumentParser( description = "Plot Ice Extent between Runs and Observations")
    parser.add_argument('-e', '--experiments_dir', action = 'store', nargs = '+', \
        help="directories of the experiments")
    parser.add_argument('-y', '--yaml', action = 'store', nargs = 1, \
        help="yaml file")
    args = parser.parse_args()
    exp_dirs = args.experiments_dir
    config = diag_tools.utils.load_yaml(args.yaml[0])
    poles = ['NH', 'SH']
    variables = config['variables']['ice'] + ['tmask']
    forecast_days = config['maps']['forecast_days']
    forecast_hours = np.array(forecast_days)*24.0
    save_dir = config['save_dir'] 
    ####################################
    # grab ice extent from models
    DATS, exps = [], []
    for e in exp_dirs:
        files = glob.glob(e + '/ice*nc')
        ds = xr.open_mfdataset(files, preprocess=get_preprocessor(variables, forecast_hours),
                                chunks={}, parallel=True, coords="minimal", data_vars="minimal",compat="override")
        exp = Path(e).name
        exps.append(exp)
        DATS.append(ds.expand_dims({"name" : [exp]}))
    ds = xr.concat(DATS, dim = 'name') 
    
    ####################################
    # edit ds for maps 
    ds['forecast_day'] = ds['forecast_hour'] / 24.0
    ds = ds.swap_dims({'forecast_hour': 'forecast_day'})
    ds = ds.drop_vars('forecast_hour')
    
    ####################################
    # interpolate to reg lat/lon grid
    ds = ds.rename({'TLAT': 'lat', 'TLON': 'lon'})
    ds = ds.chunk({'nj': -1, 'ni': -1})
    ds['mask'] = ds['tmask']
    for v in config['variables']['ice']:
        ds[v] = ds[v].where(ds['mask'] == 1, drop = False)
    # DES Grid
    res = config['maps']['interpolation_grid']
    DES = xr.Dataset({"lat": (["lat"], np.arange(-90 + (res/2), 90, res)), 
                      "lon": (["lon"], np.arange(-180 + (res/2), 180, res)),})
    land_mask = regionmask.defined_regions.natural_earth_v5_0_0.land_10
    DES['mask'] = xr.DataArray(np.isnan(land_mask.mask(DES['lon'].values, DES['lat'].values)).astype(int),
                    coords={'lat': DES['lat'].values, 'lon': DES['lon'].values}, name='mask')
    #DES["mask"] = xr.where(DES.lat >= -70.0, DES["mask"], 0)
    # perform interpolation
    DES = DES.assign_attrs({'grid' : str(res) + 'degree' }) 
    ds = diag_tools.utils.interp(ds, DES, extrap_method = None) #, var = var)
    
    ########################
    # create analysis
    if config['maps']['contour_sic_analysis']:
        analysis = ds['aice'].isel(forecast_day=0)
        ds_analysis = analysis.broadcast_like(ds)
        anal_dims = list(ds_analysis.dims)
    
    ########################
    # create plot
    p_options = {
        "NH": {"crs": crs.NorthPolarStereo(), "x": (-4000000, 4000000), "y": (-4000000, 4000000)},
        "SH": {"crs": crs.SouthPolarStereo(), "x": (-4000000, 4000000), "y" : (-4000000, 4000000)}}   
    for label, ds_group in ds.groupby(ds.time.dt.strftime("%Y-%m")):
        print(label)
        for n in ds.name:
            for v in config['variables']['ice']:
                hv_map(ds, v) 
         
if __name__ == "__main__":
    main()
