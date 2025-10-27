import numpy as np
import xarray as xr
import xesmf as xe
import pandas as pd
import os

# new utils
def debug(exit_program = False):
    debug = os.environ.get('DEBUG_DIAG', False)
    if (debug == True) and (exit_program == True):
        print("Debug Flag is on, will exit")
        exit(1)
    else:
        return debug

def FORCE_CALC():
    return os.environ.get('FORCE_CALC', 'False').lower() == 'true'

def N_TIMES():
    return int(os.environ.get('N_TIMES', 50))

def stop():
    print('DEBUGING will stop')
    exit(1)

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
    forecast_hours = xr.DataArray(data=tau.values, dims=['forecast_hour'], name='forecast_hour')
    forecast_deltas = forecast_hours.astype('timedelta64[h]')
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
    dir_weights = os.path.dirname(SRC_DATA.file_name) + '/interp_weights'
    os.makedirs(dir_weights, exist_ok=True)
    ########################
    # interp to these grids
    print('interpolating to', DES.grid)
    file_weights = dir_weights + '/regridding_weights_to_' + DES.grid \
                   + '_' + interp_method + '_extrap_' + extrap_method+ '.nc'
    rw = True if os.path.exists(file_weights) else False
    ############
    if 'land_mask' in DES.variables:
        DES['mask'] = (DES['land_mask'].dims, DES['land_mask'].values)
    regridder = xe.Regridder(SRC_DATA, DES, method = interp_method, \
                      extrap_method = extrap_method, \
                      reuse_weights=rw, filename=file_weights)
    TMP = regridder(SRC_DATA)
    TMP = TMP.where(DES['mask'].astype(bool))
    return TMP

