import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class line(object):
    da = None
    region = 'global'
    obs = False
    cell_area = False
    plot_spread = False
    debug_plot = False
    @classmethod
    def create(cls):
        da = cls.da
        region = cls.region
        obs = cls.obs
        cell_area = cls.cell_area
        SPREAD = cls.plot_spread
        DEBUG = cls.debug_plot
        exp_names = list(da.experiment.values)
        hemisphere = {"Arctic": "NH", "Antarctic" : "SH"} 
        if 'hemisphere' in da.dims:
            da = da.sel(hemisphere = hemisphere[region])    
        SUFFIX = "_EXPS_" + "_".join(exp_names)
        if SPREAD:
            fig_name = 'SPREAD_' + da.name + '_' + region + '_' + da.period_label + SUFFIX + '.png'
        else:
            fig_name = da.name + '_' + region + '_' + da.period_label + SUFFIX + '.png'
        if len(fig_name) > 255:
            short_names = [item.rsplit('_', 1)[-1] for item in exp_names]
            SUFFIX = "_EXPS_" + "_".join(short_names)
            fig_name = da.name + '_' + region + '_' + da.period_label + SUFFIX + '.png'
            if len(fig_name) > 255:
                print("FATAL: fig_name too long", len(fig_name), fig_name)
                exit(1)
        ####################################
        if da.name in ['ice_extent', 'ice_volume', 'snow_volume']:
            dat = da
        else:
            if 'TLAT' in da.coords:
                da = da.rename({"TLAT": "latitude", "TLON": "longitude"})
                cell_area = cell_area.rename({"TLAT": "latitude", "TLON": "longitude"})    
            if region == 'nino34':
                lat_mask = (da.latitude >= -5) & (da.latitude <= 5)
                lon_mask = (da.longitude >= 190) & (da.longitude <= 240)
                if not isinstance(obs, bool):
                    obs = obs.sel(latitude=slice(-5,5), longitude=slice(190,240))
            elif region == 'tropics':
                lat_mask = (da.latitude >= -20) & (da.latitude <= 20)
                lon_mask = (da.longitude >= 120) & (da.longitude <= 260)
                if not isinstance(obs, bool):
                    obs = obs.sel(latitude=slice(-20,20), longitude=slice(120,260))
            elif region == 'equator':
                lat_mask = (da.latitude >= -5) & (da.latitude <= 5)
                lon_mask = (da.longitude >= 120) & (da.longitude <= 260)
                if not isinstance(obs, bool):
                    obs = obs.sel(latitude=slice(-5,5), longitude=slice(120,260))
            elif region == 'Arctic':
                lat_mask = (da.latitude >= 70) & (da.latitude <= 90)
                lon_mask = (da.longitude >= 0) & (da.longitude <= 360)
                if not isinstance(obs, bool):
                    obs = obs.sel(latitude=slice(70,90), longitude=slice(0,360))
            elif region == 'Antarctic':
                lat_mask = (da.latitude >= -90) & (da.latitude <= -70)
                lon_mask = (da.longitude >= 0) & (da.longitude <= 360)
                if not isinstance(obs, bool):
                    obs = obs.sel(latitude=slice(-90,-70), longitude=slice(0,360))            
            if region != 'global':
                da = da.where(lat_mask & lon_mask, drop=True)
            grid_dims = tuple(set(da.latitude.dims) | set(da.longitude.dims))
            dim_slices = {dim: da[dim] for dim in cell_area.dims if dim in da.dims}
            weights = cell_area.sel(dim_slices).fillna(0)
            weights.name = "weights"
            # Collapse spatial grid FIRST
            dat = da.weighted(weights).mean(grid_dims)
            if not isinstance(obs, bool):
                obs_w = np.cos(np.deg2rad(obs.latitude))
                obs = obs.weighted(obs_w).mean(dim=['latitude', 'longitude'], keep_attrs=True).compute()
        # Handle Spread computation AFTER spatial reduction
        if SPREAD and da.name:
            dat = dat.max(dim='member') - dat.min(dim='member')
            if da.name not in ['ice_extent', 'ice_volume', 'snow_volume']:
                y_label = da.attrs['y_label']
                period_label = da.attrs['period_label']
                dat = dat.max(dim='member') - dat.min(dim='member')
                dat.attrs['y_label'] = y_label
                dat.attrs['period_label'] = period_label
        fig, ax = plt.subplots()
        if len(da.experiment.values) == 2:
            colors = ['blue', 'green']
        else:
            colors = plt.cm.tab10(np.linspace(0, 1, len(da.experiment)))
        for i, n in enumerate(da.experiment.values):
            sub_dat = dat.sel(experiment=n)
            if SPREAD:
                mean = sub_dat.compute()
                ax.plot(da.y_label, mean, color=colors[i], label=n)
            else:
                # Materialize 1D time-series into RAM cleanly
                mean = sub_dat.mean(dim='member').compute()
                lower = sub_dat.min(dim='member').compute()
                upper = sub_dat.max(dim='member').compute()
                print(mean)
                ax.plot(da.y_label, mean, color=colors[i], label=n)
                ax.fill_between(da.y_label, lower, upper, color=colors[i], alpha=0.2)
        if not isinstance(obs, bool):
            ax.plot(da.y_label, obs, color='k', label=obs.title)
        ax.set_xlim(da.y_label.min(), da.y_label.max())
        ax.legend(frameon=False)
        ax.set_ylabel(da.name + (' Spread' if SPREAD else ''))
        ax.set_title(region + ': ' + da.period_label)
        if DEBUG:
            plt.show()
            exit(1)
        fig.savefig(fig_name, dpi=300, bbox_inches='tight')
        print('SAVED:', fig_name)
        plt.close(fig)

