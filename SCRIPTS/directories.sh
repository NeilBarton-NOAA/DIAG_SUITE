#!/bin/sh
set -u
EXP=${1:-HR1}
dtg=${3:-${DTG}}

SCRIPT_DIR=${SCRIPT_DIR:-$PWD}

# Local Directories, works on hera
TOPDIR_OBS=/scratch2/NCEPDEV/stmp3/${USER}/DIAG/OBS
TOPDIR_OUTPUT=/scratch2/NCEPDEV/stmp3/${USER}/DIAG
TOPDIR_FIGURES=/scratch2/NCEPDEV/stmp3/${USER}/FIGURES

# Location of based on experiment
case ${EXP} in 
    'HR1' )     
        SRC_DIR="/NCEPDEV/emc-climate/5year/Jiande.Wang/WCOSS2/HR1"
        ;;
    'HR2' )     
        SRC_DIR="/NCEPDEV/emc-climate/5year/role.ufscpara/{WCOSS2,HERA}/HR2"
        ;;
    'EP4' )     
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4/ep4_f'
        ;;
    'EP4a' )    
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4a'
        ;;
    'EP5')      
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5' 
        local_download_dir=${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}
        hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.${f} 
        FL=35 # Forecast Length is 35 days
        ;;
    'EP5r1')    
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5r1' 
        local_download_dir=${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}
        local_ice_dir=${local_download_dir}/ice 
        hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.${f} 
        FL=35 # Forecast Length is 35 days
        ;;
    'DA_TEST' )      
        SRC_DIR='/scratch1/NCEPDEV/stmp2/Lydia.B.Stefanova/DA'
        ;;

* ) echo 'FATAL: case unknowned ' && exit 1
esac



