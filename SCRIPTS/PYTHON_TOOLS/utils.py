import numpy as np
import xarray as xr
import pandas as pd
# new utils
def debug(exit_program = False):
    import os
    debug = os.environ.get('DEBUG_DIAG', False)
    if (debug == True) and (exit_program == True):
        print("Debug Flag is on, will exit")
        exit(1)
    else:
        return debug

def add_forecast_hour(OBS, last_forecast_hour):
    t_last = OBS['time'][0] + np.timedelta64(int(last_forecast_hour), 'h')
    times = OBS['time'].sel(time = slice(OBS['time'][0], t_last))
    end_date = OBS['time'][-1].values - pd.Timedelta(hours = int(last_forecast_hour))
    init_times = OBS['time'].sel(time=slice(None, end_date))
    tau = (times - times[0]) / np.timedelta64(1,'h')
    forecast_hours = xr.DataArray(data=tau.values, dims=['forecast_hour'], name='forecast_hour')
    forecast_deltas = forecast_hours.astype('timedelta64[h]')
    target_datetimes = xr.DataArray(init_times, dims=['time']) + forecast_deltas
    print(target_datetimes)
    print(OBS['time'])
    OBS = OBS.sel(time=target_datetimes[-3::])
    OBS['valid_times'] = OBS['time']
    OBS = OBS.drop_vars('time')
    OBS['forecast_hour'] = tau.values
    OBS['time'] = OBS['valid_times'].values[:,0]
    exit(1)
    return OBS 

def interp(ds_model, ds_obss, var = 'aice_d', force_calc = True):
    file_save = os.path.dirname(ds_model.file_name) + '/INTERP_' + os.path.basename(ds_model.file_name) 
    if (os.path.exists(file_save) == False) or (force_calc == True):
        ds_model = ds_model.rename({'TLAT': 'lat', 'TLON': 'lon'})
        ds_model['mask'] = (ds_model['tmask'].dims, ds_model['tmask'].values)
        ds_model[var] = ds_model[var].where(ds_model['mask'] == 1, drop = False)
        ds_model = daily_taus(ds_model, var)
        ################################################
        # create regridder/interpolate data/ make new data array
        dir_weights = os.path.dirname(ds_model.file_name) + '/interp_weights'
        os.makedirs(dir_weights, exist_ok=True)
        # remove data sets if they have the same grid as another
        GRIDS, UNIQUE = set(), []
        for ds_obs in ds_obss:
            if ds_obs.grid not in GRIDS:
                UNIQUE.append(ds_obs)
                GRIDS.add(ds_obs.grid)
        # interp to these grids
        for ds_obs in UNIQUE:
            ############
            # determine grid name
            interp_method, extrap_method = 'bilinear', 'nearest_s2d'
            file_weights = dir_weights + '/regridding_weights_CICE025_to_' + \
                           ds_obs.grid + 'km_' + interp_method + '_extrap_' + extrap_method+ '.nc'
            ############
            # interpolate if needed
            print('interpolating to', ds_obs.grid)
            ds_obs['mask'] = (ds_obs['land_mask'].dims, ds_obs['land_mask'].values)
            rw = True if os.path.exists(file_weights) else False
            regridder = xe.Regridder(ds_model, ds_obs, method = interp_method, \
                                     extrap_method = extrap_method, \
                                     reuse_weights=rw, filename=file_weights)
            TMP = regridder(ds_model)
            TMP = TMP.where(ds_obs['mask'].astype(bool))
            if ds_obs.grid[2:4] == '25':
                TMP = TMP.rename_dims({'y': 'y' + ds_obs.grid, 'x': 'x' + ds_obs.grid})
            else:
                TMP = TMP.rename_dims({'yc': 'y' + ds_obs.grid, 'xc': 'x' + ds_obs.grid})
            new_var = var + ds_obs.grid
            print('Adding to Dataset', new_var)
            ds_model['lat' + ds_obs.grid ] = (TMP['mask'].dims, ds_obs['lat'].values)
            ds_model['lon' + ds_obs.grid ] = (TMP['mask'].dims, ds_obs['lon'].values)
            ds_model[new_var] = (TMP[var].dims, TMP[var].values)
            ds_model[new_var + '_binary'] = xr.where(ds_model[new_var] > 0.15,1,0).astype("int32")
            del TMP
        # orign grid changes for binary data
        ds_model[var + '_binary'] = xr.where(ds_model[var] > 0.15,1,0).astype("int32")
        ds_model = ds_model.rename({'lat': 'TLAT', 'lon': 'TLON'})
        # write file
        encoding = { var: {"zlib": True, "complevel": 6} for var in ds_model.data_vars }

