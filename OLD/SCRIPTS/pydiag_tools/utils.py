import numpy as np
import xarray as xr
import xesmf as xe
import pandas as pd
from pathlib import Path
import os, shutil

def make_cyclic(ds, lon_dim='lon'):
    """
    Manually adds a cyclic point to 2D coordinates and all variables 
    sharing the longitude dimension.
    """
    # 1. Identify which variables/coords need to be expanded
    # We look for anything that has the 'lon' dimension
    vars_to_expand = [v for v in ds.variables if lon_dim in ds[v].dims]
    new_data_vars = {}
    for v in vars_to_expand:
        data = ds[v].values
        # Determine which axis is the longitude dimension
        # (Usually it's the last one, but this is safer)
        axis = ds[v].dims.index(lon_dim)
        # Slice the first column: data[:, :1] for 2D, or [:, :, :1] for 3D
        # We use 'np.take' or a slice object to handle any dimension count
        slice_obj = [slice(None)] * data.ndim
        slice_obj[axis] = slice(0, 1)
        first_col = data[tuple(slice_obj)]
        # Concatenate the first column to the end
        new_data_vars[v] = (ds[v].dims, np.concatenate([data, first_col], axis=axis))
    # 2. Build the new Dataset with the expanded variables
    # We start with the variables that DIDN'T change (to keep metadata)
    ds_remainder = ds.drop_vars(vars_to_expand)
    ds_cyclic = xr.Dataset(new_data_vars, attrs=ds.attrs)
    # Merge them back together
    return xr.merge([ds_remainder, ds_cyclic])

def all_dtgs(ds):
    t_grid, f_grid = np.meshgrid(ds['time'].values, ds['forecast_hour'].values)
    f_delta = pd.to_timedelta(f_grid.ravel(), unit='h').values.reshape(f_grid.shape)
    valid_grid = t_grid + f_delta
    unique_times = np.unique(valid_grid)
    dtgs = pd.to_datetime(unique_times).strftime('%Y%m%d').unique().tolist()
    return dtgs

def ds_to_netcdf(ds, f_write, complevel = 6):
    print('WRITING:', f_write)
    encoding = {var: {"zlib": True, "complevel": complevel}  # Compression level 1–9
                for var in ds.data_vars }
    f_temp = f_write + '_temp'
    file_path = Path(f_temp)
    file_path.unlink(missing_ok=True)
    ds.to_netcdf(f_temp, format="NETCDF4", encoding=encoding)
    shutil.move(f_temp, f_write)
    print('WROTE:', f_write)

def load_yaml(path):
    import yaml
    with open(path, 'r') as f:
        raw_yaml = f.read()
        expanded_yaml = os.path.expandvars(raw_yaml)
    return yaml.safe_load(expanded_yaml)

def debug(exit_program = False):
    debug = os.environ.get('DEBUG_DIAG', 'False').lower() in ('true', 't')
    if (debug == True) and (exit_program == True):
        print("Debug Flag is on, will exit")
        exit(1)
    else:
        return debug

def daily_taus(DAT, var):
    if ('_h' in var):
        print('MODEL output in hours and OBS in days: will only examine days')
        min_tau = np.min(DAT['tau'].values)
        if min_tau != 0:
            min_tau = min_tau + (24 - min_tau)
        u_taus = np.arange(min_tau, np.max(DAT['tau'].values) + 24 , 24)
        DAT['new_tau'] = u_taus
        DAT['new_' + var] = (('new_tau', 'time', 'nj', 'ni'), DAT[var].sel(tau = u_taus).values)
        DAT = DAT.drop(var)
        DAT = DAT.drop('tau')
        DAT = DAT.rename({'new_tau': 'tau', 'new_' + var: var})
    return DAT

def add_forecast_hour(OBS, last_forecast_hour):
    t_last = OBS['time'][0] + np.timedelta64(int(last_forecast_hour), 'h')
    times = OBS['time'].sel(time = slice(OBS['time'][0], t_last))
    end_date = OBS['time'][-1].values - pd.Timedelta(hours = int(last_forecast_hour))
    init_times = OBS['time'].sel(time=slice(None, end_date))
    tau = (times - times[0]) / np.timedelta64(1,'h')
    hours_np = tau.values
    deltas_h = hours_np.astype('timedelta64[h]')
    deltas_ns = deltas_h.astype('timedelta64[ns]')
    forecast_deltas = xr.DataArray(data=deltas_ns, dims=['forecast_hour'], name='forecast_hour')
    target_datetimes = xr.DataArray(init_times, dims=['time']) + forecast_deltas
    all_required_times = np.unique(target_datetimes.values)
    OBS = OBS.reindex(time=all_required_times)
    OBS = OBS.sel(time=target_datetimes)
    OBS['valid_times'] = OBS['time']
    OBS = OBS.drop_vars('time')
    OBS['forecast_hour'] = tau.values
    OBS['time'] = OBS['valid_times'].values[:,0]
    return OBS 

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

