# some plotting graph 
import calendar
import cartopy.crs as ccrs
#import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) )
import PYTHON_TOOLS as npb
import warnings
#warnings.filterwarnings("ignore")
#def fxn():
#    warnings.warn("deprecated", DeprecationWarning)
#with warnings.catch_warnings():
#    warnings.simplefilter("ignore")
#    fxn()

def getICEdomain(domain):
    dx = dy = 25000
    if domain == 'north':
        x = np.arange(-3850000, +3750000, +dx)
        y = np.arange(+5850000, -5350000, -dy)
        kw = dict(central_latitude=90, central_longitude=-45, true_scale_latitude=70)
    elif domain == 'south':
        x = np.arange(-3950000, +3950000, +dx)
        y = np.arange(+4350000, -3950000, -dy)
        kw = dict(central_latitude=-90, central_longitude=0, true_scale_latitude=-70)
    return x, y, kw

class CICE(object):
    save_dir = './'
    @classmethod
    def create(cls):
        olon, olat = cls.dat['TLON'], cls.dat['TLAT']
        d_tau = cls.tau
        if cls.times.size == 1:
            dat = cls.dat[cls.var_name].sel(time = cls.times, forecast_hour = d_tau)
        else:
            dat = cls.dat[cls.var_name].sel(time = cls.times, forecast_hour = d_tau).mean(dim = 'time') 
        t_array = npb.timetools.time_plus_tau(cls.times.values, cls.tau)
        if cls.times.size == 1:
            obs = cls.obs['ice_con'].sel(time = t_array)
        else:
            obs = cls.obs['ice_con'].sel(time = t_array).mean(dim = 'time')
        fig = plt.figure(figsize=(8, 6))
        if cls.pole == 'north':
            ax = fig.add_subplot(1,1,1, projection = ccrs.NorthPolarStereo())
            ax = npb.base_maps.Arctic(ax, labels = False)
            t_lon, t_lat = 180.0, 53.0
        elif cls.pole == 'south':
            ax = fig.add_subplot(1,1,1, projection = ccrs.SouthPolarStereo())
            ax = npb.base_maps.Antarctic(ax, labels = False)
            t_lon, t_lat = 0.0, -43.
        if cls.var_name == 'aice':
            vmin = 0.15
            vmax = 1.0
            cmap_DAT = plt.get_cmap('terrain_r')
        else:
            if cls.pole == 'north':
                vmin = dat.where(cls.dat['TLAT'] > 0).min().values
                vmax = dat.where(cls.dat['TLAT'] > 0).max().values
            elif cls.pole == 'south':
                vmin = dat.where(cls.dat['TLAT'] < 0).min().values
                vmax = dat.where(cls.dat['TLAT'] < 0).max().values
            dat = dat.where(dat > 0)
            cmap_DAT = plt.get_cmap('jet')
        im = ax.pcolormesh(olon, olat, dat, 
            transform=ccrs.PlateCarree(), 
            vmin = vmin,
            vmax = vmax,
            cmap = cmap_DAT)
        ax = npb.base_maps.add_features(ax)
        ax.text(t_lon, t_lat, cls.title, \
            fontsize = 'large', \
            fontweight = 'bold', \
            transform = ccrs.PlateCarree(), \
            ha = 'center', va = 'center')
        x, y, kw = npb.maps.getICEdomain(cls.pole)
        ax.contour(x, y, obs, [0.15], colors = ['#A09898'], linewidths = 1.5, transform = ccrs.Stereographic(**kw))
        cbar_ax = fig.add_axes([0.25, 0.07, 0.52, 0.035])
        cbar = fig.colorbar(im, cax = cbar_ax, orientation='horizontal' )
        cbar_label = {'aice' : 'Concentration', 'hi' : 'Thickness (m)' }
        cbar.set_label(cbar_label[cls.var_name])
        fig_name = cls.save_dir + '/' + cls.pole[0].upper() + 'H_map' \
            + cls.title.replace(' ','').replace(':','') + '_' + cls.var_name + '.png'
        print('SAVED:', fig_name)
        plt.savefig(fig_name, bbox_inches = 'tight')
        #plt.show()

class IIEE(object):
    save_dir = './'
    @classmethod
    def create(cls):
        fig = plt.figure(figsize=(8, 6))
        if cls.pole == 'north':
            ax = fig.add_subplot(1,1,1, projection = ccrs.NorthPolarStereo())
            ax = npb.base_maps.Arctic(ax, labels = False)
            t_lon, t_lat = 180.0, 53.0
            var = 'diff_NH'
        elif cls.pole == 'south':
            ax = fig.add_subplot(1,1,1, projection = ccrs.SouthPolarStereo())
            ax = npb.base_maps.Antarctic(ax, labels = False)
            t_lon, t_lat = 0.0, -43.
            var = 'diff_SH'
        if cls.times.size == 1:
            dat = cls.dat[var].sel(time = cls.times, forecast_hour = cls.tau)
        else:
            dat = cls.dat[var].sel(time = cls.times, forecast_hour = cls.tau).mean(dim = 'time') 
        dat = dat.where(dat != 0)
        vmin, vmax = -1, 1
        cmap_DAT = plt.get_cmap('coolwarm')
        x, y, kw = npb.maps.getICEdomain(cls.pole)
        im = ax.pcolormesh(x, y, dat, 
            vmin = vmin,
            vmax = vmax,
            cmap = cmap_DAT,
            transform = ccrs.Stereographic(**kw))
        ax = npb.base_maps.add_features(ax)
        ax.text(t_lon, t_lat, cls.title, \
            fontsize = 'large', \
            fontweight = 'bold', \
            transform = ccrs.PlateCarree(), \
            ha = 'center', va = 'center')
        cbar_ax = fig.add_axes([0.25, 0.07, 0.52, 0.035])
        cbar = fig.colorbar(im, cax = cbar_ax, orientation='horizontal' )
        cbar.set_label('Model Minus Obs')
        fig_name = cls.save_dir + '/' + cls.pole[0].upper() + 'H_map' \
            + cls.title.replace(' ','').replace(':','') + '_' + 'IIEE_DIFF.png'
        print('SAVED:', fig_name)
        plt.savefig(fig_name, bbox_inches = 'tight')
        #plt.show()

