#!/usr/bin/env python3 
########################
from pathlib import Path
import numpy as np
import pandas as pd
import argparse
import sys, os
import xarray as xr
p = os.getenv("pytools", os.path.dirname(os.path.realpath(__file__)))
if p not in sys.path: sys.path.insert(0, p)
import pytools as py

def main():
    ################################################
    parser = argparse.ArgumentParser( description = "Comparing GFS Runs")
    parser.add_argument('-e', '--experiments', action = 'store', nargs = '+', 
                        default = ['retrov17_01_realtime'],
                        help = 'experiments names from COMROOT directory')
    parser.add_argument('-c', '--comroot', action = 'store', nargs = 1,
                        default = os.getenv('NPB_WORKDIR') + '/RUNS/COMROOT',
                        help = 'comroot/top directory of experiments')
    parser.add_argument('-y', '--yaml', action = 'store', nargs = 1, \
                        default = os.getenv('PWD') + '/eval.yaml', \
                        help="yaml file with configuration options")
    parser.add_argument('-d','--debug', action = argparse.BooleanOptionalAction, default=False,
                        help = 'show plot for debugging') 
    
    ############
    args = parser.parse_args()
    experiments = args.experiments
    config = py.load_yaml(args.yaml)
    config["comroot"] = args.comroot
    DEBUG = args.debug

    ############
    exp_names, exp_dirs = [], [] 
    for e in experiments:
        name = os.path.basename(os.path.normpath(e))
        exp_names.append(name)
        d = e if '/' in e else config['comroot'] + '/' + e
        exp_dirs.append(d)
    exps = dict(zip(exp_names, exp_dirs))
    ################################################
    # hopeful nothing below here needs to be changed
    ds = []
    for e in exps.keys():
        ds_save = Path(config['comroot'] + "/ZARR/") / Path(e + '.zarr')
        config['zarr_file'] = ds_save
        Path(ds_save).parent.mkdir(parents=True, exist_ok=True)
        for d in Path(exps[e]).iterdir():
            print(d)
            if os.path.exists(ds_save):
                dtg = os.path.basename(d).split(".")[-1]
                dtg = np.datetime64(f"{dtg[:4]}-{dtg[4:6]}-{dtg[6:8]}")
                ds_dtg = xr.open_zarr(ds_save)['time'].astype("datetime64[D]")
                PARSE_FILES = False if np.any(dtg == ds_dtg) else True
            else:
                PARSE_FILES = True
            if PARSE_FILES:
                files = sorted(Path(d).rglob("*.nc"))
                py.parse_output(files, config)
        ds.append(xr.open_zarr(ds_save))
    ds = ds[0] if len(ds) == 1 else xr.concat(ds, dim = 'experiment', join = 'outer')
    print(ds)
    #################################################
    #ds = py.ds_addvar(ds, var)
    #ice_vars = ['ice_extent', 'ice_volume', 'snow_volume', 'Tsfc', 'aice', 'albsni', 'hi', 'hs']
    #model = 'ice' if var in ice_vars else 'ocn'
    #da = ds[var].sel(component = model, experiment = exp_names) 
    #if (model == 'ice') and (var not in ['ice_extent', 'ice_volume', 'snow_volume']):
    #    da_aice = ds['aice'].sel(component='ice', experiment=exp_names)
    #    cell_area = ds['cell_area'].sel(component='ice', experiment=exp_names)
    #    da = da.where(da_aice > 0, drop = False) 
    #    if var == 'albsni': da = da.where(da < 100, drop = False) 
    #else:
    #    cell_area = np.cos(np.deg2rad(ds.latitude))

    ################################################
    # grab obs
    #if var in ['ice_extent', 'SST']:
    #if var in ['ice_extent']:
    #    cm.start_dtg = pd.to_datetime(ds.time.values[0]).replace(day = 1)
    #    cm.end_dtg = pd.to_datetime(ds.time.values[-1]) + pd.offsets.MonthEnd(0)
    #    cm.var = var
    #    obs = cm.grab()
    #else:
    #    obs = False

    ########################
    # spatial plots
    # global
    #if (len(exps) == 2) and (model == 'ocn'):
    #    py.maps.three_panel(da, DEBUG)
    # polar 
    #if (len(exps) == 2) and (model == 'ice') and (var not in ['ice_extent', 'ice_volume', 'snow_volume']):
    #    py.maps.six_panel(da, DEBUG)
    ########################
    # line plots
    #if model == 'ocn':
    #    py.plots.line(da, 'global', obs, cell_area, DEBUG)
    #    py.plots.line(da, 'nino34', obs, cell_area, DEBUG)
    #    py.plots.line(da, 'tropics', obs, cell_area, DEBUG)
    #    py.plots.line(da, 'equator', obs, cell_area, DEBUG)
    #if 'hemisphere' in da.dims:
    #    ob = obs.sel(hemisphere = 'NH') if var in ['ice_extent'] else False
    #    py.plots.line(da.sel(hemisphere = 'NH'), 'Arctic', ob, cell_area)
    #    ob = obs.sel(hemisphere = 'SH') if var in ['ice_extent'] else False
    #    py.plots.line(da.sel(hemisphere = 'SH'), 'Antarctic', ob, cell_area)
    #elif var != 'WWV':
    #    py.plots.line(da, 'Arctic', obs, cell_area)
    #    py.plots.line(da, 'Antarctic', obs, cell_area)
#
    print('SCRIPT FINISHED')

if __name__ == "__main__":
    main()
