#!/bin/sh
set -u
EXPS='RETROV17'
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
JOB_NAME=MAPS.${EXPS}.CICE
source ${DIAG_DIR}/MACHINE/config.sh
${SUBMIT} ${DIAG_DIR}/SCRIPTS/MAPS_cice.py -e ${exp_dirs} -y ${YAML}

