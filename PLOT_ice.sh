#!/bin/sh
set -u
EXPS="${@}"
BACKGROUND_JOB=T
export DEBUG_DIAG=F
source ${PWD}/experiment_options.sh DUMMY ice 
source ${PWD}/MACHINE/config.sh

############
# model files
files=""
for EXP in ${EXPS}; do
    files=${files}$(ls ${TOPDIR_OUTPUT}/${EXP}/ice_extent_${EXP}.nc)" "
done

############
# ice_extent
JOB_NAME=PLOT.${EXPS}.ICE_EXTENT
source ${DIAG_DIR}/MACHINE/config.sh
${SUBMIT} ${DIAG_DIR}/SCRIPTS/PLOT_ice_extent.py -f ${files} -fd ${TOPDIR_FIGURES} \
            -obs ${TOPDIR_OBS}/ice_concentration/amsr2 analysis \
#            -obs analysis \
#            -obs ${TOPDIR_OBS}/ice_concentration/amsr2 ${TOPDIR_OBS}/ice_concentration/climatology persistance analysis \

exit 1
###########
# iiee
JOB_NAME=CALC.${EXP}.IIEE
source ${DIAG_DIR}/MACHINE/config.sh
${SUBMIT} ${DIAG_DIR}/SCRIPTS/PLOT_iiee.py -f ${files} -fd ${TOPDIR_FIGURES} \
            -obs analysis \

