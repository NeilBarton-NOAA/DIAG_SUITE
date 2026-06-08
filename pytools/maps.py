import pandas as pd
import numpy as np
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import imageio.v3 as iio

############
# model data
limits = {  'SST':                  [(0, 30), (0, 30), (-2.0, 2.0)],
            'SSS':                  [(25, 40), (25, 40), (-3, 3)],
            'SSH':                  [(-2.0, 1.0), (-2., 1.), (-0.5, 0.5)],
            'WWV':                  [(1000.0, 2000.0), (1000., 2000.), (-800., 800.)],
            'MLD_003':              [(0.0, 40.0), (0., 40.), (-50., 50.)],
            'SW':                   [(50.0, 300.0), (50., 300.), (-30., 30.)],
            'SVA':                  [(25, 35), (25, 35), (-1, 1)],
            'dt20c':                [(100, 200), (100, 200), (-50, 50)],
            'T300':                 [(10, 30), (10, 30), (-15, 15)],
            'Tsfc':                 [(-32, 0), (-32, 0), (-5, 5)],
            'hs':                   [(0, 0.6), (0, 0.6), (-0.25, 0.25)],
            'hi':                   [(0, 4), (0, 4), (-1, 1)],
            'albsni':               [(0, 100), (0, 100), (-100, 100)],
            'ocnheat':              [(10, 30), (10, 30), (-5, 5)]
         }   

#c_maps = ['magma', 'magma', 'RdBu_r']
c_maps = ['plasma', 'plasma', 'RdBu_r']

def three_panel(ds, DEBUG = False):
    exp_names = list(ds.experiment.values)
    SUFFIX = "_EXPS_" + "_".join(exp_names)
    exp_names.append(exp_names[0] + ' minus ' + exp_names[1])
    loop_files=[]
    for t in ds.time:
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 5), \
            subplot_kw={'projection': ccrs.Robinson(central_longitude=180)})
        for i, ax in enumerate(axes):
            # Select the data (example: first 3 time steps)
            if i == 2:
                dat1 = ds.sel(time = t, experiment = exp_names[0]).mean(dim = 'member')
                dat2 = ds.sel(time = t, experiment = exp_names[1]).mean(dim = 'member')
                dat = dat1 - dat2
            else:
                dat = ds.sel(time = t, experiment = exp_names[i]).mean(dim = 'member')
            # Plot using xarray's built-in plotting (transform is CRITICAL here)
            if ds.name in limits:
                v_min, v_max = limits[ds.name][i]
            else:
                v_min, v_max = dat.min().values, dat.max().values
                print('limits not set:', v_min, v_max)
            # Levels for Colormap
            levels = np.linspace(v_min, v_max, 17)
            cmap = plt.get_cmap(c_maps[i])  # Choose your colormap
            norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
            dat.plot(
                ax=ax, 
                transform=ccrs.PlateCarree(), # Data is usually lat/lon (PlateCarree)
                cmap = cmap,
                norm = norm,
                levels = levels,
                extend = 'both',
                cbar_kwargs={'orientation': 'horizontal', 'pad': 0.05, 'ticks': np.linspace(v_min, v_max, 5)},
            )
            # lines
            gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5, linestyle='--')
            gl.ylocator = mticker.FixedLocator([-60,-20,-5,0,5,20,60])
            gl.xlocator = mticker.FixedLocator([-170,-120,-80,120])
            # Add map features
            ax.coastlines()
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.set_global() # Ensures the whole world is shown
            ax.set_title(str(t.dt.year.values) + '-' + str(t.dt.month.values).zfill(2) + ': ' + exp_names[i])
        plt.tight_layout()
        name = ds.name + '_' + str(t.dt.year.values) + '-' + str(t.dt.month.values).zfill(2) + SUFFIX + '.png'
        loop_files.append(name)
        if DEBUG:
            plt.show(); exit(1)
        plt.savefig(name, dpi = 400)
        print("SAVED:", name)
        plt.close()
    loop_name = ds.name + '_' + pd.to_datetime(ds.time.values[0]).strftime('%Y%m') + SUFFIX + '.gif'
    frames = [iio.imread(img, mode='RGB') for img in loop_files]
    iio.imwrite(loop_name, frames, duration=500, loop=0, dither=0)
    print("SAVED:", loop_name)

def six_panel(ds, DEBUG = False):
    exp_names = list(ds.experiment.values)
    SUFFIX = "_EXPS_" + "_".join(exp_names)
    exp_names.append(exp_names[0] + ' minus ' + exp_names[1])
    gif_files=[]
    for t in ds.time:
        fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(14, 8), gridspec_kw={'height_ratios': [1, 1, 0.04]})
        for ax in axes.flat:
            ax.axis('off')
        for row in range(2):
            for col in range(3):
                proj = ccrs.NorthPolarStereo() if row == 0 else ccrs.SouthPolarStereo()
                i = ((row * 3) + col) + 1
                ax = fig.add_subplot(3, 3, i, projection=proj)
                if row == 0:
                    ax.set_extent([-180, 180, 55, 90], ccrs.PlateCarree()) 
                else:
                    ax.set_extent([-180, 180, -90, -45], ccrs.PlateCarree())
                # circle
                theta = np.linspace(0, 2*np.pi, 100)
                center, radius = [0.5, 0.5], 0.5
                verts = np.vstack([np.sin(theta), np.cos(theta)]).T
                circle = mpath.Path(verts * radius + center)
                ax.set_boundary(circle, transform=ax.transAxes)
                # data
                if col == 2:
                    dat1 = ds.sel(time = t, experiment = exp_names[0]).mean(dim = 'member')
                    dat2 = ds.sel(time = t, experiment = exp_names[1]).mean(dim = 'member')
                    dat = dat1 - dat2
                else:
                    dat = ds.sel(time = t, experiment = exp_names[col]).mean(dim = 'member')
                # Plot using xarray's built-in plotting (transform is CRITICAL here)
                if ds.name in limits:
                    v_min, v_max = limits[ds.name][col]
                else:
                    v_min, v_max = dat.min().values, dat.max().values
                    print('limits not set:', v_min, v_max)
                # pcolormesh with levels
                levels = np.linspace(v_min, v_max, 13)
                cmap = plt.get_cmap(c_maps[col])  # Choose your colormap
                norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)
                cf = ax.pcolormesh(dat.TLON, dat.TLAT, dat, transform = ccrs.PlateCarree(),
                                  cmap=cmap, norm=norm)
                if row == 1:
                    cax = axes[2, col] # Grab the preallocated slot in the 3rd row
                    cax.axis('on')     # Turn the frame back on so labels show up
                    cbar = plt.colorbar(cf, cax=cax, orientation='horizontal',
                                        ticks=np.linspace(v_min, v_max, 5), extend = 'both')
                    cbar.ax.tick_params(labelsize=10)
                # plot options
                gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False, linewidth=1, color='gray',
                              alpha=0.5, linestyle='--')
                gl.ylocator = mticker.FixedLocator([-80,-60,60,80])
                ax.coastlines()
                ax.add_feature(cfeature.BORDERS, linestyle=':')
                if row == 0:
                    ax.set_title(str(t.dt.year.values) + '-' + str(t.dt.month.values).zfill(2) + ': ' + exp_names[col])
        plt.tight_layout()
        name = ds.name + '_' + str(t.dt.year.values) + '-' + str(t.dt.month.values).zfill(2) + SUFFIX + '.png'
        gif_files.append(name)
        if DEBUG:
            plt.show(); exit(1)
        plt.savefig(name, dpi = 600)
        print("SAVED:" , name)
    loop_name = ds.name + '_' + pd.to_datetime(ds.time.values[0]).strftime('%Y%m') + SUFFIX + '.gif'
    frames = [iio.imread(img, mode='RGB') for img in gif_files]
    iio.imwrite(loop_name, frames, duration=500, loop=0, dither=0)
    print("SAVED:", loop_name)
