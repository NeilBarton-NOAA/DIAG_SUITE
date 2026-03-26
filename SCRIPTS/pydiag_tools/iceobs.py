import glob, os, sys
import numpy as np
import xarray as xr
import pandas as pd
from datetime import datetime
from . import icecalc, utils

# global variables
dtgs = '*'
directory = None

################################################
# grab sea ice concentrations
class sic(object):
    pole = 'NH'
    climatology_years = 10
    @classmethod
    def grab(cls):
        global directory, dtgs
        obs_dir = directory
        ob_name = os.path.basename(obs_dir)
        if ob_name == 'climatology':
            save_file = obs_dir + '/' + 'noaa_cdr_climo_years_' \
                    + str(cls.climatology_years) + '_parsed_' + cls.pole + '.nc'
            ds = xr.open_dataset(save_file) if os.path.exists(save_file) else calc_icecon_daily_climatology(save_file, cls.pole)
            grid = 25
        elif ob_name == 'amsr2':
            ds = amsr2(directory, cls.pole, dtgs)
            grid = 25
        elif ob_name == 'osi_saf':
            ds = osi_saf(directory, cls.pole, dtgs)
            grid = 10
        else:
            print('FATAL iceobs.py, ob_name unknown', ob_name)
            exit(1)
        ############
        vars_keep = set(['ice_con', 'land_mask', 'lat', 'lon', 'time', 'dayofyear'])
        vars_to_drop = [key for key in ds.data_vars if key not in vars_keep]
        ds = ds.drop_vars(vars_to_drop)
        ds = ds.assign_attrs({'name': ob_name})
        ds = ds.assign_attrs({'pole': cls.pole})
        ds = ds.assign_attrs({'grid' : cls.pole + str(grid)})
        ds = ds.assign_attrs({'grid_area' : grid**2.})
        return ds

########################
# calculate extent from sea ice concentrations
class extent(object):
    var = 'ice_con'
    @classmethod
    def grab(cls):
        global directory, dtgs
        file = directory + '/ice_extent_' + dtgs[0] + '_to_' + dtgs[-1] + '.nc'
        if os.path.exists(file):
            print('opening', file)
            ds = xr.open_dataset(file)
        else:
            icecalc.extent.var = cls.var
            P_DS = []
            for p in ['NH', 'SH']:
                sic.pole = p
                icecalc.extent.ds = sic.grab()
                ds = icecalc.extent.calc()
                P_DS.append(ds.expand_dims({'pole': [p]}))
            ds = xr.concat(P_DS, dim = 'pole').to_dataset()
            utils.ds_to_netcdf(ds, file) 
        return ds

def osi_saf(directory, pole, dtgs):
    if isinstance(dtgs, str):
        file_search = directory + '/*' + pole.lower() + '*' + dtgs + '*.nc'
        f = glob.glob(file_search)
    else:
        f = []
        for d in dtgs: 
            fs = glob.glob(directory + '/*' + pole.lower() + '*' + d + '*.nc')
            f.append(fs[0])
    if len(f) == 0:
        print('FATAL: iceobs.sic.grab(), No files found:', file_search)
        exit(1)
    ds = xr.open_mfdataset(f, data_vars='all')
    ds['time'] = ds['time'] - np.timedelta64(12, 'h')
    grid_area = int(abs(ds['xc'][1] - ds['xc'][0]))
    ds['ice_con'] = (ds['ice_conc'].dims, ds['ice_conc'].values / 100.0)
    land_mask = ds['ice_con'][0]
    land_mask = land_mask.where(land_mask.isnull(), 1, drop=False)
    land_mask = land_mask.fillna(0)
    ds['land_mask'] = (land_mask.dims, land_mask.values)    
    ds['ice_con'] = ds['ice_con'].where(land_mask == 1, drop = False)
    ds = ds.assign_attrs({'grid' : pole + str(grid_area)})
    ds = ds.assign_attrs({'pole': pole})
    ds = ds.assign_attrs({'name': 'osi_saf'})
    ds = ds.assign_attrs({'file_name': f }) 
    return ds

def amsr2(directory, pole, dtgs):
    group = '/HDFEOS/GRIDS/' + pole[0] + 'pPolarGrid25km/Data Fields'
    v = 'SI_25km_' + pole + '_ICECON_DAY'
    if isinstance(dtgs, str):
        file_search = directory + '/*' + dtgs + '*.he5'
        f = glob.glob(file_search)[0]
        ds = xr.open_mfdataset(f, engine = 'h5netcdf', group = group)
        t = np.datetime64(dtgs[0:4] + '-' + dtgs[4:6] + '-' + dtgs[6:8], 'ns')
        ds = ds.expand_dims({"time": [t]})
    else:
        DATS = []
        for dtg in dtgs: 
            file_search = directory + '/*' + dtg + '*.he5'
            f = glob.glob(file_search)[0]
            ds = xr.open_mfdataset(f, engine = 'h5netcdf', group = group)
            t = np.datetime64(dtg[0:4] + '-' + dtg[4:6] + '-' + dtg[6:8], 'ns')
            ds = ds.expand_dims({"time": [t]})
            DATS.append(ds)
        ds = xr.concat(DATS, dim = 'time')
    grid = xr.open_dataset(f, engine = 'h5netcdf', group = group.split('Data')[0])
    ds['lat'] = (grid['lat'].dims, grid['lat'].values)
    ds['lon'] = (grid['lon'].dims, grid['lon'].values)
    ds = ds.rename({'YDim': 'y', 'XDim': 'x'})
    ds['land_mask'] = xr.where(ds[v] > 100, 0, 1).squeeze()
    ds['ice_con'] = ds[v] / 100.0
    ds['ice_con'] = ds['ice_con'].where(ds['land_mask'] == 1, drop = False)
    return ds

def open_noaacdr_mf(files):
    def drop_vars(ds):
        ds = ds.drop('latitude')
        ds = ds.drop('longitude')
        return ds
    files.sort()
    ds = xr.open_mfdataset(files, preprocess = drop_vars, combine = 'nested', concat_dim = 'tdim')
    geo = xr.open_dataset(files[0]) 
    ds['lat'] = (geo['latitude'].dims, geo['latitude'].values)
    ds['lon'] = (geo['longitude'].dims, geo['longitude'].values)
    ds = ds.swap_dims({'tdim' : 'time'})
    v = ds['cdr_seaice_conc']
    if len(v.shape) == 3:
        v = v[0]
    land_mask = xr.where(v >= 2., 0, 1)
    ds['land_mask'] = (land_mask.dims, land_mask.values)    
    return ds

def calc_icecon_daily_climatology(save_file, pole, years = 10):
    print('CALCULATING DAILY CLIMATOLOGY SEA ICE CONCENTRATIONS:', pole)
    ice_dir = os.path.dirname(save_file) + '/../noaa_cdr'
    f_search = ice_dir + '/' + pole[0].lower() + '*/*daily_' + pole.lower() + '*.nc'
    ds = open_noaacdr_mf(glob.glob(f_search))
    # time for climatology
    t_last = ds['time'].values[-1]
    t_first = np.array(pd.to_datetime(t_last) - pd.DateOffset(years= years))
    obs = np.zeros((366, ds['y'].size, ds['x'].size))
    variables = ['nsidc_nt_seaice_conc', 'nsidc_bt_seaice_conc', 'cdr_seaice_conc']
    for var in variables:    
        dat = ds[var].sel(time = slice(t_first, t_last))
        obs = obs + dat.groupby("time.dayofyear").mean().values
    obs = obs / len(variables)
    ds['dayofyear'] = np.arange(366) + 1
    ds['ice_con'] = (('dayofyear','y','x'), obs)
    ds['ice_con'] = ds['ice_con'].where(ds['land_mask'] == 1, drop = False)
    grid_area = int(ds.spatial_resolution.strip('km'))
    ds = ds.assign_attrs({'Start Year for Climo': str(t_first)})
    ds = ds.assign_attrs({'End Year for Climo': str(t_last)})
    ds = ds.assign_attrs({'Years for Climo': years})
    ds = ds.assign_attrs({'Datasets for Climo': variables})
    ds = ds.assign_attrs({'name': 'climatology'})
    ds = ds.assign_attrs({'pole': pole})
    ds = ds.assign_attrs({'grid' : pole + str(grid_area)})
    ds = ds.assign_attrs({'grid_area' : grid_area**2.})
    ds = ds[['ice_con', 'lat', 'lon', 'land_mask', 'time', 'dayofyear']]
    to_netcdf(ds, save_file)
    return ds

