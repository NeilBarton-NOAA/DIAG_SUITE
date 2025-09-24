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
    grid_size = None
    @classmethod
    def calc(cls):
        dat = cls.ds[cls.var]
        dims = cls.ds[cls.var].dims[-2::] if len(cls.ds[cls.var].dims) > 2 else cls.ds[cls.var].dims
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
            if cls.grid_size:
                grid_size = cls.grid_size
            else:
                if cls.var == 'ice_con':
                    grid_size = float(cls.ds.grid[-2::])**2.0
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
 
#def interp(ds_model, ds_obss, var = 'aice_d', force_calc = True):
#    file_save = os.path.dirname(ds_model.file_name) + '/INTERP_' + os.path.basename(ds_model.file_name) 
#    if (os.path.exists(file_save) == False) or (force_calc == True):
#        ds_model = ds_model.rename({'TLAT': 'lat', 'TLON': 'lon'})
#        ds_model['mask'] = (ds_model['tmask'].dims, ds_model['tmask'].values)
#        ds_model[var] = ds_model[var].where(ds_model['mask'] == 1, drop = False)
#        ds_model = daily_taus(ds_model, var)
#        ################################################
#        # create regridder/interpolate data/ make new data array
#        dir_weights = os.path.dirname(ds_model.file_name) + '/interp_weights'
#        os.makedirs(dir_weights, exist_ok=True)
#        # remove data sets if they have the same grid as another
#        GRIDS, UNIQUE = set(), []
#        for ds_obs in ds_obss:
#            if ds_obs.grid not in GRIDS:
#                UNIQUE.append(ds_obs)
#                GRIDS.add(ds_obs.grid)
#        # interp to these grids
#        for ds_obs in UNIQUE:
#            ############
#            # determine grid name
#            interp_method, extrap_method = 'bilinear', 'nearest_s2d'
#            file_weights = dir_weights + '/regridding_weights_CICE025_to_' + \
#                           ds_obs.grid + 'km_' + interp_method + '_extrap_' + extrap_method+ '.nc'
#            ############
#            # interpolate if needed
#            print('interpolating to', ds_obs.grid)
#            ds_obs['mask'] = (ds_obs['land_mask'].dims, ds_obs['land_mask'].values)
#            rw = True if os.path.exists(file_weights) else False
#            regridder = xe.Regridder(ds_model, ds_obs, method = interp_method, \
#                                     extrap_method = extrap_method, \
#                                     reuse_weights=rw, filename=file_weights)
#            TMP = regridder(ds_model)
#            TMP = TMP.where(ds_obs['mask'].astype(bool))
#            if ds_obs.grid[2:4] == '25':
#                TMP = TMP.rename_dims({'y': 'y' + ds_obs.grid, 'x': 'x' + ds_obs.grid})
#            else:
#                TMP = TMP.rename_dims({'yc': 'y' + ds_obs.grid, 'xc': 'x' + ds_obs.grid})
#            new_var = var + ds_obs.grid
#            print('Adding to Dataset', new_var)
#            ds_model['lat' + ds_obs.grid ] = (TMP['mask'].dims, ds_obs['lat'].values)
#            ds_model['lon' + ds_obs.grid ] = (TMP['mask'].dims, ds_obs['lon'].values)
#            ds_model[new_var] = (TMP[var].dims, TMP[var].values)
#            ds_model[new_var + '_binary'] = xr.where(ds_model[new_var] > 0.15,1,0).astype("int32")
#            del TMP
#        # orign grid changes for binary data
#        ds_model[var + '_binary'] = xr.where(ds_model[var] > 0.15,1,0).astype("int32")
#        ds_model = ds_model.rename({'lat': 'TLAT', 'lon': 'TLON'})
#        # write file
#        encoding = { var: {"zlib": True, "complevel": 6} for var in ds_model.data_vars }
#        ds_model.to_netcdf(file_save, format="NETCDF4", encoding=encoding)
#        print('WROTE:', file_save)

class iiee(object):
    grid_size = None
    @classmethod
    def calc(cls):
        print('CALCULATING INTEGRATED ICE EDGE ERROR:', cls.grid) 
        # variables could have different time and forecast_hour lenghts
        ds_model, ds_obs = xr.align(cls.ds_model, cls.ds_obs, join = 'inner')
        # variable names
        var = 'aice' + cls.grid
        if var == 'aice':
            obs_var = 'aice'
            area = ds_obs['tarea']
            DIV = 1e12
        else:
            if 'yc' in ds_obs['ice_con'].dims:
                ds_obs = ds_obs.rename({'yc': 'y' + cls.grid, 'xc': 'x' + cls.grid})
            else:
                ds_obs = ds_obs.rename({'y': 'y' + cls.grid, 'x': 'x' + cls.grid})
            obs_var = 'ice_con'
            DIV = 1e6
            area = float(cls.grid[-2::])**2.0
        # set values to zero and one
        ds_model[var] = xr.where(ds_model[var] > 0.15, 1, 0).astype("int32")
        ds_obs[obs_var] = xr.where(ds_obs[obs_var] > 0.15, 1, 0).astype("int32")
        # dimensions
        dim_all = ds_model[var].dims
        dim_sum = dim_all[-2::]
        dim_save = dim_all[0:len(dim_all) - 2]
        # calculations
        ds_model['diff' + cls.grid] = ds_model[var] - ds_obs[obs_var]
        iiee = (np.multiply(abs(ds_model['diff' + cls.grid]), area)).sum(dim = dim_sum).values / DIV
        aee  = abs(np.multiply(ds_model['diff' + cls.grid], area).sum(dim = dim_sum).values / DIV)
        ds_model['iiee'] = (dim_save, iiee)
        ds_model['aee'] = (dim_save, aee)
        ds_model['me'] = (dim_save, iiee - aee)
        # Skim data set
        dim_all = dim_all + tuple(['lat' + cls.grid, 'lon' + cls.grid, 'diff' + cls.grid, 'iiee', 'aee', 'me'])
        for v in ds_model.variables:
            if v not in list(dim_all):
                ds_model = ds_model.drop(v)
        return ds_model
