import calendar
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import os
from . import utils
debug = utils.debug(False)
colors = ['maroon','blue','darkgreen']
class ice_extent(object):
    pole = 'north'
    save_dir = './'
    @classmethod
    def create(cls):
        ########################
        # plot model data with tau
        fig_name = 'ice_extent_' + cls.title.replace(' ','_') + '_' 
        if cls.times.size == 1:
            model = cls.MODEL['extent'].sel(time = cls.times, pole = cls.pole)
        else:
            model = cls.MODEL['extent'].sel(time = cls.times, pole = cls.pole).mean('time')
        model_taus = model['forecast_hour'].values
        for i, name in enumerate(model['name'].values):
            dat = model.sel(name = name)
            if 'member' not in cls.MODEL.dims:
                plt.plot(model_taus/24.0, dat.values, color = colors[i], label = name)
            else:
                plt.plot(model_taus/24.0, dat.mean('member').values, 
                        color = colors[i], 
                        linewidth = 2.0, 
                        label = ds.test_name )
                plt.fill_between(model_taus/24.0, 
                        dat.min('member').values, 
                        dat.max('member').values, 
                        color = colors[i], 
                        alpha = 0.5)
            fig_name = fig_name + name.replace(':', '').replace(' ','').replace('/','') + '_'
        ########################
        # observations; get times for obs
        if cls.times.size == 1:
            obs = cls.OBS['extent'].sel(time = cls.times, pole = cls.pole)
        else:
            obs = cls.OBS['extent'].sel(time = cls.times, pole = cls.pole).mean('time')
        tau = obs['forecast_hour'].values/24.0
        styles = ['-','--','-.',':']
        for i, name in enumerate(obs['name'].values):
            y = obs.sel(name = name)
            m = ~np.isnan(y)
            plt.plot(tau[m], y[m], color = 'k', linestyle = styles[i], linewidth = 2.0, label = name)
            fig_name = fig_name + name.replace(':', '').replace(' ','').replace('/','') + '_'
        ########################
        # figure options
        fig_name = cls.save_dir + '/' + cls.pole[0].upper() + 'H_' + fig_name[0:-1] + '.png'
        plt.legend(frameon = False)
        plt.xlim(model_taus[0]/24, model_taus[-1]/24)
        plt.xlabel('Forecast Day')
        plt.ylabel(cls.pole[0].upper() + 'H Sea Ice Extent')
        plt.title(cls.pole[0].upper() + 'H Sea Ice Extent: ' + cls.title)
        plt.savefig(fig_name, bbox_inches = 'tight')
        print('SAVED:', fig_name)
        if debug:
            plt.show()
        plt.close()

def monthdiff_imshow(DAT1, DAT2, var = 'extent', pole = 'north'):
    dat_plot = []
    y_label = []
    try:
        taus = DAT1['tau'].values
    except:
        taus = DAT2['tau'].values
    for m in np.arange(12) + 1:
        dat = []
        y_label.append(calendar.month_abbr[m])
        d1_time = DAT1['time'].isel(time = DAT1['time'].dt.month.isin([m]))
        d2_time = DAT2['time'].isel(time = DAT2['time'].dt.month.isin([m]))
        same_times = np.array(list(set(d1_time.values) & set(d2_time.values)))
        if len(same_times) > 0:
            for ds in [DAT1, DAT2]:
                if 'tau' not in ds.keys():
                    # Observations
                    last_tau = int(DAT1['tau'][-1].values)
                    ob = []
                    for t in same_times:
                        t_last = t + np.timedelta64(last_tau, 'D')
                        obs = ds[var].sel(time = slice(t, t_last), pole = pole).values
                        ob.append(np.interp(taus, np.arange(0, obs.size), obs))
                    d = np.mean(np.array(ob), axis = 0)
                else:
                    if 'member' in ds.dims:
                        d = ds[var].sel(time = same_times, pole = pole).mean(['time','member'])
                    else:
                        d = ds[var].sel(time = same_times, pole = pole).mean('time')
                d = np.ma.masked_where(d == 0, d)
                dat.append(d)
            le = min(dat[0].size, dat[1].size)
            diff = dat[0][0:le] - dat[1][0:le]
            if (diff.size > np.max(taus)): # if taus aren't integers of days
                diff = np.interp(np.arange(np.min(taus), np.max(taus) + 1), taus, diff)
        else:
            diff = np.empty(diff.size)
        dat_plot.append(diff)
    dat_plot = np.array(dat_plot)
    try:
        title = pole[0].upper() + 'H ' + var.upper() + ' Difference: ' + DAT1.test_name + ' minus ' + DAT2.test_name
    except:
        title = pole[0].upper() + 'H ' + var.upper() + ' Difference:  DAT1 minus DAT2'
    print(title)
    print(' Min:', np.round(np.nanmin(dat_plot),2), '  Max:', np.round(np.nanmax(dat_plot),2))
    try:
        vmin = DAT1.DMIN
        vmax = DAT1.DMAX
    except:
        mi = np.nanmin(dat_plot)
        ma = np.nanmax(dat_plot)
        if abs(mi) > abs(ma):
            vmin = mi
            vmax = -1 * vmin
        else:
            vmax = ma
            vmin = -1 * vmax
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1,1,1)
    cmap = plt.get_cmap('seismic')
    im = ax.imshow(dat_plot, cmap = cmap, 
                    vmin = vmin, vmax = vmax, 
                    aspect = 'auto', 
                    interpolation = 'none')
    cbar = plt.colorbar(im)
    cbar.set_label('million sq km') 
    taus = taus[0:le]
    taus = np.arange(np.min(taus), np.max(taus) + 1)
    plt.xticks(np.arange(taus.size)[::3], taus[::3].astype('int'))
    plt.yticks(np.arange(12), y_label)
    ax.set_xlabel('Forecast Day')
    ax.set_title(title, fontsize = 16, fontweight = 'bold')
    #plt.show()
    try:
        save_dir = DAT1.save_dir
    except:
        save_dir = './'
    fig_name = save_dir + '/' + pole[0].upper() + 'H_' + var + '_MONTHvsTAU_' + title[2::].replace(' ','').replace(':','').replace('/','') + '.png'
    plt.savefig(fig_name, bbox_inches = 'tight')
    plt.close()
    print('SAVED:', fig_name)

class iiee(object):
    pole = 'north'
    save_dir = './'
    @classmethod
    def create(cls):
        exp_title = ''
        tau_max = cls.DATS[0]['forecast_hour'].max().values
        for i, dat in enumerate(cls.DATS):
            for j, ob in enumerate(cls.OBS_TYPES):
                if dat.test_name not in exp_title:
                    exp_title = exp_title + dat.test_name + '_'
                if cls.times.size == 1:
                    data = dat['iiee'].sel(obs_type = ob, 
                                           hemisphere = cls.pole, 
                                           time = cls.times, 
                                           forecast_hour = slice(0,tau_max))
                else:
                    data = dat['iiee'].sel(obs_type = ob, 
                                           hemisphere = cls.pole, 
                                           time = cls.times, 
                                           forecast_hour = slice(0,tau_max)).mean('time')
                default_style = {'style': '-', 'c': colors[i], 'label': f'{dat.test_name} vs {ob}'}
                style_config = {'persistence': {'style': ':', 'c': 'k', 'label': ob},
                                'climatology': {'style': '--', 'c': 'k', 'label': ob}}
                plot_style = default_style
                for key, style_props in style_config.items():
                    if key in ob:
                        plot_style = style_props
                        break # Stop after the first match
                style, c, label = plot_style['style'], plot_style['c'], plot_style['label']
                plot = (ob not in ['persistence', 'climatology']) or (i + 1 == len(cls.DATS))
                if plot:
                    if 'member' in data.dims:
                        plt.plot(data['forecast_hour'].values/24, data.mean('member').values, 
                             linewidth = 2.0, color = c, linestyle = style, label = label )
                        plt.fill_between(data['forecast_hour'].values/24, data.min('member').values, 
                             data.max('member').values, color = c, alpha = 0.5)
                    else:
                        plt.plot(data['forecast_hour'].values/24, data.values, 
                             linewidth = 2.0, color = c, linestyle = style, label = label)
        if cls.pole == 'NH':
            t = 'Arctic '
        elif cls.pole == 'SH':
            t = 'Antarctic '
        plt.title(t + cls.title)
        plt.xlim(data['forecast_hour'].min().values/24, data['forecast_hour'].max().values/24)
        plt.ylabel('IIEE')
        plt.xlabel('Forecast Day')
        plt.legend(frameon = False)
        fig_name = cls.save_dir + '/' + cls.pole[0].upper() + 'H_iiee_' + exp_title + cls.title.replace(' ','').replace(':','').replace('/','') + '.png'
        plt.savefig(fig_name)
        print('SAVED:', fig_name)  
        if debug:
            plt.show()
        plt.close()
               
class iiee_min_imshow(object):
    pole = 'north'
    save_dir = './'
    @classmethod
    def create(cls):
        exp_title = ''
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(1,1,1)
        ob_type_month, y_label = [], []
        for m in np.arange(12) + 1:
            plot_data = []
            y_label.append(calendar.month_abbr[m])
            times = cls.DAT['time'].isel(time = cls.DAT['time'].dt.month.isin([m]))
            min_ob_type = []
            for j, ob in enumerate(cls.OBS_TYPES):
                data = cls.DAT['iiee'].sel(obs_type = ob, pole = cls.pole, time = times).mean('time')
                if 'member' in cls.DAT.dims:
                    data = data.mean('member') 
                min_ob_type.append(data.values)
            ob_type_month.append(np.argmin(np.array(min_ob_type),axis = 0))
        # get colors 
        cmap = ListedColormap(["blue", "grey", "black"])
        im = ax.imshow(ob_type_month, cmap = cmap, 
                        vmin = 0, vmax = len(cls.OBS_TYPES)-1,
                        aspect = 'auto', interpolation = 'none')
        for ii, ob in enumerate(cls.OBS_TYPES):
            print(ob)
            c = cmap(ii/(len(cls.OBS_TYPES) - 1))
            if ob.split('_')[-1] == 'conc':
                tt = cls.DAT.test_name
            else:
                tt = ob.split('_')[-1].capitalize()
            plt.text(np.max(data['tau'].values) + 2 , 4 + ii, tt, color = c, fontsize = 16, fontweight = 'bold')
        taus = data['tau'].values
        plt.xticks(np.arange(len(data['tau'].values))[::3], data['tau'].values[::3].astype('int'))
        plt.yticks(np.arange(12), y_label)
        ax.set_xlabel('Forecast Day')
        if cls.pole == 'north':
            title = cls.DAT.test_name + ': NH Min IIEE' 
        elif cls.pole == 'south':
            title = cls.DAT.test_name + ': SH Min IIEE'
        ax.set_title(title, fontsize = 16, fontweight = 'bold')
        plt.tight_layout()
        #plt.show()
  
