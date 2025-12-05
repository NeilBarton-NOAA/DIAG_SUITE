#!/bin/sh
set -u
EXP=${1}
FORCE_CALC=T
BACKGROUND_JOB=F

export DIAG_DIR=${PWD}
source ${DIAG_DIR}/experiment_options.sh ${EXP} ice 
source ${DIAG_DIR}/MACHINE/config.sh

############
# model files
files=$(ls ${TOPDIR_OUTPUT}/${EXP}/aice_interp_??????????.nc)
#files=$(ls ${TOPDIR_OUTPUT}/${EXP}/aice_interp_2025010[1,2]*.nc)

############
# ice_extent
JOB_NAME=CALC.${EXP}.ICE_EXTENT
source ${DIAG_DIR}/MACHINE/config.sh
f_out=${TOPDIR_OUTPUT}/${EXP}/ice_extent_${EXP}.nc 
${SUBMIT} ${DIAG_DIR}/SCRIPTS/CALC_ice_extent.py -f ${files} -o ${f_out}

###########
# iiee
JOB_NAME=CALC.${EXP}.IIEE
source ${DIAG_DIR}/MACHINE/config.sh
f_out=${TOPDIR_OUTPUT}/${EXP}/iiee_${EXP}.nc 
${SUBMIT} ${DIAG_DIR}/SCRIPTS/CALC_iiee.py -f ${files} -o ${f_out} \
            -obs ${TOPDIR_OBS}/ice_concentration/amsr2 ${TOPDIR_OBS}/ice_concentration/climatology

