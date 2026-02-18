#!/bin/sh
set -u
EXP=${1}
MODEL=${2:-'ice'}
BACKGROUND_JOB=T

source ${PWD}/experiment_options.sh ${EXP} ${MODEL} ${COMPUTE_ACCOUNT}
source ${PWD}/MACHINE/config.sh

files=$(ls ${TOPDIR_OUTPUT}/${EXP}/ice_??????????.nc)
for f in ${files}; do
    f_out="${f/ice/aice_interp}"
    if [[ ! -f ${f_out} ]]; then
        echo $f
        dtg=$( echo "${f::-3}" | cut -d'_' -f2 )
        JOB_NAME=INTERPaice.${EXP}.${dtg}
        WALLTIME="00:15:00"
        source ${DIAG_DIR}/MACHINE/config.sh
        ${SUBMIT} ${DIAG_DIR}/SCRIPTS/INTERP_aice.py -f ${f} \
            -obs ${TOPDIR_OBS}/ice_concentration/amsr2 -o ${f_out}
        [[ ${?} > 0 ]] && echo "FATAL with SUBMIT" && exit 1
    fi
done
