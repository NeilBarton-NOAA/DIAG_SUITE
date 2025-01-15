import glob
import pandas as pd
import pyproj
import numpy as np
import xarray as xr
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../PYTHON_TOOLS')
import PYTHON_TOOLS as npb

def parse_noaacdr(files, var, file_name):
    def drop_vars(ds):
        ds = ds.drop('latitude')
        ds = ds.drop('longitude')
        return ds
    print('not found, parsing data:', file_name)
    files.sort()
    obs = xr.open_mfdataset(files, preprocess = drop_vars, combine = 'nested', concat_dim = 'tdim')
    obs = obs.rename({'tdim' : 'time'})
    geo = xr.open_dataset(files[0])
    obs['lat'] = (geo['latitude'].dims, geo['latitude'].values)
    obs['lon'] = (geo['longitude'].dims, geo['longitude'].values)
    obs['ice_con'] = (obs[var].dims, obs[var].values)
    for key in list(obs.keys()):
        if key not in ['ice_con', 'lat', 'lon']:
            obs = obs.drop(key)
    obs.to_netcdf(file_name)
    print('wrote:', file_name)
    return obs

def get_extentobs_NASA(obs_dir):
    ice_dir = obs_dir + '/ice_extent/nasateam'
    files = ['gsfc.nasateam.daily.extent.1978-2021.n', 'gsfc.nasateam.daily.extent.1978-2021.s']
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
        ob['hemisphere'] = hem
        for k in ob.keys():
            if k.strip() not in ['time', 'hemisphere', v_key]:
                ob.drop(k, axis = 1, inplace = True)
            else:
                ob.rename(columns = {k: k.strip()}, inplace = True)
        ob[v_key] = ob[v_key] / 10e5
        ob.rename(columns = {v_key: 'extent'}, inplace = True)
        ob.set_index(['time', 'hemisphere'], inplace = True)
        if ii == 0:
            obs = ob
        else:
            obs = pd.concat([obs,ob])
    obs = obs.to_xarray()
    obs = obs.assign_attrs({'test_name': 'OBS-NASA'})
    return obs

def get_extentobs_bootstrap(obs_dir):
    ice_dir = obs_dir + '/ice_extent/bootstrap'
    files = ['gsfc.bootstrap.daily.extent.1978-2021.n', 'gsfc.bootstrap.daily.extent.1978-2021.s']
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
        ob['hemisphere'] = hem
        for k in ob.keys():
            if k.strip() not in ['time', 'hemisphere', v_key]:
                ob.drop(k, axis = 1, inplace = True)
            else:
                ob.rename(columns = {k: k.strip()}, inplace = True)
        ob[v_key] = ob[v_key] / 10e5
        ob.rename(columns = {v_key: 'extent'}, inplace = True)
        ob.set_index(['time', 'hemisphere'], inplace = True)
        if ii == 0:
            obs = ob
        else:
            obs = pd.concat([obs, ob])
    obs = obs.to_xarray()
    obs = obs.assign_attrs({'test_name': 'OBS-bootstrap'})
    return obs

def get_thickness(obs_dir):
    ice_dir = obs_dir + '/ICE_THICKNESS'
    obs = xr.open_mfdataset(ice_dir + '/ice*.nc')
    return obs

def get_icecon_daily_climatology(obs_dir, years = 10):
    ice_dir = obs_dir + '/ice_concentration/noaa_cdr'
    variables = ['nsidc_nt_seaice_conc', 'nsidc_bt_seaice_conc', 'cdr_seaice_conc']
    poles = ['north', 'south']
    ob = []
    for ii, pole in enumerate(poles):
        print('CALCULATING DAILY CLIMATOLOGY SEA ICE CONCENTRATIONS:', pole)
        save_file = ice_dir + '_climo_years_' + str(years) + '_parsed_' + pole + '.nc'
        if os.path.exists(save_file):
            dat = xr.open_dataset(save_file)
        else:
            dats = []
            # grab data
            for var in variables:
                obs_file = ice_dir + '_' + var + '_parsed_' + pole + '.nc'
                if os.path.exists(obs_file):
                    dats.append(xr.open_dataset(obs_file))
                else:
                    files = glob.glob(ice_dir + '/' + pole + '/*daily_' + pole[0] + '*.nc')
                    dats.append(parse_noaacdr(files, var, obs_file))
            # slice time
            obs = np.zeros((366, dats[0]['y'].size, dats[0]['x'].size))
            for i, d in enumerate(dats):
                if i == 0:
                    t_last = d['time'].values[-1]
                    t_first = np.array(pd.to_datetime(t_last) - pd.DateOffset(years= years))
                dat = d['ice_con'].sel(time = slice(t_first, t_last))
                obs = obs + dat.groupby("time.dayofyear").mean().values
            obs = obs / len(variables)
            dat = dats[0]
            dat = dat.drop('ice_con')
            dat = dat.drop('time')
            dat['dayofyear'] = np.arange(366) + 1
            dat['ice_con'] = (('dayofyear','y','x'), obs)
            t_last = np.array(pd.to_datetime(t_last))
            dat = dat.assign_attrs({'Start Year for Climo': str(t_first)})
            dat = dat.assign_attrs({'End Year for Climo': str(t_last)})
            dat = dat.assign_attrs({'Years for Climo': years})
            dat = dat.assign_attrs({'Datasets for Climo': variables})
            dat = dat.assign_attrs({'name': 'climatology'})
            dat = dat.assign_attrs({'pole': pole[0].upper() + 'H'})
            dat.to_netcdf(save_file)
            print('wrote:', save_file)
        ob.append(dat)
    return ob[0], ob[1]

def get_icecon_nt(obs_dir):
    ice_dir = obs_dir + '/ice_concentration/noaa_cdr'
    var = 'nsidc_nt_seaice_conc'
    poles = ['north', 'south']
    ob = []
    for ii, pole in enumerate(poles):
        print('READING NOAA NASA Team ICE CONCENTRATIONS:', pole)
        obs_file = ice_dir + '_' + var + '_parsed_' + pole + '.nc'
        if os.path.exists(obs_file):
            obs = xr.open_dataset(obs_file)
        else:
            files = glob.glob(ice_dir + '/' + pole + '/*daily_' + pole[0] + '*.nc')
            obs = parse_noaacdr(files, var, obs_file)
        obs = obs.assign_attrs({'pole': pole[0].upper() + 'H'})
        obs = obs.assign_attrs({'name': var})
        ob.append(obs)
    return ob[0], ob[1]

def get_icecon_bs(obs_dir):
    ice_dir = obs_dir + '/ice_concentration/noaa_cdr'
    var = 'nsidc_bt_seaice_conc'
    poles = ['north', 'south']
    ob = []
    for ii, pole in enumerate(poles):
        print('READING NOAA Boot Strap ICE CONCENTRATIONS:', pole)
        obs_file = ice_dir + '_' + var + '_parsed_' + pole + '.nc'
        if os.path.exists(obs_file):
            obs = xr.open_dataset(obs_file)
        else:
            files = glob.glob(ice_dir + '/' + pole + '/*daily_' + pole[0] + '*.nc')
            obs = parse_noaacdr(files, var, obs_file)
        obs = obs.assign_attrs({'pole': pole[0].upper() + 'H'})
        obs = obs.assign_attrs({'name': var})
        ob.append(obs)
    return ob[0], ob[1]

def get_icecon_cdr(obs_dir):
    ice_dir = obs_dir + '/ice_concentration/noaa_cdr'
    var = 'cdr_seaice_conc'
    poles = ['north', 'south']
    ob = []
    for ii, pole in enumerate(poles):
        print('READING NOAA-CDR ICE CONCENTRATIONS:', pole)
        obs_file = ice_dir + '_' + var + '_parsed_' + pole + '.nc'
        if os.path.exists(obs_file):
            obs = xr.open_dataset(obs_file)
        else:
            files = glob.glob(ice_dir + '/' + pole + '/*daily_' + pole[0] + '*.nc')
            obs = parse_noaacdr(files, var, obs_file)
        obs = obs.assign_attrs({'pole': pole[0].upper() + 'H'})
        obs = obs.assign_attrs({'name': var})
        ob.append(obs)
    return ob[0], ob[1]

def get_icecon_nsidc0051(obs_dir):
    def rename_variable(ds):
        for pv in ['F13_ICECON', 'F17_ICECON']:
            if pv in ds.keys():
                ds = ds.rename_vars({pv: 'ice_con'})
        return ds
    ice_dir = obs_dir + '/ice_concentration/nsidc-0051'
    poles = ['north', 'south']
    ob = []
    for ii, pole in enumerate(poles):
        print('READING NSIDC-0051 ICE CONCENTRATIONS:', pole)
        obs_file = ice_dir + '_parsed_' + pole + '.nc'
        if os.path.exists(obs_file):
            obs = xr.open_dataset(obs_file)
        else:
            files = glob.glob(ice_dir + '/' + pole + '/NSIDC*' + pole[0].upper() + '*.nc')
            for f in files:
                if len(f.split('/')[-1]) != 42:
                    files.remove(f)
            files.sort()
            obs = xr.open_mfdataset(files, preprocess = rename_variable) 
            # add/calc lat and lon
            inputEPSG = int(obs.geospatial_bounds_crs.split(':')[-1])
            outputEPSG = 4326
            x, y = np.meshgrid(obs['x'].values, obs['y'].values)
            proj = pyproj.Transformer.from_crs(inputEPSG, outputEPSG, always_xy = True)
            lat, lon = proj.transform(x, y)
            obs['lat'] = ({'y', 'x'}, lat)
            obs['lon'] = ({'y', 'x'}, lon)
            obs = obs.assign_attrs({'pole': pole[0].upper() + 'H'})
            obs = obs.assign_attrs({'name': 'nsidc0051'})
            # save to netcdf
            obs.to_netcdf(obs_file)
            print('wrote:', obs_file)
        ob.append(obs)
    return ob[0], ob[1]

