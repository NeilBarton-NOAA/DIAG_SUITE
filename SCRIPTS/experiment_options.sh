#!/bin/sh
set -u
EXP=${1:-HR1}
dtg=${2:-${DTG}}
HSI=${HSI:-F}
SCRIPT_DIR=${SCRIPT_DIR:-$PWD}

# Local Directories, works on hera
machine=$(uname -n)
if [[ ${machine:0:3} == hfe ]]; then
    WORK_DIR=/scratch2/NCEPDEV
elif [[ ${machine} == hercules* ]]; then
    WORK_DIR=/work/noaa/marine
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi
TOPDIR_OBS=${WORK_DIR}/${USER}/DIAG/OBS
TOPDIR_OUTPUT=${WORK_DIR}/${USER}/DIAG
TOPDIR_FIGURES=${WORK_DIR}/${USER}/FIGURES

# Location of based on experiment
case ${EXP} in 
    'HR1' )     
        SRC_DIR="/NCEPDEV/emc-climate/5year/Jiande.Wang/WCOSS2/HR1"
        ;;
    'HR2' )     
        SRC_DIR="/NCEPDEV/emc-climate/5year/role.ufscpara/*/HR2/*er"
        if [[ ${HSI} == T ]]; then
            hpss_dir=$( hsi -q ls -d ${SRC_DIR}/${dtg}/ 2>&1 | grep year )
            hpss_file=${hpss_dir::-1}/ice.tar
        fi
        local_download_dir=${TOPDIR_OUTPUT}/${EXP}
        local_ice_dir=${local_download_dir}/gfs.${dtg:0:8}/${dtg:8:10}/model_data/ice/history
        FL=16
        FPD=8
        file_search="ice[1,2]*nc"
        ;;
    'HR3a' )
        SRC_DIR="/NCEPDEV/emc-climate/5year/role.ufscpara/WCOSS2/HR3a/*er"
        if [[ ${HSI} == T ]]; then
            hpss_dir=$( hsi -q ls -d ${SRC_DIR}/${dtg}/ 2>&1 | grep year )
            hpss_file=${hpss_dir::-1}/ice_6hravg.tar
        fi
        local_download_dir=${TOPDIR_OUTPUT}/${EXP}
        local_ice_dir=${local_download_dir}/gfs.${dtg:0:8}/${dtg:8:10}/model_data/ice/history
        FL=16
        FPD=4
        file_search="gfs.ice.t??z.*.f???.nc"
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
        local_ice_dir=${local_download_dir}/ice 
        hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.ice.tar
        FL=35 # Forecast Length is 35 days
        file_search="iceh*${member}.nc"
        ;;
    'EP5r1')    
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5r1' 
        local_download_dir=${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}
        local_ice_dir=${local_download_dir}/ice 
        hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.ice.tar 
        FL=35 # Forecast Length is 35 days
        ;;
    'SFS' )      
        SRC_DIR='local'
        local_download_dir=${TOPDIR_OUTPUT}/${EXP}
        local_ice_dir=${local_download_dir}/gefs.${dtg:0:8}/${dtg:8:10}/model_data/ice/history
        FL=$(( 4 * 31 )) # Forecast Length is 4 months
        FPD=4
        file_search="gfs.ice.t??z.*.f???.nc"
        hpss_file=""
        ;;
    'DA_TEST' )      
        SRC_DIR='/scratch1/NCEPDEV/stmp2/Lydia.B.Stefanova/DA'
        ;;

* ) echo 'FATAL: case unknowned ' && exit 1
esac



