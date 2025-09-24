#!/usr/bin/env python3 
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../' )
import PYTHON_TOOLS as npb

dtg = sys.argv[1]
output_dir = sys.argv[2] + '/sst/ostia'
os.makedirs(output_dir, exist_ok = True)

f_save = output_dir + '/OSTIA_SST_' + dtg + '.nc'
npb.ocnobs.cm.dtg = dtg
npb.ocnobs.cm.var = 'sst'
dat = npb.ocnobs.cm.grab()
dat.file_name = f_save
# interp on MOM6/CICE6 grid
dat = npb.calc.interp(dat, dat_des)


