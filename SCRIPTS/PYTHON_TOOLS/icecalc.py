import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import xesmf as xe
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../PYTHON_TOOLS')
import PYTHON_TOOLS as npb

def extent(DAT, var = 'aice_d', force_calc = False):
    # grab data if already calculated
    try:
        f = DAT.extent_file
    except:
        f = None
    os.remove(f) if force_calc and os.path.exists(f) else None
    if os.path.exists(f):
       print("ice_extent.nc file exist", f)
       dd = xr.open_dataset(f)
       DAT['extent'] = (dd['extent'].dims, dd['extent'].values)
    # assume data are from CICE model
    dims = ('nj', 'ni')
    DIV = 1e12
    # see if data are already there
    if 'extent' not in list(DAT.keys()) or force_calc:
        print('CALCULATING ICE EXTENT:')
        NH, SH = [], []
        ds = DAT.isel(time = 0)
        print('     looping through time')
        if 'member' in DAT.dims:
            dims_save = ['pole', 'time', 'member', 'forecast_hour']
        else:
            dims_save = ['pole', 'time', 'forecast_hour']
        for t in DAT['time']:
            print('     ', t.values)
            # NH
            ds = DAT.sel(time = t.values)
            ds = ds.where(ds.TLAT > 10)
            dum = DAT['tarea'].where(ds[var] >= 0.15).sum(dim = dims) / DIV
            NH.append(DAT['tarea'].where(ds[var] >= 0.15).sum(dim = dims).values / DIV)
            # SH
            ds = DAT.sel(time = t.values)
            ds = ds.where(ds.TLAT < -20)
            SH.append(ds['tarea'].where(ds[var] >= 0.15).sum(dim = dims).values / DIV)
        shape = (2,) + np.array(NH).shape 
        data = np.zeros((shape))
        data[0,:] = np.array(NH)
        data[1,:] = np.array(SH)
        data = np.ma.masked_where(data == 0, data)
        DAT = DAT.assign(extent=(dims_save, data))
        DAT = DAT.assign(pole=('pole', ['north', 'south']))
        if f:
            SAVE_DAT = DAT.copy()
            for key in SAVE_DAT.keys():
                if key not in ['extent', 'time', 'time_start', 'forecast_time', 'pole', 'member', 'forecast_hour']:
                    SAVE_DAT = SAVE_DAT.drop(key)
            print('writing:', f)
            if os.path.exists(f):
                SAVE_DAT.to_netcdf(f, mode = 'a')
            else:
                SAVE_DAT.to_netcdf(f)
    return DAT
    
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

def CALC_IIEE(MODEL, OBS, AREA):
    MODEL[MODEL > 0.15] = 1
    MODEL[MODEL <= 0.15] = 0
    OBS[OBS > 1] = 0 # land mask
    OBS[OBS > 0.15] = 1
    OBS[OBS <= 0.15] = 0
    IIEE = np.nansum(np.multiply(MODEL - OBS), AREA) / 1000000
    AEE = np.abs(np.nansum(np.multiply((MODEL - OBS), AREA))) / 1000000
    ME = IIEE - AEE
    return IIEE, AEE, ME
            
def grid_name(ob):
    ############
    # determine grid name
    if 'grid_name' not in ob.attrs:
        if 'spatial_resolution' in ob.attrs: 
            grid_area = int(ob.spatial_resolution.strip('km'))
        elif 'geospatial_x_resolution' in ob.attrs:
            grid_area = int(ob.geospatial_x_resolution.split()[0][0:2])
        else:
            print('grid resolution unknown')
            for k in ob.attrs.keys():
                print(' ',k,'   ', ob.attrs[k])
                exit(1)
        grid_name = ob.pole + str(grid_area)
        ob = ob.assign_attrs({'grid_name' : grid_name})
    return ob

def interp(DAT, OBS, var = 'aice_d', force_calc = False):
    file_save = os.path.dirname(DAT.file_name) + '/interp_obs_grids_' + os.path.basename(DAT.file_name) 
    if (os.path.exists(file_save) == False) or (force_calc == True):
        DAT.rename({'TLAT': 'lat', 'TLON': 'lon'})
        DAT['lat'] = (DAT['TLAT'].dims, DAT['TLAT'].values)
        DAT['lon'] = (DAT['TLON'].dims, DAT['TLON'].values)
        DAT = daily_taus(DAT, var)
        if 'tarea' in DAT.variables:
            DAT = DAT.drop('tarea')
        ################################################
        # create regridder/interpolate data/ make new data array
        dir_weights = os.path.dirname(DAT.file_name) + '/interp_weights'
        if not os.path.exists(dir_weights):
            os.makedirs(dir_weights)
        TMP_NAMES, TMP_DS = [], []
        for ob in OBS:
            ############
            # determine grid name
            ob = grid_name(ob)
            ############
            # interpolate if needed
            if (var + ob.grid_name) not in TMP_NAMES:
                print('interpolating to', ob.grid_name)
                D = DAT.copy()
                file_weights = dir_weights + '/regridding_weights_CICE025_to_' + ob.grid_name + 'km.nc'
                print(file_weights)
                if os.path.exists(file_weights):
                    regridder = xe.Regridder(D, ob, 'nearest_s2d', reuse_weights=True, filename=file_weights)
                else:
                    regridder = xe.Regridder(D, ob, 'nearest_s2d', reuse_weights=False, filename=file_weights)
            TMP = regridder(D)
            TMP = TMP.rename_dims({'y': 'y' + ob.grid_name, 'x': 'x' + ob.grid_name})
            TMP = TMP.rename({'lat': 'lat' + ob.grid_name, 'lon': 'lon' + ob.grid_name})
            TMP_NAMES.append(var + ob.grid_name)
            TMP_DS.append(TMP)
            del TMP
        for i, T in enumerate(TMP_NAMES):
            print('Adding to Dataset', T)
            data = TMP_DS[i][var].values
            dims = TMP_DS[i][var].dims
            DAT[T] = (dims, data)
            data_bin = np.copy(data); del data
            data_bin[data_bin > 0.15] = 1
            data_bin[data_bin <= 0.15] = 0
            data_bin[np.isnan(data_bin)] = 0
            DAT[T + '_binary'] = (dims, data_bin.astype("int32"))
            del data_bin
        data = DAT[var].values
        dims = DAT[var].dims
        data_bin = np.copy(data); del data
        data_bin[data_bin > 0.15] = 1
        data_bin[data_bin <= 0.15] = 0
        data_bin[np.isnan(data_bin)] = 0
        DAT[var + '_binary'] = (dims, data_bin.astype("int32"))
        encoding = { var: {"zlib": True, "complevel": 4} for var in DAT.data_vars }
        DAT.to_netcdf(file_save, format="NETCDF4", encoding=encoding)
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
        #.sel(forecast_time = common).squeeze()
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
        DAT['diff'] = (model_dims, model.values - data.values) 
        DAT['iiee'][k,p,:] = (np.multiply(abs(DAT['diff']), area)).sum(dim = dim_sum).values / 1e6
        DAT['aee'][k,p,:]  = abs(np.multiply(DAT['diff'], area).sum(dim = dim_sum).values / 1e6)
        #print('forecast vs data', DAT['iiee'][k,p,:].sel(time = t).values)
        DAT.drop('diff')
        #########################################
        # persistence (first time of model) versus observations
        k = OBS_NAMES.index(ob.name + '_persistence')
        model = data.isel(forecast_hour = 0 ) 
        _, model = xr.broadcast(data, model)
        DAT['diff'] = (model_dims, model.values - data.values) 
        DAT['iiee'][k,p,:] = (np.multiply(abs(DAT['diff']), area)).sum(dim = dim_sum).values / 1e6
        DAT['aee'][k,p,:]  = abs(np.multiply(DAT['diff'], area).sum(dim = dim_sum).values / 1e6)
        #print('forecast vs persistence', DAT['iiee'][k,p,:].sel(time = t).values)
        DAT.drop('diff')
        # climatology values versus observations
        if ADD_CLIMO:
            k = OBS_NAMES.index(ob.name + '_climatology')
            data = ob['ice_con'].sel(forecast_hour = common)
            clim = CLIMO[p]
            doy = pd.to_datetime(ob['forecast_hour'].sel(forecast_hour = common).values).day_of_year
            clim = clim.sel(dayofyear = doy.values)
            clim = clim.rename_dims({'y': 'y' + ob.grid_name, 'x': 'x' + ob.grid_name, 'dayofyear' : 'forecast_hour'})
            model = clim['ice_con'] #.sel(dayofyear = doy.values)
            model = model.drop_vars('dayofyear')
            model = model.where(model < 2, 0)
            model = model.where(model < 0.15, 1, 0)
            model = model.expand_dims(time = [t])
            DAT['diff'] = (model.dims, model.values - data.values)
            iiee = np.array((np.multiply(abs(DAT['diff']), area)).sum(dim = dim_sum).values / 1e6)
            aee = abs(np.multiply(DAT['diff'], area).sum(dim = dim_sum).values / 1e6)
            if 'member' in DAT.dims:
                for mem in DAT['member'].values:
                    DAT['iiee'][k,p,mem,:,0] = iiee
                    DAT['aee'][k,p,mem,:,0]  = aee
            else:
                DAT['iiee'][k,p,:]= iiee
                DAT['aee'][k,p,:]= iiee 
            #print('forecast vs climatology', DAT['iiee'][k,p,:].sel(time = t).values)
        #exit(1)
    DAT['me'] = (DAT['iiee'].dims, DAT['iiee'].values - DAT['aee'].values)
    SAVE_DAT = DAT.copy()
    SAVE_DAT.drop('TLAT')
    SAVE_DAT.drop('TLON')
    for key in SAVE_DAT.keys():
        if key not in ['member', 'forecast_time', 'time', 'pole', 'tau', 'obs_type', 'iiee', 'aee', 'me']:
            SAVE_DAT = SAVE_DAT.drop(key)
    return SAVE_DAT
