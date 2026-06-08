################################################################################
# Neil P. Barton
# (c) Neil P. Barton, 2014-02-26 Wed 01:42 AM UTC
################################################################################
# These Modules Provide default maps based on basemap and matplotlib
#   updated to python3 12/14/2020
################################################################################///
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.ticker as mticker
import numpy as np

def add_features(ax):
    ax.coastlines()
    ax.add_feature(cfeature.LAKES, edgecolor = "black", facecolor = 'None' )
    #ax.add_feature(cfeature.RIVERS, edgecolor = "black")
    ax.add_feature(cfeature.BORDERS, linestyle="--")
    return ax

class Global(object):
     def __new__(self, ax = None, labels = True):
        if not ax:
            ax = plt.axes(projection=ccrs.Mollweide())
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False,
               linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.xlines = True
        xticks = [-180, -120,  -60, 0, 60, 120, 180]
        yticks = [-90, -60, -30, 0, 30, 60, 90]
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        if labels:
            for x in xticks[1::]:
                suffix = 'W' if x < 0 and abs(x) != 180 else 'E'
                txt = str(abs(x)) + r'$^{\circ}$' + suffix
                ax.text(x,-60,txt, size = 8, ha = 'center', va = 'center', transform=ccrs.Geodetic())
            for y in yticks[1:-1]:
                suffix = 'S' if y < 0  else 'N'
                txt = str(abs(y)) + r'$^{\circ}$' + suffix + r'   '
                ax.text(-180,y,txt, size = 8, ha = 'right', va = 'center', transform=ccrs.Geodetic())
        return ax
        
class Arctic(object):
     def __new__(self, ax = None, labels = True):
        if not ax:
            ax = plt.axes(projection=ccrs.NorthPolarStereo( central_longitude=180.0 ))
        ax.set_extent([-180, 180, 55, 90], ccrs.PlateCarree())
        # set up lat and lon
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False,
               linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.xlines = True
        xticks = [-180, -120, -60, 0, 60, 120, 180]
        yticks = [60, 70, 80]
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        # ticks
        if labels:
            print('in labels')
            for x in xticks[1:-1]:
                suffix = 'W' if x < 0 and abs(x) != 180 else 'E'
                txt = str(abs(x)) + r'$^{\circ}$' + suffix
                ax.text(x,60,txt, size = 8, ha = 'center', va = 'center', transform=ccrs.Geodetic())
            for y in yticks:
                suffix = 'S' if y < 0  else 'N'
                txt = str(abs(y)) + r'$^{\circ}$' + suffix + r'   '
                ax.text(-180,y,txt, size = 8, ha = 'left', va = 'center', transform=ccrs.Geodetic())
        ## circle 
        theta = np.linspace(0, 2*np.pi, 100)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax.set_boundary(circle, transform=ax.transAxes)
        return ax

class Antarctic(object):
     def __new__(self, ax = None, labels = True):
        if not ax:
            ax = plt.axes(projection=ccrs.SouthPolarStereo())
        ax.set_extent([-180, 180, -45, -90], ccrs.PlateCarree())
        # set up lat and lon
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False,
               linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.xlines = True
        xticks = [-180, -120, -60, 0, 60, 120, 180]
        yticks = [-50, -60, -70, -80]
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        # ticks
        if labels:
            for x in xticks[1:-1]:
                suffix = 'W' if x < 0 and abs(x) != 180 else 'E'
                txt = str(abs(x)) + r'$^{\circ}$' + suffix
                ax.text(x,-50,txt, size = 8, ha = 'center', va = 'center', transform=ccrs.Geodetic())
            for y in yticks:
                suffix = 'S' if y < 0  else 'N'
                txt = str(abs(y)) + r'$^{\circ}$' + suffix + r'   '
                ax.text(-180,y,txt, size = 8, ha = 'left', va = 'center', transform=ccrs.Geodetic())
        # circle 
        theta = np.linspace(0, 2*np.pi, 100)
        center, radius = [0.5, 0.5], 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax.set_boundary(circle, transform=ax.transAxes)
        return ax

