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

def monthly(DAT, ICECON = None, pole = 'north'):    
    print('in maps.monthly')
    if ICECON.any():
        x, y, kw = npb.maps.getICEdomain(pole)
    save_dir = DAT.save_dir
    test_name = DAT.test_name
    var_name = DAT.var_name
    long_name = DAT.long_name
    #olon, olat = DAT['TLON'].values, DAT['TLAT'].values
    olon, olat = DAT['TLON'], DAT['TLAT']
    cmap_DAT = plt.get_cmap('terrain_r')
    taus_len = np.size(DAT['tau'].values)
    taus = DAT['tau'].values[0::int(taus_len/4)]
    for tau in taus:
        fig = plt.figure(figsize=(6,8))
        axs = []
        for i, month in enumerate(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']):
            print('tau', tau, 'month', month)
            DA = DAT.isel(time = DAT['time'].dt.month.isin([int(month)])) 
            t_array = npb.timetools.time_plus_tau(DA['time'].values, tau*24)
            if ICECON.any():
                OBS = ICECON['ice_con'].sel(time = t_array).mean(dim = 'time')
            D = DA[var_name].sel(tau = tau).mean(dim = 'time')
            if pole == 'north':
                ax = fig.add_subplot(4,3,i+1, projection = ccrs.NorthPolarStereo())
                ax = npb.base_maps.Arctic(ax, labels = False)
                t_lon, t_lat = 180.0, 43.0
            elif pole == 'south':
                ax = fig.add_subplot(4,3,i+1, projection = ccrs.SouthPolarStereo())
                ax = npb.base_maps.Antarctic(ax, labels = False)
                t_lon, t_lat = 0.0, -30.
            im = ax.pcolormesh(olon, olat, D, 
                transform=ccrs.PlateCarree(), 
                vmin = 0.15,
                vmax = 1.0,
                cmap = cmap_DAT)
            ax.set_title(calendar.month_abbr[int(month)])
            ax = npb.base_maps.add_features(ax)
            if ICECON.any():
                ax.contour(x, y, OBS, [0.15], colors = ['k'], transform = ccrs.Stereographic(**kw))
                axs.append(ax)
        axs = np.array(axs)
        #xo, yo, width, height
        cbar_ax = fig.add_axes([0.15, 0.07, 0.72, 0.02])
        fig.colorbar(im, ax = axs[-1], cax = cbar_ax, orientation='horizontal' )
        axs[1].text(t_lon, t_lat, \
            test_name + '; ' + long_name + '; Forecast Day ' + str(tau), \
            fontsize = 'large', \
            fontweight = 'bold', \
            transform = ccrs.PlateCarree(), \
            ha = 'center', va = 'center')
        plt.show()
        fig_name = save_dir + '/' + pole[0].upper() + 'H_' + test_name + '_' + var_name + '_FORECASTDAY_' + str(tau) + '.png'
        print('SAVED:', fig_name)
        plt.savefig(fig_name, bbox_inches = 'tight')
        plt.close()

def difference(DAT1, DAT2, ICEOBS = None, domain = 'Arctic'):
    print('in maps.difference')
    if ICEOBS.any():
        x, y, kw = npb.maps.getICEdomain(domain)
    DES = npb.defaults_from_array(DAT1, DAT2)
    titles = DES['TITLES']
    olat, olon = DES['LAT'], DES['LON']
    VMIN, VMAX = DES['MIN'], DES['MAX']
    DMIN, DMAX = DES['DMIN'], DES['DMAX']
    plot_title = DES['PLOT_TITLE']
    save_dir = DES['SAVE_DIR']
    print('before index')
    lon, lat, DAT1 = npb.maptools.index_lon_lat_dat(olon, olat, DAT1.values)
    lon, lat, DAT2 = npb.maptools.index_lon_lat_dat(olon, olat, DAT2.values)
    cmap_DAT = plt.get_cmap('terrain_r')
    cmap_DIFF = plt.get_cmap('seismic')
    # FIGURE
    fig = plt.figure(figsize=(10, 5))
    axs, pcs = [], []
    DAT = [DAT0, DAT2, DAT1 - DAT2]
    try:
        DMIN, DMAX = DAT1['DMIN'].values, DAT1['DMAX'].values
    except:
        DMAX = np.nanmax(np.abs(DAT1 - DAT2))
        DMIN = -1.0 * DMAX
    print('looping plots')
    for i in range(3):
        if domain == 'Arctic':
            ax = fig.add_subplot(1,3,i+1, projection=ccrs.NorthPolarStereo())
            ax = npb.base_maps.Arctic(ax)
            t_lon, t_lat = 180.0, 47.0
        elif domain == 'Antarctic':
            ax = fig.add_subplot(1,3,i+1, projection=ccrs.SouthPolarStereo())
            ax = npb.base_maps.Antarctic(ax)
            t_lon, t_lat = 0.0, -37.
        cmap = cmap_DIFF if i == 2 else cmap_DAT
        MIN = DMIN if i == 2 else VMIN
        MAX = DMAX if i == 2 else VMAX
        pcs.append(ax.pcolormesh(lon, lat, DAT[i], 
           transform=ccrs.PlateCarree(), 
           vmin = MIN,
           vmax = MAX,
           cmap = cmap))
        ax.set_title(titles[i])
        ax = npb.base_maps.add_features(ax)
        if ICEOBS.any():
            ax.contour(x, y, ICEOBS, [0.15], colors = ['k'], transform = ccrs.Stereographic(**kw))
        axs.append(ax)
    axs = np.array(axs)
    cbar_ax = fig.add_axes([0.16, 0.15, 0.44, 0.05])
    fig.colorbar(pcs[0], ax = axs[1], cax = cbar_ax, orientation='horizontal' )
    cbar_ax = fig.add_axes([0.70, 0.15, 0.17, 0.05])
    fig.colorbar(pcs[-1], ax = axs[1], cax = cbar_ax, orientation='horizontal' )
    axs[1].text(t_lon, t_lat, plot_title, fontweight = 'bold', fontsize = 16, ha = 'center', transform = ccrs.PlateCarree())
    fig_name = save_dir + '/' +  domain.upper() + '_' +\
        plot_title.replace(':','').replace(' ','').replace(',','') + '_' +\
        titles[0].replace(' ','') + '_' +\
        titles[1].replace(' ','') + '.png'
    print('SAVED:', fig_name)
    plt.savefig(fig_name, bbox_inches = 'tight')
    plt.close()
