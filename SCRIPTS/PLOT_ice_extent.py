#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
import argparse, calendar, os, sys
import glob as glob
import numpy as np
from pathlib import Path
import pandas as pd
import xarray as xr
import holoviews as hv
from holoviews.plotting.util import process_cmap
from holoviews import opts
p = os.getenv("pydiag_tools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pydiag_tools as diag_tools

def select_extent(ds):
    return ds[['extent']]

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
        files = glob.glob(e + '/ice*nc')
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
    diag_tools.iceobs.dtgs = diag_tools.utils.all_dtgs(ds) 
    DATS = []
    if config['plot']['analysis']:
        print('using analsyis')
        D = MODEL.isel(forecast_hour = 0)
        D = D.drop_vars('forecast_hour')
        D = D.squeeze()
        D = D.expand_dims({'name': ['analysis']})
        DATS.append(D)
        
    for ob in config['observations']['sic']:
        print('obs:', ob)
        diag_tools.iceobs.directory = ob
        D = diag_tools.iceobs.extent.grab()
        D = D.expand_dims({'name': [Path(ob).stem]})
        DATS.append(D)
    
    OBS = xr.concat(DATS, dim = 'name')

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
    common_times = np.intersect1d(MODEL.time.values, OBS.time.values)
    OBS = OBS.sel(time = common_times)
    MODEL = MODEL.sel(time = common_times)
    ds = xr.concat([MODEL, OBS], dim = 'name', data_vars = 'all', join='inner')
    
    ####################################
    # edit color map and ds for hv plots
    ds['forecast_day'] = ds['forecast_hour'] / 24.0
    ds = ds.swap_dims({'forecast_hour': 'forecast_day'})
    ds = ds.drop_vars('forecast_hour')
    #ds = ds.compute()
    
    names = ds.name.values
    palette = process_cmap('Category10', ncolors=(len(names)))
    color_map = [('black' if name in list(OBS.name.values) else palette[i]) for i, name in enumerate(ds.name.values)]
    
    hv.extension('bokeh')
    hv_ds = hv.Dataset(ds,
        kdims=['name', 'pole', 'time', 'forecast_day'], 
        vdims=['extent']
    )
    explorer = hv_ds.to(
        hv.Curve,
        kdims=['forecast_day'],
        vdims=['extent'],
        groupby=['name','pole', 'time']).overlay('name')

    # 4. Apply styling and tooltips
    explorer.opts(
        opts.Curve(
            width=700, height=400,
            show_grid=True,
            tools=['hover'],
            color=hv.Cycle(values=color_map),
            line_width=2
        ),
        opts.Overlay(
        title="Ice Extent Comparison",
        legend_position='right',
        legend_labels="",
        click_policy='hide' # Clicking a name in the legend hides its line
        )
    )
    hv.save(explorer, save_dir + '/ice_extent_explorer.html', fmt='html', resources='inline')
    print('SAVED hv plot')
    
if __name__ == "__main__":
    main()

