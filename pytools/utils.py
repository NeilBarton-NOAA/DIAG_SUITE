import glob
import pandas as pd
from pathlib import Path
import numpy as np
import os
import xesmf as xe
import xarray as xr

def load_yaml(path):
    import yaml
    with open(path, 'r') as f:
        raw_yaml = f.read()
        expanded_yaml = os.path.expandvars(raw_yaml)
    return yaml.safe_load(expanded_yaml)

def grabdata(ds_save, exps, ymd, FORCE_CALC = False):
    if not ds_save.exists() or FORCE_CALC:
        ds_all = []
        for i, e_name in enumerate(exps.keys()):
            e = exps[e_name]
            print(e_name)
            ds_ocn, ds_ice = [], []
            mems = len(glob.glob(e + "/sfs." + ymd + "/00/mem*/products/ocean/netcdf/1p00/"))
            for mem in range(mems):
                print("  member: ", mem)
                #print(e + d)
                # MOM6 output
                d = "/sfs." + ymd + "/00/mem" + str(mem).zfill(3) + \
                    "/products/ocean/netcdf/1p00/sfs.ocean*monthly_avg*nc"
                files = glob.glob(e + d)
                ds = xr.open_mfdataset(files)
                vars_month = ['ocnheat', 'dt20c']
                for v in vars_month:
                    d = "/sfs." + ymd + "/00/mem" + str(mem).zfill(3) + \
                        "/products/ocean/netcdf/1p00/sfs." + v + "*monthly_avg*nc"
                    files = glob.glob(e + d)
                    dd = xr.open_mfdataset(files)
                    ds[v] = (ds['SST'].dims, dd[v].values)
                time_strings = ds.time.dt.strftime("%Y-%m-15")
                ds = ds.assign_coords(time=pd.to_datetime(time_strings))
                ds_ocn.append(ds.expand_dims({'member' : [mem]}))
                # CICE output
                d = "/sfs." + ymd + "/00/mem" + str(mem).zfill(3) + \
                    "/products/ice/netcdf/native/sfs.*monthly_avg*nc"
                files = glob.glob(e + d)
                ds = xr.open_mfdataset(files)
                rename_map = {name: name[:-2] for name in ds.variables if name.endswith('_h') or name.endswith('_d')}
                ds = ds.rename(rename_map)
                ds = ds.assign_coords(time=pd.to_datetime(time_strings))
                ds_ice.append(ds.expand_dims({'member' : [mem]}))
            ds_ocn = xr.concat(ds_ocn, dim = 'member')
            ds_ocn = ds_ocn.expand_dims({'component' : ['ocn']})
            ds_ice = xr.concat(ds_ice, dim = 'member')
            ds_ice = ds_ice.expand_dims({'component' : ['ice']})
            ds = xr.concat([ds_ocn, ds_ice], dim = 'component')
            ds_all.append(ds.expand_dims({'experiment': [e_name] }))
        ds = xr.concat(ds_all, dim = 'experiment')
        ds = ds.drop_vars("time_bnds")
        ds = ds.chunk({'time': 12, 'member': -1, 'z_l': 1, 'nj': -1, 'ni': -1, 'latitude':-1, 'longitude':-1})
        ds.to_zarr(ds_save, consolidated=True, mode = 'w')
        print('SAVED:', ds_save)
    else:
        print('OPENING:', ds_save)
        ds = xr.open_dataset(ds_save, engine="zarr")
    return(ds)

def get_thickness(z_l):
    dz = np.diff(z_l)
    z_i = [0]
    # Intermediate interfaces are mid-way between centers
    for i in range(len(dz)):
        z_i.append(z_l[i] + dz[i]/2)
    # The last interface is extrapolated: 
    # (Last center + distance from the previous interface to that center)
    last_gap = z_l[-1] - z_i[-1]
    z_i.append(z_l[-1] + last_gap)
    z_i = np.array(z_i)
    return np.diff(z_i)

def ds_addvar(ds, var):
    if var == 'ice_extent':
        NH = ds['cell_area'].where((ds['TLAT'] > 20) & (ds['aice'] >= 0.15)).sum(dim = ['nj', 'ni']) / 1e12
        SH = ds['cell_area'].where((ds['TLAT'] < -20) & (ds['aice'] >= 0.15)).sum(dim = ['nj', 'ni']) / 1e12
        NH = NH.expand_dims({'hemisphere': ['NH']})
        SH = SH.expand_dims({'hemisphere': ['SH']})
        ds[var] = xr.concat([NH, SH], dim = 'hemisphere')
    if var == 'snow_volume':
        NH = (ds['aice'] * ds['hs'] * ds['cell_area']).where(ds['TLAT'] > 20).sum(dim = ['nj', 'ni']) / 1e12
        SH = (ds['aice'] * ds['hs'] * ds['cell_area']).where(ds['TLAT'] < -20).sum(dim = ['nj', 'ni']) / 1e12
        NH = NH.expand_dims({'hemisphere': ['NH']})
        SH = SH.expand_dims({'hemisphere': ['SH']})
        ds[var] = xr.concat([NH, SH], dim = 'hemisphere')
    if var == 'ice_volume':
        NH = (ds['aice'] * ds['hi'] * ds['cell_area']).where(ds['TLAT'] > 20).sum(dim = ['nj', 'ni']) / 1e12
        SH = (ds['aice'] * ds['hi'] * ds['cell_area']).where(ds['TLAT'] < -20).sum(dim = ['nj', 'ni']) / 1e12
        NH = NH.expand_dims({'hemisphere': ['NH']})
        SH = SH.expand_dims({'hemisphere': ['SH']})
        ds[var] = xr.concat([NH, SH], dim = 'hemisphere')
    if var == 'SSS':
        ds[var] = ds['so'].isel(z_l = 0 )
    if var == 'SVA':
        h = xr.DataArray(get_thickness(ds['z_l']), coords={'z_l': ds.z_l}, dims=['z_l'])
        salt = ds['so'] * h
        salt_w = salt.sum(dim='z_l') / h.sum(dim='z_l')
        ds[var] = salt_w.where(ds['SST'].notnull())
    if var == 'WWV':
        R = 6371000  # Radius of Earth in meters
        d_lat = np.radians(1.0) # 1 degree in radians
        d_lon = np.radians(1.0) # 1 degree in radians
        area = (R**2) * d_lat * d_lon * np.cos(np.radians(ds['latitude']))
        mld_broadcast, area = xr.broadcast(ds['dt20c'], area)
        ds[var] = (ds['dt20c'] * area) / 1e9
    if var == 'ocnheat':
        ds['ocnheat'] = ds['ocnheat'] / 1e9
    if var == 'T300':
        rho0 = 1035.0
        cp = 3991.8679
        ds['h'] = xr.DataArray(get_thickness(ds['z_l']), coords={'z_l': ds.z_l}, dims=['z_l'])
        depth_bottom = ds.h.cumsum(dim='z_l')
        depth_top = depth_bottom - ds.h
        dz_300 = np.maximum(0, np.minimum(depth_bottom, 300) - depth_top)
        ohc_per_m2 = (ds.temp * dz_300 * rho0 * cp).sum(dim='z_l')
        ds[var] = ohc_per_m2 / 1e9
    return ds

def interp(SRC_DATA, DES, interp_method = 'bilinear', extrap_method = 'nearest_s2d'):
    ########################
    # create regridder/interpolate data/ make new data array
    dir_weights = Path(SRC_DATA.file_name).parent if hasattr(SRC_DATA, 'file_name') else Path.cwd() / 'GRIDS'
    os.makedirs(dir_weights, exist_ok=True)
    ########################
    # interp to these grids
    print('interpolating to', DES.grid)
    file_weights = str(dir_weights) + '/regridding_weights_to_' + DES.grid \
                   + '_' + interp_method + '_extrap_' + str(extrap_method) + '.nc'
    rw = True if os.path.exists(file_weights) else False
    ############
    if 'land_mask' in DES.variables:
        DES['mask'] = (DES['land_mask'].dims, DES['land_mask'].values)
    ############
    #2D array for regridder
    spatial_coords = ['ni', 'nj']
    extra_dims = {d: 0 for d in SRC_DATA.dims if d not in spatial_coords} 
    grid_template = SRC_DATA.isel(extra_dims)
    ############
    # regrid/interpolate
    regridder = xe.Regridder(grid_template, DES, method = interp_method, \
                      extrap_method = extrap_method, periodic=True, \
                      reuse_weights=rw, filename=file_weights)
    TMP = regridder(SRC_DATA)
    if 'land_mask' in DES.variables:
        TMP = TMP.where(DES['mask'].astype(bool))
    return TMP
    
def get_area(ds, da):
    if (da.model == 'ice') and (da.name not in ['ice_extent', 'ice_volume', 'snow_volume']):
        da_aice = ds['aice'].sel(component='ice')
        cell_area = ds['cell_area'].sel(component='ice')
        cell_area = cell_area.isel(time = 0)
        da = da.where(da_aice > 0, drop = False) 
        if da.name == 'albsni': da = da.where(da < 100, drop = False) 
    else:
        cell_area = np.cos(np.deg2rad(ds.latitude))
    return da, cell_area

def sel_analysis_period(da, forecast_time, analysis_period):
    if analysis_period == 'first':
        da.attrs['period_label'] = str(da.time.values[0])[:7]
        da = da.isel(time = 0)
        forecast_times = forecast_time.isel(time = 0)
    elif len(analysis_period[0]) == 6: #YYYYMM
        da.attrs['period_label'] = f"{analysis_period[0][:4]}-{analysis_period[0][4:]}"
        da = da.sel(time = da.period_label).squeeze(dim='time').drop_vars('time')
        forecast_times = forecast_time.sel(time = da.period_label).squeeze(dim='time').drop_vars('time')
    else:
        print('FATAL: analysis_period unknown', analysis_period[0])
        exit(1)
    return da, forecast_times

