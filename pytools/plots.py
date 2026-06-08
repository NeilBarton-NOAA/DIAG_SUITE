import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def line(ds, region = 'globe', obs = False, cell_area = False, DEBUG = False):
    exp_names = list(ds.experiment.values)
    SUFFIX = "_EXPS_" + "_".join(exp_names)
    ####################################
    if ds.name in ['ice_extent', 'ice_volume', 'snow_volume']:
        dat = ds
    else:
        if 'TLAT' in ds.coords:
            ds = ds.rename({"TLAT": "latitude"})
            ds = ds.rename({"TLON": "longitude"})
            cell_area = cell_area.rename({"TLAT": "latitude"})
            cell_area = cell_area.rename({"TLON": "longitude"})
        if region == 'nino34':
            lat_mask = (ds.latitude >= -5) & (ds.latitude <= 5)
            lon_mask = (ds.longitude >= 190) & (ds.longitude <= 240)
            if not isinstance(obs, bool):
                obs = obs.sel(latitude=slice(-5,5), longitude=slice(190,240))
        if region == 'tropics':
            lat_mask = (ds.latitude >= -20) & (ds.latitude <= 20)
            lon_mask = (ds.longitude >= 120) & (ds.longitude <= 260)
            if not isinstance(obs, bool):
                obs = obs.sel(latitude=slice(-20,20), longitude=slice(120,260))
        if region == 'equator':
            lat_mask = (ds.latitude >= -5) & (ds.latitude <= 5)
            lon_mask = (ds.longitude >= 120) & (ds.longitude <= 260)
            if not isinstance(obs, bool):
                obs = obs.sel(latitude=slice(-5,5), longitude=slice(120,260))
        if region == 'Arctic':
            lat_mask = (ds.latitude >= 70) & (ds.latitude <= 90)
            lon_mask = (ds.longitude >= 0) & (ds.longitude <= 360)
            if not isinstance(obs, bool):
                obs = obs.sel(latitude=slice(70,90), longitude=slice(0,360))
        if region == 'Antarctic':
            lat_mask = (ds.latitude >= -90) & (ds.latitude <= -70)
            lon_mask = (ds.longitude >= 0) & (ds.longitude <= 360)
            if not isinstance(obs, bool):
                obs = obs.sel(latitude=slice(-90,-70), longitude=slice(0,360))
        if region != 'global':
            ds = ds.where(lat_mask & lon_mask, drop=True)
        grid_dims = tuple(set(ds.latitude.dims) | set(ds.longitude.dims))
        dim_slices = {dim: ds[dim] for dim in cell_area.dims if dim in ds.dims}
        weights = cell_area.sel(dim_slices).fillna(0)
        weights.name = "weights"
        dat = ds.weighted(weights).mean(grid_dims)
        if not isinstance(obs, bool):
            obs_w = np.cos(np.deg2rad(obs.latitude))
            obs = obs.weighted(obs_w).mean(dim = ['latitude', 'longitude'], keep_attrs=True)
    plt.figure()
    if len(ds.experiment.values) == 2:
        colors = ['blue', 'green']
    else:
        colors = plt.cm.tab10(np.linspace(0, 1, len(ds.experiment)))
    for i, n in enumerate(ds.experiment.values):
        mean = dat.sel(experiment = n).mean(dim = 'member') 
        #lower = dat.sel(experiment = n).min(dim = 'member')
        #upper = dat.sel(experiment = n).max(dim = 'member') 
        lower = dat.sel(experiment = n).quantile(0.10, dim = 'member') 
        upper = dat.sel(experiment = n).quantile(0.90, dim = 'member') 
        plt.plot(mean.time, mean, color=colors[i], label = n)
        plt.fill_between(mean.time, lower, upper, color=colors[i], alpha=0.2)
    # plot obs
    if not isinstance(obs, bool):
        plt.plot(obs.time, obs, color='k', label = obs.title)
    plt.legend(frameon=False)
    plt.ylabel(ds.name)
    plt.title(region)
    if DEBUG:
        plt.show(); exit(1)
    fig_name = ds.name + '_' + region + '_' + pd.to_datetime(mean.time.values[0]).strftime('%Y%m%d') + SUFFIX + '.png'
    plt.savefig(fig_name, dpi=600, bbox_inches='tight')
    print('SAVED:', fig_name)

