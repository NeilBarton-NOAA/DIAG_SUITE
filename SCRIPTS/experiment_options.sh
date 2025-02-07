#!/bin/sh
set -u
EXP=${1:-EP6}
dtg=${2:-${DTG}}
SCRIPT_DIR=${SCRIPT_DIR:-$PWD}

# Local Directories, works on hera
machine=$(uname -n)
if [[ ${machine:0:3} == hfe || ${machine} == h*[cm]* ]]; then
    WORK_DIR=/scratch2/NCEPDEV/stmp3
elif [[ ${machine} == hercules* ]]; then
    WORK_DIR=/work/noaa/marine
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi
export TOPDIR_OBS=${WORK_DIR}/${USER}/DIAG/OBS
export TOPDIR_OUTPUT=${WORK_DIR}/${USER}/DIAG
export TOPDIR_FIGURES=${WORK_DIR}/${USER}/FIGURES

# Location of based on experiment
case ${EXP} in 
    'EP5r1')    
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5r1' 
        WORKFLOW="GEFS"
        #local_download_dir=${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}
        #local_ice_dir=${local_download_dir}/ice 
        #hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.ice.tar 
        #FL=35 # Forecast Length is 35 days
        #CICE_SUFFIX="d"
        ;;
    'EP6')    
        SRC_DIR='/NCEPDEV/emc-ensemble/5year/emc.ens/WCOSS2/EP6'
        WORKFLOW="GW"
        RUN="gefs"
        #hpss_file=${SRC_DIR}/${dtg}/gefs_ice.tar
        #local_download_dir=${TOPDIR_OUTPUT}/${EXP}
        #local_ice_dir=${local_download_dir}/gefs.${dtg:0:8}/${dtg:8:10}/mem*/model/ice/history
        #file_search="gefs.ice.t??z.*.f*.nc"
        #FL=48 # Forecast Length is 48 days
        #CICE_SUFFIX="h"
        ;;
     'DUMMY')
        echo "DUMMY EXP for scripts"
        ;;
* ) echo 'FATAL: case unknowned ' && exit 1
esac



