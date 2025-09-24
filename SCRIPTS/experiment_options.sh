#!/bin/sh
set -u
declare -rx PS4='+ $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]'"(${1}): "
EXP=${1:-EP6}
dtg=${2:-${DTG}}
SCRIPT_DIR=${SCRIPT_DIR:-$PWD}
EXP=${EXP%,}
####################################
# Variables based on experiment name
case ${EXP} in 
    'EP5r1')    
        SRC_DIR='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5r2_f' 
        WORKFLOW="GEFS"
        RUN="gefs"
        OBS="noaa_cdr"
        ;;
    'EP6')    
        SRC_DIR='/NCEPDEV/emc-ensemble/5year/emc.ens/WCOSS2/EP6'
        WORKFLOW="GW"
        RUN="gefs"
        OBS="noaa_cdr"
        ;;
    'GFSRETRO')    
        SRC_DIR='/5year/NCEPDEV/emc-global/emc.glopara/WCOSS2/GFSv17/retrotestgfs1*'
        WORKFLOW="GFS"
        RUN="gfs"
        OBS="osi_saf analysis"
        ;;
    'GFSBASE')    
        SRC_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt13_base*'
        WORKFLOW="GFS"
        RUN="gfs"
        OBS="analysis"
        ;;
    'GFSUPD01')    
        SRC_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt13_upd01*'
        WORKFLOW="GFS"
        RUN="gfs"
        OBS="analysis"
        ;;
     'DUMMY')
        echo "DUMMY EXP for scripts"
        ;;
* ) echo 'FATAL: case unknowned ' && exit 1
esac

####################################
# Local Directoriesi and 'global' variables
machine=$(uname -n)
if [[ ${machine:0:3} == hfe || ${machine} == h*[cm]* ]]; then
    WORK_DIR=/scratch2/NCEPDEV/stmp3
elif [[ ${machine} == hercules* ]]; then
    WORK_DIR=/work/noaa/marine
elif [[ ${machine} == gaea* || ${machine} == dtn* || ${machine} == c6* ]]; then
    WORK_DIR=/gpfs/f6/sfs-emc/scratch
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi
export TOPDIR_OBS=${WORK_DIR}/${USER}/DIAG/OBS
export TOPDIR_OUTPUT=${WORK_DIR}/${USER}/DIAG
export TOPDIR_FIGURES=${WORK_DIR}/${USER}/FIGURES

