import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import xesmf as xe
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../PYTHON_TOOLS')
import PYTHON_TOOLS as npb

def extent(DAT, area, var = 'aice_d', force_calc = False):
    # grab data if already calculated
    try:
        f = DAT.extent_file
    except:
        f = None
    if os.path.exists(f):
       dd = xr.open_dataset(f)
       DAT['extent'] = (dd['extent'].dims, dd['extent'].values)
    # assume data are from CICE model
    dims = ('nj', 'ni')
    DIV = 1e12
    # see if data are already there
    if 'extent' not in list(DAT.keys()) or force_calc:
        print('CALCULATING ICE EXTENT:')
        # too much memory for below, must loop
        #NH = d['area'].where(d['ICEC_surface'] > 0.15).sum(dim=('latitude', 'longitude'))
        NH, SH = [], []
        ds = DAT.isel(time = 0)  
        _, area = xr.broadcast(ds[var], area['tarea'])
        DAT['tau_area'] = (area.dims, area.values) 
        print('     looping through time')
        if 'member' in DAT.dims:
            dims_save = ['hemisphere', 'time', 'member', 'tau']
        else:
            dims_save = ['hemisphere', 'time', 'tau']
        for t in DAT['time']:
            print('     ', t.values)
            # NH
            ds = DAT.sel(time = t.values)
            ds = ds.where(ds.TLAT > 20)
            NH.append(DAT['tau_area'].where(ds[var] >= 0.15).sum(dim = dims) / DIV)
            # SH
            ds = DAT.sel(time = t.values)
            ds = ds.where(ds.TLAT < -20)
            SH.append(ds['tau_area'].where(ds[var] >= 0.15).sum(dim = dims) / DIV)
        shape = (2,) + np.array(NH).shape 
        data = np.zeros((shape))
        data[0,:] = np.array(NH)
        data[1,:] = np.array(SH)
        print(data.shape)
        print(dims_save)
        DAT = DAT.assign(extent=(dims_save, data))
        DAT = DAT.assign(hemisphere=('hemisphere', ['north', 'south']))
        if f:
            SAVE_DAT = DAT.copy()
            for key in SAVE_DAT.keys():
                if key not in ['extent', 'time', 'hemisphere', 'member', 'tau']:
                    SAVE_DAT = SAVE_DAT.drop(key)
            print(SAVE_DAT)
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
        DAT.to_netcdf(file_save)
        print('WROTE:', file_save)

def iiee(DAT, DAT_area, OBS, var = 'aice_d', persistence = True):
    # interpolate model data onto observation grids
    print('CALCULATING INTEGRATED ICE EDGE ERROR:') 
    OBS_NAMES, var_names = [], []
    for i, ob in enumerate(OBS):
        ob = grid_name(ob)
        var_name = var + ob.grid_name + '_binary'
        if var_name not in var_names:
            var_names.append(var_name)
        if ob.name not in OBS_NAMES:
            OBS_NAMES.append(ob.name)
            if ob.name != 'climatology':
                OBS_NAMES.append(ob.name + '_persistence')
    if persistence:
        OBS_NAMES.append('persistence')
        ob = DAT.copy()
        ob = ob.assign_attrs({'name' : 'persistence'}) 
        ob = ob.assign_attrs({'grid_name' : 'CICE'}) 
        _, DAT_area = xr.broadcast(DAT[var], DAT_area)
        OBS.append(ob)
    if 'climatology' in OBS_NAMES:
        doy = pd.to_datetime(DAT['time'].values).day_of_year
        DAT['dayofyear'] = ('time', doy)
    dims_iiee = ('obs_type', 'pole') + DAT[var].dims[0:-2] 
    dims_shape = ()
    coords_iiee = {}
    t = DAT['time'].values[0]
    print(t)
    for dd in dims_iiee:
        if dd == 'time':
            coords_iiee[dd] = [t]
        elif dd == 'obs_type':
            coords_iiee[dd] = OBS_NAMES
        elif dd == 'pole':
            coords_iiee[dd] = ['north', 'south']
        else:
            coords_iiee[dd] = DAT[dd].values
        dims_shape = dims_shape + (len(coords_iiee[dd]),)
    M_NUMS = np.empty(dims_shape) 
    M_NUMS = xr.DataArray(M_NUMS, coords = coords_iiee, dims = dims_iiee)
    DAT['iiee'] = M_NUMS
    DAT['aee'] = M_NUMS
    for i, ob in enumerate(OBS):
        ob = grid_name(ob)
        print(' Verifying Data:',ob.name, ob.grid_name)
        p = 0 if 'NH' in ob.grid_name else 1
        k = OBS_NAMES.index(ob.name)
        if ob.name == 'persistence':
            v = var + '_binary'
            area = DAT_area['tarea']
        else:
            v = var + ob.grid_name + '_binary'
            area = float(ob.grid_name[2::])**2.
        model_dims = DAT[v].dims
        dim_sum = model_dims[-2::]
        # model values
        model = DAT[v]
        # observations
        if ob.name == 'persistence':
            data = ob[v].sel(tau = 0)
        elif ob.name == 'climatology':
            # make a fake tau and add data for each doy
            tau_size = int(DAT['tau'].size)
            ob = ob.rename_dims({'y': 'y' + ob.grid_name, 'x': 'x' + ob.grid_name})
            dat_dims = ('tau',) + ob['ice_con'].dims[1::]
            dim_shape = (tau_size,) + ob['ice_con'].shape[1::]
            ob['clim'] = (dat_dims, np.empty(dim_shape))
            M_NUMS = np.empty(dims_shape) 
            for j, d in enumerate(DAT['tau'].values):
                dd = doy[0] + (d / 24)
                if dd > 365:
                    dd = dd - 365 
                ob['clim'][j,:,:] = ob['ice_con'].sel(dayofyear = dd)
            data = ob['clim']
        else:    
            t_last = t + np.timedelta64(int(DAT['tau'][-1].values/24), 'D')
            ob = ob.rename_dims({'y': 'y' + ob.grid_name, 'x': 'x' + ob.grid_name, 'time' : 'tau'})
            data = ob['ice_con'].sel(time = slice(t, t_last))
            data['tau'] = DAT['tau'].values
            data = data.drop_vars('time')
        if ob.name != 'persistence':
            data = data.where(data < 2, 0)
            data = data.where(data < 0.15, 1, 0)
        _, data = xr.broadcast(model, data)
        # take diff for IIEE calculations 
        DAT['diff'] = (model_dims, model.values - data.values) 
        if ob.name == 'persistence':
            DAT['iiee'][k,0,:] = (np.multiply(abs(DAT['diff']), area)).where(DAT['TLAT'] > 50).sum(dim = dim_sum).values / 1e12
            DAT['aee'][k,0,:]  = abs(np.multiply(DAT['diff'], area).where(DAT['TLAT'] > 50).sum(dim = dim_sum).values / 1e12)
            DAT['iiee'][k,1,:] = (np.multiply(abs(DAT['diff']), area)).where(DAT['TLAT'] < 50).sum(dim = dim_sum).values / 1e12
            DAT['aee'][k,1,:]  = abs(np.multiply(DAT['diff'], area).where(DAT['TLAT'] < 50).sum(dim = dim_sum).values / 1e12)
        else:
            DAT['iiee'][k,p,:] = (np.multiply(abs(DAT['diff']), area)).sum(dim = dim_sum).values / 1e6
            DAT['aee'][k,p,:]  = abs(np.multiply(DAT['diff'], area).sum(dim = dim_sum).values / 1e6)
        DAT.drop('diff')
        if ob.name not in ['climatology', 'persistence']:
            data = ob['ice_con'].sel(time = t)
            data = data.where(data < 2, 0)
            data = data.where(data < 0.15, 1, 0)
            _, data = xr.broadcast(model, data)
            k = OBS_NAMES.index(ob.name + '_persistence')
            DAT['diff'] = (model_dims, model.values - data.values) 
            DAT['iiee'][k,p,:] = (np.multiply(abs(DAT['diff']), area)).sum(dim = dim_sum).values / 1e6
            DAT['aee'][k,p,:]  = abs(np.multiply(DAT['diff'], area).sum(dim = dim_sum).values / 1e6)
        DAT.drop('diff')
    if persistence:
        # OBS list is acting as a global variable, I don't quit understand why, so just remove
        OBS = OBS.pop()
    DAT['me'] = (DAT['iiee'].dims, DAT['iiee'].values - DAT['aee'].values)
    SAVE_DAT = DAT.copy()
    SAVE_DAT.drop('TLAT')
    SAVE_DAT.drop('TLON')
    for key in SAVE_DAT.keys():
        if key not in ['member', 'tau', 'time', 'pole', 'obs_type', 'iiee', 'aee', 'me']:
            SAVE_DAT = SAVE_DAT.drop(key)
    return SAVE_DAT
