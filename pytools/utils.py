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

def ds_addvar(ds, var, ds_save=None):
    print('adding variable', var)
    # Check if variable already exists in ds
    if var in ds:
        return ds
    # Handle derived Zarr cachingif ds_save path is provided
    if (ds_save is not None) and (ds_save.exists()):
        print(f"LOADING CACHED {var} FROM: {ds_save}")
        ds_derived = xr.open_dataset(ds_save, engine="zarr")
        ds[var] = ds_derived[var]
        return ds
    # --- CALCULATION LOGIC ---
    if var in ['ice_extent', 'snow_volume', 'ice_volume']:
        # 1. Pull 2D static coordinates into RAM as small NumPy arrays (~a few KB)
        tlat = ds['TLAT'].values if hasattr(ds['TLAT'], 'values') else ds['TLAT'].compute().values
        area = ds['cell_area'].values if hasattr(ds['cell_area'], 'values') else ds['cell_area'].compute().values
        area = area / 1e12  # Convert m^2 to 10^6 km^2 upfront
        # 2. Create 2D hemisphere boolean masks
        nh_mask = tlat > 20
        sh_mask = tlat < -20
        # 3. Streamlined computation using .where()
        if var == 'ice_extent':
            ice_mask = ds['aice'] >= 0.15
            nh_val = (ds['cell_area'].where(ice_mask & nh_mask)).sum(dim=['nj', 'ni']) / 1e12
            sh_val = (ds['cell_area'].where(ice_mask & sh_mask)).sum(dim=['nj', 'ni']) / 1e12
        elif var == 'snow_volume':
            snow_vol = ds['aice'] * ds['hs'] * area
            nh_val = snow_vol.where(nh_mask).sum(dim=['nj', 'ni'])
            sh_val = snow_vol.where(sh_mask).sum(dim=['nj', 'ni'])
        elif var == 'ice_volume':
            ice_vol = ds['aice'] * ds['hi'] * area
            nh_val = ice_vol.where(nh_mask).sum(dim=['nj', 'ni'])
            sh_val = ice_vol.where(sh_mask).sum(dim=['nj', 'ni'])
        # 4. Concatenate both hemispheres
        nh_val = nh_val.expand_dims({'hemisphere': ['NH']})
        sh_val = sh_val.expand_dims({'hemisphere': ['SH']})
        # 5. Compute the final collapsed timeseries (~few KB total size)
        res_var = xr.concat([nh_val, sh_val], dim='hemisphere').compute()
        ds[var] = res_var
    elif var == 'SSS':
        ds[var] = ds['so'].isel(z_l=0)
    elif var == 'SVA':
        h = xr.DataArray(get_thickness(ds['z_l']), coords={'z_l': ds.z_l}, dims=['z_l'])
        salt = ds['so'] * h
        salt_w = salt.sum(dim='z_l') / h.sum(dim='z_l')
        ds[var] = salt_w.where(ds['SST'].notnull())
    elif var == 'WWV':
        R = 6371000  # Radius of Earth in meters
        d_lat = np.radians(1.0)
        d_lon = np.radians(1.0)
        area_grid = (R**2) * d_lat * d_lon * np.cos(np.radians(ds['latitude']))
        mld_broadcast, area_grid = xr.broadcast(ds['dt20c'], area_grid)
        ds[var] = (ds['dt20c'] * area_grid) / 1e9
    elif var == 'ocnheat':
        ds['ocnheat'] = ds['ocnheat'] / 1e9
    elif var == 'T300':
        rho0 = 1035.0
        cp = 3991.8679
        ds['h'] = xr.DataArray(get_thickness(ds['z_l']), coords={'z_l': ds.z_l}, dims=['z_l'])
        depth_bottom = ds.h.cumsum(dim='z_l')
        depth_top = depth_bottom - ds.h
        dz_300 = np.maximum(0, np.minimum(depth_bottom, 300) - depth_top)
        ohc_per_m2 = (ds.temp * dz_300 * rho0 * cp).sum(dim='z_l')
        ds[var] = ohc_per_m2 / 1e9
    # --- SAVE TO ZARR CACHE ---
    if ds_save is not None:
        print(f"SAVING DERIVED VAR {var} TO: {ds_save}")
        da_out = ds[var].copy()
        # 2. Reset coordinates that aren't strictly core dimensions
        # Keeps dimensions like ['experiment', 'member', 'time', 'hemisphere']
        keep_dims = list(da_out.dims)
        da_out = da_out.drop_vars([c for c in da_out.coords if c not in keep_dims])
        # 3. Create a clean Dataset and force object coordinates (like hemisphere strings) to str dtype
        ds_out = xr.Dataset({var: da_out})
        for c in ds_out.coords:
            if ds_out[c].dtype == object:
                ds_out[c] = ds_out[c].astype(str)
        # 4. Save clean dataset to Zarr
        ds_out.to_zarr(ds_save, mode='w', consolidated=True)
    return ds










    print('adding variable', var)
    if var in ['ice_extent', 'snow_volume', 'ice_volume']:
        # 1. Pull 2D static coordinates into RAM as small NumPy arrays (~a few KB)
        # This prevents Dask from broadcasting 2D grid metrics across member/time/exp dimensions
        tlat = ds['TLAT'].values if hasattr(ds['TLAT'], 'values') else ds['TLAT'].compute().values
        area = ds['cell_area'].values if hasattr(ds['cell_area'], 'values') else ds['cell_area'].compute().values
        area = area / 1e12  # Convert m^2 to 10^6 km^2 upfront

        # 2. Create 2D hemisphere boolean masks
        nh_mask = tlat > 20
        sh_mask = tlat < -20

        # 3. Streamlined computation using .where() rather than large array multiplication
        if var == 'ice_extent':
            # Create a boolean mask for ice extent (aice >= 15%)
            ice_mask = ds['aice'] >= 0.15
            
            # Apply spatial area and sum over grid dimensions lazily
            nh_val = (ds['cell_area'].where(ice_mask & nh_mask)).sum(dim=['nj', 'ni']) / 1e12
            sh_val = (ds['cell_area'].where(ice_mask & sh_mask)).sum(dim=['nj', 'ni']) / 1e12

        elif var == 'snow_volume':
            snow_vol = ds['aice'] * ds['hs'] * area
            nh_val = snow_vol.where(nh_mask).sum(dim=['nj', 'ni'])
            sh_val = snow_vol.where(sh_mask).sum(dim=['nj', 'ni'])

        elif var == 'ice_volume':
            ice_vol = ds['aice'] * ds['hi'] * area
            nh_val = ice_vol.where(nh_mask).sum(dim=['nj', 'ni'])
            sh_val = ice_vol.where(sh_mask).sum(dim=['nj', 'ni'])

        # 4. Concatenate both hemispheres into a single spatial-collapsed array
        nh_val = nh_val.expand_dims({'hemisphere': ['NH']})
        sh_val = sh_val.expand_dims({'hemisphere': ['SH']})
        
        # 5. Compute the final collapsed timeseries (~few KB total size)
        ds[var] = xr.concat([nh_val, sh_val], dim='hemisphere').compute()
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
    elif analysis_period == 'all':
        da = da.mean(dim = 'time', keep_attrs=True)
        da.attrs['period_label'] = 'ALL'
        forecast_times = forecast_time #.sel(time = da.period_label).squeeze(dim='time').drop_vars('time')
    elif len(analysis_period) == 6: #YYYYMM
        da.attrs['period_label'] = f"{analysis_period[:4]}-{analysis_period[4:]}"
        da = da.sel(time = da.period_label).squeeze(dim='time').drop_vars('time')
        forecast_times = forecast_time.sel(time = da.period_label).squeeze(dim='time').drop_vars('time')
    else:
        print('FATAL: analysis_period unknown', analysis_period)
        exit(1)
    return da, forecast_times

