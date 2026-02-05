#!/bin/sh
set -u
[[ ${DEBUG:-F} == T ]] && declare -rx PS4='+ $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]'"(${1}): "
EXP=${1}
MODEL=${2}
export HPC_ACCOUNT=${3}
####################################
# Variables based on experiment name
case ${EXP} in 
    'RETROV17')    
        HPSS_DIR='/5year/NCEPDEV/emc-global/emc.glopara/*/GFSv17/retrov17*'
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

