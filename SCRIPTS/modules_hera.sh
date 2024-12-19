#!/bin/sh
set -u
set +x
module purge
module use -a $HOME/TOOLS/modulefiles
module load conda

#module use -a /contrib/anaconda/modulefiles
module load hpss

module use -a /scratch2/NCEPDEV/nwprod/hpc-stack/libs/hpc-stack/modulefiles/stack
module load hpc/1.1.0
module load hpc-intel/2022.1.2 
module load nco/4.9.1
#module load netcdf/4.7.0
module load wgrib2
module load cdo/2.3.0

set -x
