#!/usr/bin/env python3 
########################
#  Neil P. Barton (NOAA-EMC), 2022-10-27
#   compare REPLAY data sets
#   https://docs.xarray.dev/en/stable/user-guide/plotting.html
########################
########################
import argparse
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import glob 
import numpy as np
import pandas as pd
import xarray as xr
path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.getenv("PYTHON_TOOLS")) if 'slurm' in path else sys.path.append(path)
import PYTHON_TOOLS as npb

parser = argparse.ArgumentParser( description = "Calculates Integrated Ice Extent Error Between Runs and Observations")
parser.add_argument('-f', '--files', action = 'store', nargs = '+', help="model files to calc iiee")
parser.add_argument('-v', '--vars', action = 'store', nargs = 1, help="output file to save")
args = parser.parse_args()
files = args.files
variables = args.files

########################
for f in files:
    print(f)
    ds = 
print('CALC_spot_check.py SUCCESSFUL')

