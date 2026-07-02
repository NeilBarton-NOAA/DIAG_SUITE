#!/bin/bash
NPB_DIR=/NCEPDEV/emc-marine/5year/Neil.Barton/URSA/beta1.1_GFS_ICs
YZ_DIR=/NCEPDEV/emc-global/5year/Yangxing.Zheng/URSA/scratch/SFS_C192mx025_GFSV17ICs
JW_DIR=/NCEPDEV/emc-climate/5year/Jiande.Wang/URSA/beta1.1_GFS_ICs/SFS_C192mx025_GFSV17ICs
# Add Jiande's DIR when ready
hsi "ln -s ${YZ_DIR}/2* ${NPB_DIR}"
hsi "ln -s ${JW_DIR}/2* ${NPB_DIR}"
hsi ls -l ${NPB_DIR}

