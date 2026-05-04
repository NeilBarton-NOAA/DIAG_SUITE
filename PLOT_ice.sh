#!/bin/sh
set -u
EXPS='RETROV17'
WALLTIME="04:00:00"
BACKGROUND_JOB=T
export DIAG_DIR=${PWD}
source ${PWD}/MACHINE/config.sh
YAML=${DIAG_DIR}/YAMLS/eval.yaml
exp_dirs=""
for e in ${EXPS}; do
    exp_dirs="${exp_dirs}${TOPDIR_OUTPUT}/${e} "
done
echo $exp_dirs
############
# ice_extent
JOB_NAME=PLOT.${EXPS}.ICE_EXTENT
source ${DIAG_DIR}/MACHINE/config.sh
${SUBMIT} ${DIAG_DIR}/SCRIPTS/PLOT_ice_extent.py -e ${exp_dirs} -y ${YAML}

exit 1
###########
# iiee
JOB_NAME=CALC.${EXP}.IIEE
source ${DIAG_DIR}/MACHINE/config.sh
${SUBMIT} ${DIAG_DIR}/SCRIPTS/PLOT_iiee.py -f ${files} -fd ${TOPDIR_FIGURES} \
            -obs analysis \

