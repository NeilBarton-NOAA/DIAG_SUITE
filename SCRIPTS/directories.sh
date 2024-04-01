#!/bin/sh
set -u
EXP=${1:-HR1}

SCRIPT_DIR=${SCRIPT_DIR:-$PWD}

# Location of DATA, if on hera, scripts will not download data
case ${EXP} in 
    'HR1' )     SRC_DIR="/NCEPDEV/emc-climate/5year/Jiande.Wang/WCOSS2/HR1";;
    'HR2' )     SRC_DIR="/NCEPDEV/emc-climate/5year/role.ufscpara/{WCOSS2,HERA}/HR2";;
    'EP4' )     SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4/ep4_f';;
    'EP4a' )    SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4a';;
    'EP5')      SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5' ;;
    'EP5r1')    SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5r1' ;;
    'DA_TEST' )      SRC_DIR='/scratch1/NCEPDEV/stmp2/Lydia.B.Stefanova/DA';;

* ) echo 'FATAL: case unknowned ' && exit 1
esac

# Local Directoriesy
TOPDIR_OBS=/scratch2/NCEPDEV/stmp3/${USER}/DIAG/OBS
TOPDIR_OUTPUT=/scratch2/NCEPDEV/stmp3/${USER}/DIAG
TOPDIR_FIGURES=/scratch2/NCEPDEV/stmp3/${USER}/FIGURES


