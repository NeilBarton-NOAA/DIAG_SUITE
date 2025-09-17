from datetime import datetime
import glob
import pandas as pd
import pyproj
import numpy as np
import xarray as xr
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../PYTHON_TOOLS')
import PYTHON_TOOLS as npb

def add_forecast_hour(OBS, last_forecast_hour):
    t_last = OBS['time'][0] + np.timedelta64(int(last_forecast_hour), 'h')
    times = OBS['time'].sel(time = slice(OBS['time'][0], t_last))
    tau = (times - times[0]) / np.timedelta64(1,'h')
    end_date = OBS['time'][-1].values - pd.Timedelta(hours = int(last_forecast_hour))
    init_times = OBS['time'].sel(time=slice(None, end_date))
    forecast_hours = xr.DataArray(data=tau.values, dims=['forecast_hour'], name='forecast_hour')
    forecast_deltas = forecast_hours.astype('timedelta64[h]')
    target_datetimes = xr.DataArray(init_times, dims=['time']) + forecast_deltas
    OBS = OBS.sel(time=target_datetimes) 
    OBS['valid_times'] = OBS['time']
    OBS = OBS.drop_vars('time')
    OBS['forecast_hour'] = tau.values
    OBS['time'] = OBS['valid_times'].values[:,0]
    return OBS 

def add_land_mask(ds, var):
    v = ds[var]
    if len(v.shape) == 3:
        v = v[0]
    land_mask = xr.where(v >= 2., 0, 1)
    ds['land_mask'] = (land_mask.dims, land_mask.values)    
    return ds

################################################
################################################
# Sea Ice Concentrations
class sic(object):
    pole = 'NH'
    top_dir = './'
    ob_name = None
    climatology_years = 10
    dtg = '*'
    @classmethod
    def grab(cls):
        if cls.ob_name == None:
            print('FATAL: iceobs.sic.grab(), cls.ob_name most be defined')
            exit(1)
        elif cls.ob_name == 'osi_saf':
            obs_dir = cls.top_dir + '/ice_concentration/osi_saf/'
            if isinstance(cls.dtg, str):
                file_search = obs_dir + '*' + cls.pole.lower() + '*' + cls.dtg + '*.nc'
                f = glob.glob(file_search)
            else:
                f = []
                for d in cls.dtg: 
                    fs = glob.glob(obs_dir + '*' + cls.pole.lower() + '*' + d + '*.nc')
                    f.append(fs[0])
            if len(f) == 0:
                print('FATAL: iceobs.sic.grab(), No files found:', file_search)
                exit(1)
            ds = xr.open_mfdataset(f)
            ds['time'] = ds['time'] - np.timedelta64(12, 'h')
            grid_area = int(abs(ds['xc'][1] - ds['xc'][0]))
            ds['ice_con'] = (ds['ice_conc'].dims, ds['ice_conc'].values / 100.0)
            land_mask = ds['ice_con'][0]
            land_mask = land_mask.where(land_mask.isnull(), 1, drop=False)
            land_mask = land_mask.fillna(0)
            ds['land_mask'] = (land_mask.dims, land_mask.values)    
            ds['ice_con'] = ds['ice_con'].where(land_mask == 1, drop = False)
            ds = ds.assign_attrs({'grid' : cls.pole + str(grid_area)})
            ds = ds.assign_attrs({'pole': cls.pole})
            ds = ds.assign_attrs({'name': cls.ob_name})
            ds = ds.assign_attrs({'file_name': f })
        elif (cls.ob_name == 'amsr2'):
            file_search = cls.top_dir + '/ice_concentration/amsr2/*' + cls.dtg + '*.he5'
            group = '/HDFEOS/GRIDS/' + cls.pole[0] + 'pPolarGrid25km/Data Fields'
            v = 'SI_25km_' + cls.pole + '_ICECON_DAY'
            f = glob.glob(file_search)
            if len(f) == 0:
                print('FATAL: iceobs.sic.grab(), No files found:', file_search)
                exit(1)
            if len(f) == 1:
                print(' ', f[0])
                ds = xr.open_dataset(f[0], engine = 'h5netcdf', group = group)
            grid = xr.open_dataset(f[0], engine = 'h5netcdf', group = group.split('Data')[0])
            ds['lat'] = (grid['lat'].dims, grid['lat'].values)
            ds['lon'] = (grid['lon'].dims, grid['lon'].values)
            import matplotlib.pyplot as plt
            ds['land_mask'] = xr.where(ds[v] > 100, 0, 1)
            ds['ice_con'] = ds[v] / 100.0
            ds['ice_con'] = ds['ice_con'].where(ds['land_mask'] == 1, drop = False)
            for key in list(ds.keys()):
                if key not in ['ice_con', 'land_mask', 'lat', 'lon']:
                    ds = ds.drop(key)
            dtg = str(cls.dtg)
            t = np.datetime64(dtg[0:4] + '-' + dtg[4:6] + '-' + dtg[6:8], 'ns')
            ds = ds.expand_dims({"time": [t]})
            ds = ds.assign_attrs({'grid' : '25km'})
            ds = ds.assign_attrs({'pole': cls.pole})
            ds = ds.assign_attrs({'name': cls.ob_name})
            ds = ds.assign_attrs({'file_name': f[0] })
        elif (cls.ob_name == 'climatology'):
            save_file = cls.top_dir + '/ice_concentration/noaa_cdr_climo_years_' \
                        + str(cls.climatology_years) + '_parsed_' + cls.pole + '.nc'
            print(' ',save_file)
            if os.path.exists(save_file):
                ds = xr.open_dataset(save_file)
            else:
                ds = calc_icecon_daily_climatology(save_file, cls.pole)
        else:
            print('FATAL: iceobs.sic.grab(), Ob Name unknown', cls.ob_name)
            exit(1)
        for key in list(ds.keys()):
            if key not in ['ice_con', 'lat', 'lon', 'land_mask', 'time', 'dayofyear']:
                ds = ds.drop(key)
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
    ds = add_land_mask(ds, 'cdr_seaice_conc')
    return ds


def to_netcdf(ds, filename):
    default_compression = {"zlib": True, "complevel": 6}
    compress_encoding = {var_name: default_compression for var_name in ds.data_vars}
    ds.to_netcdf(filename, encoding=compress_encoding)
    print('SAVED:', filename)

def calc_icecon_daily_climatology(save_file, pole, years = 10):
    print('CALCULATING DAILY CLIMATOLOGY SEA ICE CONCENTRATIONS:', pole)
    ice_dir = os.path.dirname(save_file) + '/noaa_cdr'
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
    #grid_area = int(ds.geospatial_x_resolution.split()[0][0:2])
    ds = ds.assign_attrs({'Start Year for Climo': str(t_first)})
    ds = ds.assign_attrs({'End Year for Climo': str(t_last)})
    ds = ds.assign_attrs({'Years for Climo': years})
    ds = ds.assign_attrs({'Datasets for Climo': variables})
    ds = ds.assign_attrs({'name': 'climatology'})
    ds = ds.assign_attrs({'pole': pole})
    ds = ds.assign_attrs({'grid' : pole + str(grid_area)})
    ds = ds.assign_attrs({'name': 'climatology'})
    for key in list(ds.keys()):
        if key not in ['ice_con', 'lat', 'lon', 'land_mask', 'time', 'dayofyear']:
            ds = ds.drop(key)
    to_netcdf(ds, save_file)
    return ds

################################################
################################################
# Sea Ice Extents
def get_extentobs_CDR(obs_dir, var = 'cdr_seaice_conc'):
    ice_dir = obs_dir + '/ice_extent/noaa_cdr'
    if not os.path.exists(ice_dir):
        os.makedirs(ice_dir)
    poles = ['north', 'south']
    save_file = ice_dir + '/noaa_cdr_' + var + '_extent.nc'
    if os.path.exists(save_file):
        print(save_file)
        ds = xr.open_dataset(save_file)
    else:
        print('calculating extent')
        obs = npb.iceobs.get_icecon_cdr(obs_dir, var)
        ds = xr.Dataset(coords={"time": [], 'pole': ['north', 'south']})
        ds['time'] = obs[0]['time'].values
        ds['extent'] = (('time', 'pole'), np.empty((ds['time'].size,2)))
        for ob in obs:
            grid_area = int(ob.spatial_resolution.strip('km'))**2.
            p = 0 if ob.pole == 'NH' else 1
            t = ob['time'].values[0]
            ob['ice_con'] = ob['ice_con'].where(ob['ice_con'] < 2, 0)
            ob['ice_con'] = ob['ice_con'].where(ob['ice_con'] < 0.15, 1, 0)
            ds['extent'][:,p] = ob['ice_con'].sum(dim = ['x','y']) * grid_area / 1e6
        ds = ds.assign_attrs({'test_name': var})
        ds.to_netcdf(save_file)
        print("write:", save_file)
    return ds

def get_extentobs_NASA(obs_dir):
    ice_dir = obs_dir + '/ice_extent/nasateam'
    files = ['gsfc.nasateam.daily.extent.1978-2022.n', 'gsfc.nasateam.daily.extent.1978-2022.s']
    for ii, f in enumerate(files):
        print(ice_dir + '/' + f)
        #ob = pd.read_csv(ice_dir + '/' + f, delim_whitespace = True)
        ob = pd.read_csv(ice_dir + '/' + f, sep='\s+')
        t, hem = [], []
        if f[-1] == 'n':
            v_key = 'TotalArc'
        elif f[1] == 's':
            v_key = 'TotalAnt'
        for i in range(ob.shape[0]):
            y = str(ob[ob.keys()[0]][i])
            m = str(ob[ob.keys()[1]][i]).zfill(2)
            d = str(ob[ob.keys()[2]][i]).zfill(2)
            t.append(np.datetime64(y + '-' + m + '-' + d, 'ns'))
            if v_key == 'TotalArc':
                hem.append('north')
            elif v_key == 'TotalAnt':
                hem.append('south')
        ob['time'] = t
        ob['pole'] = hem
        for k in ob.keys():
            if k.strip() not in ['time', 'pole', v_key]:
                ob.drop(k, axis = 1, inplace = True)
            else:
                ob.rename(columns = {k: k.strip()}, inplace = True)
        ob[v_key] = ob[v_key] / 10e5
        ob.rename(columns = {v_key: 'extent'}, inplace = True)
        ob.set_index(['time', 'pole'], inplace = True)
        if ii == 0:
            obs = ob
        else:
            obs = pd.concat([obs,ob])
    obs = obs.to_xarray()
    obs = obs.assign_attrs({'test_name': 'OBS-NASA'})
    return obs

def get_extentobs_bootstrap(obs_dir):
    ice_dir = obs_dir + '/ice_extent/bootstrap'
    files = ['gsfc.bootstrap.daily.extent.1978-2022.n', 'gsfc.bootstrap.daily.extent.1978-2022.s']
    for ii, f in enumerate(files):
        print(ice_dir + '/' + f)
        #ob = pd.read_csv(ice_dir + '/' + f, delim_whitespace = True)
        ob = pd.read_csv(ice_dir + '/' + f, sep='\s+')
        if f[-1] == 'n':
            v_key = 'TotalArc'
        elif f[1] == 's':
            v_key = 'TotalAnt'
        t, hem = [], []
        for i in range(ob.shape[0]):
            y = str(ob[ob.keys()[0]][i])
            m = str(ob[ob.keys()[1]][i]).zfill(2)
            d = str(ob[ob.keys()[2]][i]).zfill(2)
            t.append(np.datetime64(y + '-' + m + '-' + d, 'ns'))
            if v_key == 'TotalArc':
                hem.append('north')
            elif v_key == 'TotalAnt':
                hem.append('south')
        ob['time'] = t
        ob['pole'] = hem
        for k in ob.keys():
            if k.strip() not in ['time', 'pole', v_key]:
                ob.drop(k, axis = 1, inplace = True)
            else:
                ob.rename(columns = {k: k.strip()}, inplace = True)
        ob[v_key] = ob[v_key] / 10e5
        ob.rename(columns = {v_key: 'extent'}, inplace = True)
        ob.set_index(['time', 'pole'], inplace = True)
        if ii == 0:
            obs = ob
        else:
            obs = pd.concat([obs, ob])
    obs = obs.to_xarray()
    obs = obs.assign_attrs({'test_name': 'OBS-bootstrap'})
    return obs

################################################
################################################
# Sea Ice Thickness
def get_thickness(obs_dir):
    ice_dir = obs_dir + '/ICE_THICKNESS'
    obs = xr.open_mfdataset(ice_dir + '/ice*.nc')
    return obs


