import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import xesmf as xe
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../PYTHON_TOOLS')
import PYTHON_TOOLS as npb

def to_netcdf(ds, filename):
    default_compression = {"zlib": True, "complevel": 6}
    compress_encoding = {var_name: default_compression for var_name in ds.data_vars}
    ds.to_netcdf(filename, encoding=compress_encoding)
    print('SAVED:', filename)

class extent(object):
    @classmethod
    def calc(cls):
        dat = cls.ds[cls.var]
        dims = cls.ds[cls.var].dims[-2::]
        if 'nj' in cls.ds[cls.var].dims:
            DIV = 1e12
            area = cls.ds['tarea']
            dat = cls.ds[cls.var]
            pole_data = []
            for p in ['NH', 'SH']:
                if p == 'NH':
                    EXT = area.where((dat.TLAT > 10) & (dat >= 0.15)).sum(dim = dims) / DIV    
                elif p == 'SH':
                    EXT = area.where((dat.TLAT < -10) & (dat >= 0.15)).sum(dim = dims) / DIV
                EXT = EXT.expand_dims({"hemisphere" : [p]})
                EXT.name = 'extent'
                pole_data.append(EXT)
            ds = xr.concat(pole_data, dim = 'hemisphere')
        else: 
            if cls.var == 'ice_con':
                grid_size = float(cls.ds.grid[0:2])**2.0
            else:
                grid_size = float(cls.ds[cls.var].dims[-1][-2::])**2.0
            area = xr.ones_like(cls.ds[cls.var]) * grid_size
            dat = cls.ds[cls.var]
            DIV = 1e6
            ds = area.where(dat >= 0.15).sum(dim = dims) / DIV
            ds.name = 'extent'
        return ds

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
 
def interp(ds_model, ds_obss, var = 'aice_d', force_calc = True):
    file_save = os.path.dirname(ds_model.file_name) + '/INTERP_' + os.path.basename(ds_model.file_name) 
    if (os.path.exists(file_save) == False) or (force_calc == True):
        ds_model.rename({'TLAT': 'lat', 'TLON': 'lon'})
        ds_model['lat'] = (ds_model['TLAT'].dims, ds_model['TLAT'].values)
        ds_model['lon'] = (ds_model['TLON'].dims, ds_model['TLON'].values)
        ds_model['mask'] = (ds_model['tmask'].dims, ds_model['tmask'].values)
        ds_model[var] = ds_model[var].where(ds_model['mask'] == 1, drop = False)
        ds_model = daily_taus(ds_model, var)
        ################################################
        # create regridder/interpolate data/ make new data array
        dir_weights = os.path.dirname(ds_model.file_name) + '/interp_weights'
        if not os.path.exists(dir_weights):
            os.makedirs(dir_weights)
        INTERP_DSS, INTERP_NAMES = [], []
        for ds_obs in ds_obss:
            if var + ds_obs.grid not in INTERP_NAMES:
                ############
                # determine grid name
                file_weights = dir_weights + '/regridding_weights_CICE025_to_' + ds_obs.grid + 'km.nc'
                ############
                # interpolate if needed
                print('interpolating to', ds_obs.grid)
                ds_obs['mask'] = (ds_obs['land_mask'].dims, ds_obs['land_mask'].values)
                if os.path.exists(file_weights):
                    regridder = xe.Regridder(ds_model, ds_obs, method = 'nearest_s2d', reuse_weights=True, filename=file_weights)
                else:
                    regridder = xe.Regridder(ds_model, ds_obs, method = 'nearest_s2d', reuse_weights=False, filename=file_weights)
                TMP = regridder(ds_model)
                #import matplotlib.pyplot as plt
                #plt.figure(1)
                #plt.imshow(ds_model['aice'][0,0], origin = 'lower'); plt.colorbar()
                #plt.figure(2)
                #plt.imshow(TMP['aice'][0,0]); plt.colorbar(); plt.show()
                #print(TMP)
                #exit(1)
                TMP = TMP.where(ds_obs['mask'].astype(bool))
                if ds_obs.grid[2:4] == '25':
                    TMP = TMP.rename_dims({'y': 'y' + ds_obs.grid, 'x': 'x' + ds_obs.grid})
                else:
                    TMP = TMP.rename_dims({'yc': 'y' + ds_obs.grid, 'xc': 'x' + ds_obs.grid})
                TMP = TMP.rename({'lat': 'lat' + ds_obs.grid, 'lon': 'lon' + ds_obs.grid})
                INTERP_NAMES.append(var + ds_obs.grid)
                INTERP_DSS.append(TMP)
                del TMP
        for i, T in enumerate(INTERP_NAMES):
            print('Adding to Dataset', T)
            data = INTERP_DSS[i][var].values
            dims = INTERP_DSS[i][var].dims
            ds_model[T] = (dims, data)
            data_bin = np.copy(data); del data
            data_bin[data_bin > 0.15] = 1
            data_bin[data_bin <= 0.15] = 0
            data_bin[np.isnan(data_bin)] = 0
            ds_model[T + '_binary'] = (dims, data_bin.astype("int32"))
            del data_bin
        data = ds_model[var].values
        dims = ds_model[var].dims
        data_bin = np.copy(data); del data
        data_bin[data_bin > 0.15] = 1
        data_bin[data_bin <= 0.15] = 0
        data_bin[np.isnan(data_bin)] = 0
        ds_model[var + '_binary'] = (dims, data_bin.astype("int32"))
        encoding = { var: {"zlib": True, "complevel": 6} for var in ds_model.data_vars }
        ds_model.to_netcdf(file_save, format="NETCDF4", encoding=encoding)
        print('WROTE:', file_save)

def iiee(DAT, OBS, CLIMO = False, var = 'aice_d'):
    print('CALCULATING INTEGRATED ICE EDGE ERROR:') 
    ####################################
    # set up data arrays
    if CLIMO:
        ADD_CLIMO = True
    OBS_NAMES = []
    for i, ob in enumerate(OBS):
        ob = grid_name(ob)
        if ob.name not in OBS_NAMES:
            OBS_NAMES.append(ob.name)
            OBS_NAMES.append(ob.name + '_persistence')
            if ADD_CLIMO:
                OBS_NAMES.append(ob.name + '_climatology')
    dims_iiee = ('obs_type', 'pole') + DAT[var].dims[0:-2] 
    t = DAT['time'].values[0]
    DAT['forecast_hour'] = DAT['forecast_hour'].where(DAT['forecast_hour'] >= 0, 0)
    for i, ob in enumerate(OBS):
        ob = grid_name(ob)
        print(' Verifying Data:',ob.name, ob.grid_name)
        p = 0 if 'NH' in ob.grid_name else 1
        k = OBS_NAMES.index(ob.name)
        v = var + ob.grid_name + '_binary'
        area = float(ob.grid_name[2::])**2.
        model_dims = DAT[v].dims
        dim_sum = model_dims[-2::]
        ####################################
        # observations
        t_first = t + np.timedelta64(int(DAT['forecast_hour'][0].values), 'h')
        t_last = t + np.timedelta64(int(DAT['forecast_hour'][-1].values), 'h')
        ob = ob.sel(time = slice(t_first, t_last))
        ob['ice_con'] = ob['ice_con'].where(ob['ice_con'] < 2, 0)
        ob['ice_con'] = ob['ice_con'].where(ob['ice_con'] < 0.15, 1, 0)
        ob = ob.rename({'time' : 'forecast_hour'})
        ob['forecast_hour'] = (ob['forecast_hour'].values - np.datetime64(t)) / np.timedelta64(1,'h')
        ob = ob.rename_dims({'y': 'y' + ob.grid_name, 'x': 'x' + ob.grid_name }) #, 'time' : 'forecast_time'})
        ob = ob.expand_dims(time = [t])
        common = np.intersect1d(DAT['forecast_hour'].values, ob['forecast_hour'].values)
        data = ob['ice_con'].sel(forecast_hour = common)
        # model values
        DAT = DAT.sel(forecast_hour = common)
        model = DAT[v] 
        # Set up the data set if needed
        if i == 0:
            coords = {  "obs_type"      : OBS_NAMES,
                        "pole"          : ['north', 'south'],
                        "time"          : [t],
                        "forecast_hour" : common}
            M_NUMS = np.empty((len(OBS_NAMES), 2, 1, len(common)))
            M_NUMS = xr.DataArray(M_NUMS, coords = coords, dims = dims_iiee)
            DAT['iiee'] = M_NUMS
            DAT['aee'] = M_NUMS
        #########################################
        # forecast versus obs
        _, data = xr.broadcast(model, data)
        DAT['temp_diff'] = (model_dims, model.values - data.values) 
        if 'NH' in ob.grid:
            DAT['diff_NH'] = DAT['temp_diff']
        elif 'SH' in ob.grid:
            DAT['diff_SH'] = DAT['temp_diff'] 
        DAT['iiee'][k,p,:] = (np.multiply(abs(DAT['temp_diff']), area)).sum(dim = dim_sum).values / 1e6
        DAT['aee'][k,p,:]  = abs(np.multiply(DAT['temp_diff'], area).sum(dim = dim_sum).values / 1e6)
        #print('forecast vs data', DAT['iiee'][k,p,:].sel(time = t).values)
        DAT.drop('temp_diff')
        #########################################
        # persistence (first time of model) versus observations
        k = OBS_NAMES.index(ob.name + '_persistence')
        model = data.isel(forecast_hour = 0 ) 
        _, model = xr.broadcast(data, model)
        DAT['temp_diff'] = (model_dims, model.values - data.values) 
        DAT['iiee'][k,p,:] = (np.multiply(abs(DAT['temp_diff']), area)).sum(dim = dim_sum).values / 1e6
        DAT['aee'][k,p,:]  = abs(np.multiply(DAT['temp_diff'], area).sum(dim = dim_sum).values / 1e6)
        #print('forecast vs persistence', DAT['iiee'][k,p,:].sel(time = t).values)
        DAT.drop('temp_diff')
        # climatology values versus observations
        if ADD_CLIMO:
            k = OBS_NAMES.index(ob.name + '_climatology')
            data = ob['ice_con'].sel(forecast_hour = common)
            clim = CLIMO[p]
            doy = pd.to_datetime(ob['forecast_hour'].sel(forecast_hour = common).values).day_of_year
            clim = clim.sel(dayofyear = doy.values)
            clim = clim.rename_dims({'y': 'y' + ob.grid, 'x': 'x' + ob.grid, 'dayofyear' : 'forecast_hour'})
            model = clim['ice_con'] #.sel(dayofyear = doy.values)
            model = model.drop_vars('dayofyear')
            model = model.where(model < 2, 0)
            model = model.where(model < 0.15, 1, 0)
            model = model.expand_dims(time = [t])
            DAT['temp_diff'] = (model.dims, model.values - data.values)
            iiee = np.array((np.multiply(abs(DAT['temp_diff']), area)).sum(dim = dim_sum).values / 1e6)
            aee = abs(np.multiply(DAT['temp_diff'], area).sum(dim = dim_sum).values / 1e6)
            if 'member' in DAT.dims:
                for mem in DAT['member'].values:
                    DAT['iiee'][k,p,mem,:,0] = iiee
                    DAT['aee'][k,p,mem,:,0]  = aee
            else:
                DAT['iiee'][k,p,:]= iiee
                DAT['aee'][k,p,:]= iiee 
        #exit(1)
    DAT['me'] = (DAT['iiee'].dims, DAT['iiee'].values - DAT['aee'].values)
    SAVE_DAT = DAT.copy()
    SAVE_DAT.drop('TLAT')
    SAVE_DAT.drop('TLON')
    for key in SAVE_DAT.keys():
        if key not in ['member', 'forecast_time', 'time', 'pole', 'tau', 'obs_type', 'iiee', 'aee', 'me', 'diff_NH', 'diff_SH']:
            SAVE_DAT = SAVE_DAT.drop(key)
    return SAVE_DAT
