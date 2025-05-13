#!/bin/sh
set -u
case ${WORKFLOW} in 
    'GEFS')    
    hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.ice.tar
    local_download_dir=${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}
    local_ice_dir=${local_download_dir}/ice
    ;;
    'GW')
    hpss_file=${SRC_DIR}/${dtg}/${RUN}_ice.tar
    local_download_dir=${TOPDIR_OUTPUT}/${EXP}
    local_ice_dir=${local_download_dir}/${RUN}.${dtg:0:8}/${dtg:8:10}/mem*/model/ice/history   
    ;;
    'GFS')
    hpss_file=${SRC_DIR}/${dtg}/ice_6hravg.tar
    local_download_dir=${TOPDIR_OUTPUT}/${EXP}
    local_ice_dir=${local_download_dir}/${RUN}.${dtg:0:8}/${dtg:8:10}/model/ice/history   
    ;;
    *)
    echo "FATAL: unknown workflow directory structure"
    exit 1
    ;;
esac
