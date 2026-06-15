import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import os
import sys

class extent(object):
    grid_size = None
    @classmethod
    def calc(cls):
        dat = cls.ds[cls.var]
        dims = cls.ds[cls.var].dims[-2::] if len(cls.ds[cls.var].dims) > 2 else cls.ds[cls.var].dims
        lat = 'lat' if 'lat' in dat.coords else 'TLAT'
        if 'nj' in cls.ds[cls.var].dims:
            DIV = 1e12
            area = cls.ds['tarea']
            dat = cls.ds[cls.var]
            pole_data = []
            for p in ['NH', 'SH']:
                if p == 'NH':
                    EXT = area.where((dat[lat] > 10) & (dat >= 0.15)).sum(dim = dims) / DIV    
                elif p == 'SH':
                    EXT = area.where((dat[lat] < -10) & (dat >= 0.15)).sum(dim = dims) / DIV
                EXT = EXT.expand_dims({"pole" : [p]})
                EXT.name = 'extent'
                pole_data.append(EXT)
            ds = xr.concat(pole_data, dim = 'pole')
        else: 
            if cls.grid_size:
                grid_size = cls.grid_size
            else:
                if cls.var == 'ice_con':
                    grid_size = float(cls.ds.grid.replace('km','').replace('NH','').replace('SH',''))**2.0
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
            area = float(cls.grid.replace('km','').replace('NH','').replace('SH',''))**2.0
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
        if 'valid_times' in list(ds_obs):
            ds_model['iiee'] = ds_model['iiee'].where(ds_obs['valid_times'].notnull())
            ds_model['aee'] = ds_model['aee'].where(ds_obs['valid_times'].notnull())
            ds_model['me'] = ds_model['me'].where(ds_obs['valid_times'].notnull())
        if 'valid_times' in list(ds_model):
            ds_model['iiee'] = ds_model['iiee'].where(ds_model['valid_times'].notnull())
            ds_model['aee'] = ds_model['aee'].where(ds_model['valid_times'].notnull())
            ds_model['me'] = ds_model['me'].where(ds_model['valid_times'].notnull())
        # Skim data set
        dim_all = dim_all + tuple(['lat' + cls.grid, 'lon' + cls.grid, 'diff' + cls.grid, 'iiee', 'aee', 'me'])
        for v in ds_model.variables:
            if v not in list(dim_all):
                ds_model = ds_model.drop(v)
        return ds_model
