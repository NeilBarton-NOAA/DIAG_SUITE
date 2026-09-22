#!/usr/bin/env python3 
########################
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import argparse
import sys, os, shutil
p = os.getenv("pytools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pytools as py
from pytools.obs import cm
import tracemalloc

def main():
    tracemalloc.start()
    ################################################
    parser = argparse.ArgumentParser( description = "Comparing SFS Runs")
    parser.add_argument('-e', '--experiments', action = 'store', nargs = '+', 
                        default = 'yaml',
                        help = 'experiments names from COMROOT directory')
    parser.add_argument('-v', '--var', action = 'store', nargs = 1,
                        default = ['SST'],
                        help = 'variable to analyze')
    parser.add_argument('-a', '--analysis_period', action = 'store', nargs = 1,
                        default = 'yaml',
                        help = 'forecast start period to analyze default is to graph first time step')
    parser.add_argument('-c', '--comroot', action = 'store', nargs = 1,
                        default = os.getenv('NPB_WORKDIR') + '/RUNS/COMROOT',
                        help = 'comroot/top directory of experiments')
    parser.add_argument('-y', '--yaml', action = 'store', nargs = 1, \
                        default = os.getenv('PWD') + '/eval.yaml', \
                        help="yaml file with configuration options")
    parser.add_argument('-f','--force_read', action = argparse.BooleanOptionalAction, default=False,
                        help = 're-read in files to create zarr') 
    parser.add_argument('-lv','--list_vars', action = argparse.BooleanOptionalAction, default=False,
                        help = 'list variables that are already set up') 
    parser.add_argument('-d','--debug', action = argparse.BooleanOptionalAction, default=False,
                        help = 'show plot for debugging') 
    ############
    args = parser.parse_args()
    config = py.load_yaml(args.yaml)
    var = args.var[0]
    var = config["analysis"]["variable"] if args.var == 'yaml' else args.var[0]
    experiments = config["analysis"]["experiments"] if args.experiments == 'yaml' else args.experiments
    analysis_period = config["analysis"]["period"] if args.analysis_period == 'yaml' else args.analysis_period[0]
    config["n_members"] = config['analysis']['n_members']
    comroot = args.comroot
    config["comroot"] = comroot
    FORCE_READ_DATA = args.force_read
    list_vars = args.list_vars
    DEBUG = args.debug

    ############
    if list_vars:
        for k in py.maps.limits:
            print(k)
        print('ice_extent')
        print('ice_volume')
        print('snow_volume')
        exit(1)

    ############
    if experiments == 'ALL':
        print('GRABBING ALL EXPERIMENTS AT:', comroot)
        experiments = [comroot + '/' + d for d in os.listdir(comroot) if os.path.isdir(comroot + '/' + d) and d != 'ZARR']
    exp_names, exp_dirs = [], []
    for e in experiments:
        name = os.path.basename(os.path.normpath(e))
        if name == 'SFS_NRT_C192mx025':
            name = 'CPC_ICs'
        exp_names.append(name)
        d = e if '/' in e else comroot + '/' + e
        exp_dirs.append(d)
    exps = dict(zip(exp_names, exp_dirs))
    
    ################################################
    # parse and/or grab data
    ds = []
    for e in exps.keys():
        ds_save = Path(config['comroot'] + "/ZARR/") / Path(e + '_monthly.zarr')
        config['zarr_file'] = ds_save
        Path(ds_save).parent.mkdir(parents=True, exist_ok=True)
        if FORCE_READ_DATA:
            if os.path.exists(ds_save):
                shutil.rmtree(ds_save)
        
        # if ds exist, grab dtgs
        ds_dtgs = np.array([])
        if os.path.exists(ds_save):
            with xr.open_zarr(ds_save) as zds:
                if 'time' in zds:
                    ds_dtgs = zds['time'].astype("datetime64[D]").values
        print(e)
        print(' ', ds_save)
        
        exp_dir = exps[e]
        matching_dirs = sorted([
            Path(exp_dir) / entry.name 
            for entry in os.scandir(exp_dir) 
            if entry.is_dir() and entry.name.endswith("01")
        ])

        for d in matching_dirs:
            dtg = os.path.basename(d).split(".")[-1]
            dtg = np.datetime64(f"{dtg[:4]}-{dtg[4:6]}-{dtg[6:8]}")
            PARSE_FILES = dtg not in ds_dtgs
            if PARSE_FILES:
                print('  adding ',d)
                py.sfs_to_zarr(e, str(d), config)
        ds.append(xr.open_zarr(ds_save, chunks = {'time':1}))
    #ds = ds[0] if len(ds) == 1 else xr.concat(ds, dim='experiment', join='inner') #.chunk('auto')
    aligned_ds = xr.align(*ds, join='inner', exclude=['experiment'])
    ds = aligned_ds[0] if len(aligned_ds) == 1 else xr.concat(aligned_ds, dim='experiment')
    
    ################################################
    # data array for plotting/analysis
    ds = py.ds_addvar(ds, var)
    ice_vars = ['ice_extent', 'ice_volume', 'snow_volume', 'Tsfc', 'aice', 'albsni', 'hi', 'hs']
    model = 'ice' if var in ice_vars else 'ocn'
    da = ds[var].sel(component = model, experiment = exp_names)
    da.attrs['model'] = model
    da.attrs['y_label'] = ds['forecast_month'].values
    da, cell_area = py.get_area(ds.sel(experiment = exp_names), da)
    da, forecast_times = py.sel_analysis_period(da, ds.forecast_time, analysis_period) # select time for analysis
    
    ################################################
    # grab obs
    #if var in ['ice_extent']: # 'SST'
    #    cm.start_dtg = pd.to_datetime(forecast_times.values.min()).replace(day = 1)
    #    cm.end_dtg = pd.to_datetime(forecast_times.values.max()) + pd.offsets.MonthEnd(0)
    #    cm.var = var
    #    obs = cm.grab()
    #else:
    #    obs = False
    obs = False 
    ########################
    # spatial plots
    # global
    if config['plot']['maps']:
        if (len(exps) == 2) and (model == 'ocn'):
            py.maps.three_panel(da, DEBUG)
        # polar 
        if (len(exps) == 2) and (model == 'ice') and (var not in ['ice_extent', 'ice_volume', 'snow_volume']):
            py.maps.six_panel(da, DEBUG)
    
    ########################
    # line plots
    if config['plot']['line'] or config['plot']['line']:
        py.plots.line.da = da
        py.plots.line.obs = obs
        py.plots.line.debug_plot = False
        py.plots.line.cell_area = cell_area
        region_hem = { "NH": "Arctic", "SH": "Antarctic" }
        spread_options = [config['plot']['line'] == False, config['plot']['spread']]
        for spread in spread_options:
            py.plots.line.plot_spread = spread
            for region in config['plot']['regions']:
                py.plots.line.region = region
                if model == 'ocn':
                    if not (var == 'WWV' and region in ['Arctic', 'Antarctic']):
                        py.plots.line.create()
            if 'hemisphere' in da.dims:
                for hem in ['NH', 'SH']:
                    py.plots.line.region = region_hem[hem]
                    py.plots.line.create()
                     
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    print("[ Top 10 Memory Allocations ]")
    for stat in top_stats[:10]:
        print(stat)
    print('SCRIPT FINISHED')

if __name__ == "__main__":
    main()
