#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse, calendar, os, sys
import glob as glob
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import holoviews as hv
from holoviews.plotting.util import process_cmap
from holoviews.operation.datashader import rasterize
from holoviews import opts
p = os.getenv("pydiag_tools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pydiag_tools as diag_tools
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def select_extent(ds):
    return ds[['extent']]

def hv_plot(ds_orig, obs_names, fig_name):
    print(ds_orig)
    f = Path(fig_name)
    if not f.is_file():
        ds = ds_orig.copy()
        if 'time' in ds.coords:
            ds['time'] = ds['time'].dt.strftime('%Y-%m-%d').values
        label = 'test'
        #label = str(ds.time.dt.year.values[0]) + '-' + str(ds.time.dt.month.values[0]).zfill(2)
        names = ds.name.values
        palette = process_cmap('Category10', ncolors=(len(names)))
        color_map = [('black' if name in list(obs_names) else palette[i]) for i, name in enumerate(ds.name.values)]
        hv.extension('bokeh')
        hv_ds = hv.Dataset(ds,
            kdims=['name', 'pole', 'time', 'forecast_day'], 
            vdims=['extent']
        )
        explorer = hv_ds.to(
            hv.Curve,
            kdims=['forecast_day'],
            vdims=['extent'],
            dynamic=False,
            groupby=['name','pole', 'time']).overlay('name')
        #explorer = rasterize(explorer)
        # 4. Apply styling and tooltips
        explorer.opts(
            opts.Curve(
                width=700, height=400,
                show_grid=True,
                tools=['hover'],
                color=hv.Cycle(values=color_map),
                line_width=2),
            opts.Overlay(
                title="Ice Extent Comparison " + label,
                legend_position='right',
                legend_labels="",
                click_policy='hide')
        )
        print("Saving hvplot", fig_name)
        hv.save(explorer, fig_name, fmt='html', resources='cdn')
        print('SAVED:', fig_name)
    else:
        print('Already Created:', fig_name)

def main():
    parser = argparse.ArgumentParser( description = "Plot Ice Extent between Runs and Observations")
    parser.add_argument('-e', '--experiments_dir', action = 'store', nargs = '+', \
        help="directories of the experiments")
    parser.add_argument('-y', '--yaml', action = 'store', nargs = 1, \
        help="yaml file")
    args = parser.parse_args()
    exp_dirs = args.experiments_dir
    config = diag_tools.utils.load_yaml(args.yaml[0])
    save_dir = config['save_dir']
    poles = ['NH', 'SH']

    ####################################
    # grab ice extent from models
    DATS, exps = [], []
    for e in exp_dirs:
        files = glob.glob(e + '/ice_2025*nc')
        ds = xr.open_mfdataset(files, preprocess=select_extent)
        exp = Path(e).name
        exps.append(exp)
        DATS.append(ds.expand_dims({"name" : [exp]}))

    MODEL = xr.concat(DATS, dim = 'name')
    if config['plot']['analysis'] and MODEL['time'].size < MODEL['forecast_hour'].size:
        print("config['plot']['analysis'] will be set to False")
        config['plot']['analysis'] = False

    ####################################
    # grab ice extent observations
    DATS = []
    if config['plot']['analysis']:
        print('using analsyis')
        D = MODEL.isel(forecast_hour = 0)
        D = D.drop_vars('forecast_hour')
        D = D.squeeze()
        D = D.expand_dims({'name': ['analysis']})
        DATS.append(D)
        
    diag_tools.iceobs.dtgs = diag_tools.utils.all_dtgs(ds) 
    for ob in config['observations']['sic']:
        print('obs:', ob)
        diag_tools.iceobs.directory = ob
        D = diag_tools.iceobs.extent.grab()
        D = D.expand_dims({'name': [Path(ob).stem]})
        DATS.append(D)
     
    OBS = xr.concat(DATS, dim = 'name', join = 'outer').fillna(0)

    ####################################
    ## if analysis, need to reduce time
    if config['plot']['analysis']:
        end_date = MODEL['time'][-1].values + pd.Timedelta(hours = int(MODEL['forecast_hour'][-1].values))
        MODEL = MODEL.sel(time=slice(None, end_date))

    ####################################
    # Give OBS forecast hours dimension
    OBS = diag_tools.utils.add_forecast_hour(OBS, MODEL['forecast_hour'][-1].values)
    OBS = OBS.dropna(dim='time', how='any', subset=list(OBS))
    new_names = ['analysis ' + n if n in exps else n for n in OBS['name'].values]
    OBS['name'] = new_names

    ####################################
    # grab only model output for same grid as obs
    #common_times = np.intersect1d(MODEL.time.values, OBS.time.values)
    ds = xr.concat([MODEL, OBS], dim = 'name', data_vars = 'all', join='inner')
    
    ####################################
    # edit color map and ds for hv plots
    ds['forecast_day'] = ds['forecast_hour'] / 24.0
    ds = ds.swap_dims({'forecast_hour': 'forecast_day'})
    ds = ds.drop_vars('forecast_hour')
      
    ds_monthly = ds.resample(time='MS').mean()
    hv_plot(ds_monthly, OBS.name.values, 'test.html')
    print(ds_monthly['time'].values)
    exit(1)
    for label, ds_group in ds.groupby(ds.time.dt.strftime("%Y-%m")):
        print(label)
        print(ds_group)
        exit(1)
        ds_sel = ds_group.isel(time=(slice(0,None,config['plot']['time_slice_int'])))
        fig_name = save_dir + '/' + label + '_ICE_EXTENT.html'
        hv_plot(ds_sel, OBS.name.values, fig_name)
    
if __name__ == "__main__":
    main()

