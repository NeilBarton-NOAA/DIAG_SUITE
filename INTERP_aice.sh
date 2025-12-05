#!/bin/sh
set -u
EXP=${1}
MODEL=${2:-'ice'}
BACKGROUND_JOB=F

source ${PWD}/experiment_options.sh ${EXP} ${MODEL}
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
        #SUBMIT=""
        ${SUBMIT} ${DIAG_DIR}/SCRIPTS/INTERP_aice.py -f ${f} \
            -obs ${TOPDIR_OBS}/ice_concentration/amsr2 ${TOPDIR_OBS}/ice_concentration/climatology -o ${f_out}
            #-obs osi_saf climatology analysis \
            #    -od ${TOPDIR_OBS} -o ${f_out}
        (( $? > 0 )) && exit 1
    fi
done
