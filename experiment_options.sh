#!/bin/sh
set -u
[[ ${DEBUG:-F} == T ]] && declare -rx PS4='+ $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]'"(${1}): "
EXP=${1}
MODEL=${2}
export HPC_ACCOUNT=${3:-$COMPUTE_ACCOUNT}
####################################
# Variables based on experiment name
case ${EXP} in 
    'GFSv17')    
        HPSS_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt*'
        RUN='gfs'
        ;;
    'RT13UPD01')    
        HPSS_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt13_upd01*'
        RUN='gfs'
        ice_hpss_file='ice_6hravg.tar'
        ;;
    'RT15UPD02')    
        HPSS_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt15_upd02*'
        RUN='gfs'
        ice_hpss_file='ice_6hravg.tar'
        ;;
    'RT16UPD02')    
        HPSS_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt16_upd02*'
        RUN='gfs'
        ice_hpss_file='ice_6hravg.tar'
        ;;
    'RT17UPD03')    
        HPSS_DIR='/NCEPDEV/emc-global/2year/emc.glopara/WCOSS2/GFSv17/rt17_upd03*'
        RUN='gfs'
        ice_hpss_file='ice_6hravg.tar'
        ;;
    'RETROV17')    
        HPSS_DIR='/5year/NCEPDEV/emc-global/emc.glopara/WCOSS2/GFSv17/retrov17*'
        RUN='gfs'
        ice_hpss_file='ice_6hravg.tar'
        ocn_hpss_file='ocean_6hravg.tar'
        ;;
     'DUMMY')
        ice_hpss_file=dummy
        ;;
* ) echo 'FATAL: case unknowned ' && exit 1
esac
if [[ ${MODEL} == 'ice' ]]; then
    HPSS_FILE=${ice_hpss_file}
elif [[ ${MODEL} == 'ocn' ]]; then
    HPSS_FILE=${ocn_hpss_file}
    
fi
########################
# options in scripts
export FORCE_CALC=${FORCE_CALC:-False}
export N_TIMES=${N_TIMES:-100}
export DIAG_DIR=${PWD}
export PYTHON_TOOLS=${DIAG_DIR}/SCRIPTS

